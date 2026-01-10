"""
نظام استخراج الإحداثيات الدقيقة للمواقع المكتشفة
"""
import numpy as np
from shapely.geometry import Point, Polygon, MultiPoint
from sklearn.cluster import DBSCAN
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING
import warnings
warnings.filterwarnings('ignore')

# Type checking imports (not evaluated at runtime)
if TYPE_CHECKING:
    import rasterio.transform

# Lazy imports for heavy dependencies
try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

try:
    from scipy import ndimage
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import rasterio
    from rasterio.features import shapes
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


class CoordinateExtractor:
    """
    استخراج الإحداثيات الدقيقة من خرائط الشذوذ
    
    Requires: geopandas, scipy, rasterio
    """
    
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger
        
        # Check dependencies
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if all required dependencies are available"""
        missing = []
        
        if not HAS_GEOPANDAS:
            missing.append('geopandas')
        if not HAS_SCIPY:
            missing.append('scipy')
        if not HAS_RASTERIO:
            missing.append('rasterio')
        
        if missing:
            from src.utils.dependency_errors import DependencyMissingError
            raise DependencyMissingError(
                missing_libs=missing,
                operation='coordinate extraction',
                install_hint='pip install -r requirements_core.txt -r requirements_geo.txt',
                is_critical=True
            )
    
    def extract_coordinates_from_anomaly_map(
        self,
        anomaly_map: np.ndarray,
        aoi_geometry: Optional[Polygon] = None
    ) -> gpd.GeoDataFrame:
        """
        Simplified wrapper for pipeline use - extracts coordinates without transform.
        
        Args:
            anomaly_map: Binary anomaly map (0-1)
            anomaly_surface: Anomaly confidence surface (optional)
            aoi_geometry: Area of interest geometry (optional)
        
        Returns:
            GeoDataFrame with detected site coordinates
        """
        from rasterio.transform import from_bounds
        
        # Create a simple transform from AOI or use default
        if aoi_geometry:
            bounds = aoi_geometry.bounds  # (minx, miny, maxx, maxy)
            height, width = anomaly_map.shape
            transform = from_bounds(
                bounds[0], bounds[1], bounds[2], bounds[3],
                width, height
            )
        else:
            # Default transform for demo data
            height, width = anomaly_map.shape
            transform = from_bounds(0, 0, width, height, width, height)
        
        # Use the existing method with generated transform
        crs = 'EPSG:4326'
        return self.detect_anomaly_clusters(
            anomaly_map=anomaly_map,
            transform=transform,
            crs=crs
        )
    
    def detect_anomaly_clusters(
        self, 
        anomaly_map: np.ndarray,
        transform,  # rasterio.transform.Affine
        crs: str
    ):
        """
        كشف وتجميع العناقيد الشاذة واستخراج إحداثياتها
        
        Args:
            anomaly_map: مصفوفة الشذوذ (0-1)
            transform: تحويل الإحداثيات
            crs: نظام الإحداثيات
            
        Returns:
            GeoDataFrame يحتوي على الإحداثيات والخصائص
        """
        self.logger.info("بدء استخراج إحداثيات العناقيد الشاذة...")
        
        # تطبيق عتبة الثقة
        threshold = self.config['processing']['coordinate_extraction']['confidence_threshold']
        binary_map = anomaly_map >= threshold
        
        if np.sum(binary_map) == 0:
            self.logger.warning("لم يتم اكتشاف أي مناطق تتجاوز عتبة الثقة")
            return gpd.GeoDataFrame()
        
        # وسم المناطق المتصلة
        labeled_array, num_features = ndimage.label(binary_map)
        
        self.logger.info(f"تم اكتشاف {num_features} منطقة متصلة")
        
        # استخراج خصائص كل منطقة
        features = []
        for label in range(1, num_features + 1):
            # إحداثيات البكسلات للمنطقة
            y_coords, x_coords = np.nonzero(labeled_array == label)
            
            # فلترة المناطق الصغيرة
            min_area = self.config['processing']['coordinate_extraction']['min_anomaly_area']
            if len(y_coords) < min_area:
                continue
            
            # حساب مركز الثقل
            center_y = np.mean(y_coords)
            center_x = np.mean(x_coords)
            
            # تحويل إلى إحداثيات جغرافية
            lon, lat = rasterio.transform.xy(transform, center_y, center_x)
            
            # حساب مساحة المنطقة (متر مربع)
            pixel_area = abs(transform.a * transform.e)  # مساحة البكسل
            area_m2 = len(y_coords) * pixel_area
            
            # حساب شدة الشذوذ
            anomaly_values = anomaly_map[y_coords, x_coords]
            anomaly_intensity = np.mean(anomaly_values)
            anomaly_std = np.std(anomaly_values)
            
            # حساب محيط المنطقة
            mask = labeled_array == label
            perimeter_pixels = self._calculate_perimeter(mask)
            perimeter_m = perimeter_pixels * np.sqrt(abs(pixel_area))
            
            # خصائص إضافية
            bbox = self._calculate_bounding_box(y_coords, x_coords, transform)
            compactness = (4 * np.pi * area_m2) / (perimeter_m ** 2) if perimeter_m > 0 else 0
            
            feature = {
                'cluster_id': label,
                'geometry': Point(lon, lat),
                'centroid_lon': lon,
                'centroid_lat': lat,
                'area_m2': area_m2,
                'perimeter_m': perimeter_m,
                'anomaly_intensity': anomaly_intensity,
                'anomaly_std': anomaly_std,
                'confidence': anomaly_intensity,
                'compactness': compactness,
                'pixel_count': len(y_coords),
                'bbox': bbox
            }
            features.append(feature)
        
        # إنشاء GeoDataFrame
        if features:
            gdf = gpd.GeoDataFrame(features, crs=crs)
            
            # تطبيق تجميع DBSCAN للتخلص من الزوائد
            gdf = self._apply_clustering(gdf)
            
            # تطبيع أسماء الأعمدة للتوافق مع schema_normalizer
            gdf = gdf.rename(columns={
                'cluster_id': 'id',
                'centroid_lon': 'lon',
                'centroid_lat': 'lat'
            })
            
            # إضافة عمود priority بناءً على الثقة
            if 'confidence' in gdf.columns:
                gdf['priority'] = gdf['confidence'].apply(
                    lambda x: 'high' if x >= 0.7 else ('medium' if x >= 0.4 else 'low')
                )
            else:
                gdf['priority'] = 'medium'
            
            self.logger.info(f"تم استخراج {len(gdf)} إحداثية دقيقة")
            return gdf
        else:
            return gpd.GeoDataFrame()
    
    def _calculate_perimeter(self, mask: np.ndarray) -> int:
        """
        حساب محيط المنطقة بالبكسلات
        """
        from scipy.ndimage import binary_erosion
        eroded = binary_erosion(mask)
        perimeter_mask = mask & ~eroded
        return np.sum(perimeter_mask)
    
    def _calculate_bounding_box(
        self, 
        y_coords: np.ndarray, 
        x_coords: np.ndarray,
        transform: 'rasterio.transform.Affine'
    ) -> Polygon:
        """
        حساب المربع المحيط للمنطقة
        """
        min_y, max_y = np.min(y_coords), np.max(y_coords)
        min_x, max_x = np.min(x_coords), np.max(x_coords)
        
        # الزوايا الأربع
        corners = [
            (min_x, min_y),
            (max_x, min_y),
            (max_x, max_y),
            (min_x, max_y),
        ]
        
        # تحويل إلى إحداثيات جغرافية
        geocorners = []
        for x, y in corners:
            lon, lat = rasterio.transform.xy(transform, y, x)
            geocorners.append((lon, lat))
        
        geocorners.append(geocorners[0])
        
        return Polygon(geocorners)
    
    def _apply_clustering(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        تطبيق تجميع DBSCAN لدمج النقاط المتقاربة
        """
        if len(gdf) < 2:
            return gdf
        
        # استخراج الإحداثيات
        coords = np.array([[geom.x, geom.y] for geom in gdf.geometry])
        
        # تطبيق DBSCAN
        eps = self.config['processing']['coordinate_extraction']['cluster_distance'] / 111000
        dbscan = DBSCAN(eps=eps, min_samples=1)
        labels = dbscan.fit_predict(coords)
        
        # دمج العناقيد
        merged_features = []
        unique_labels = np.unique(labels)
        
        for label in unique_labels:
            cluster_points = gdf[labels == label]
            
            if len(cluster_points) == 1:
                merged_features.append(cluster_points.iloc[0].to_dict())
            else:
                centroid_lon = cluster_points['centroid_lon'].mean()
                centroid_lat = cluster_points['centroid_lat'].mean()
                
                merged_feature = {
                    'cluster_id': f"merged_{label}",
                    'geometry': Point(centroid_lon, centroid_lat),
                    'centroid_lon': centroid_lon,
                    'centroid_lat': centroid_lat,
                    'area_m2': cluster_points['area_m2'].sum(),
                    'perimeter_m': cluster_points['perimeter_m'].max(),
                    'anomaly_intensity': cluster_points['anomaly_intensity'].max(),
                    'anomaly_std': cluster_points['anomaly_std'].mean(),
                    'confidence': cluster_points['confidence'].max(),
                    'compactness': cluster_points['compactness'].mean(),
                    'pixel_count': cluster_points['pixel_count'].sum(),
                    'bbox': cluster_points.iloc[0]['bbox'],
                    'merged_points': len(cluster_points)
                }
                merged_features.append(merged_feature)
        
        merged_gdf = gpd.GeoDataFrame(merged_features, crs=gdf.crs)
        self.logger.info(f"تم دمج {len(gdf)} نقطة إلى {len(merged_gdf)} عنقود")
        
        return merged_gdf
    
    def extract_precise_coordinates(
        self,
        anomaly_map: np.ndarray,
        transform: 'rasterio.transform.Affine',
        crs: str,
        aoi_polygon: Optional[Polygon] = None
    ) -> Dict:
        """
        استخراج إحداثيات دقيقة مع تحليل مفصل
        """
        self.logger.info("بدء استخراج الإحداثيات الدقيقة...")
        
        clusters_gdf = self.detect_anomaly_clusters(anomaly_map, transform, crs)
        
        if clusters_gdf.empty:
            return {
                'status': 'no_detections',
                'message': 'لم يتم اكتشاف أي مناطق شاذة',
                'clusters': gpd.GeoDataFrame(),
                'statistics': {}
            }
        
        if aoi_polygon:
            original_count = len(clusters_gdf)
            clusters_gdf = clusters_gdf[clusters_gdf.geometry.within(aoi_polygon)]
            filtered_count = len(clusters_gdf)
            self.logger.info(f"تمت فلترة {original_count - filtered_count} نقطة خارج AOI")
        
        statistics = self._calculate_statistics(clusters_gdf)
        classified_gdf = self._classify_points(clusters_gdf)
        report = self._generate_detailed_report(classified_gdf, statistics)
        
        return {
            'status': 'success',
            'clusters': classified_gdf,
            'statistics': statistics,
            'report': report,
            'total_detections': len(classified_gdf),
            'high_confidence_detections': len(classified_gdf[classified_gdf['confidence'] >= 0.8])
        }
    
    def _calculate_statistics(self, gdf: gpd.GeoDataFrame) -> Dict:
        """
        حساب إحصاءات مفصلة
        """
        if gdf.empty:
            return {}
        
        return {
            'total_clusters': len(gdf),
            'total_area_m2': gdf['area_m2'].sum(),
            'avg_area_m2': gdf['area_m2'].mean(),
            'max_area_m2': gdf['area_m2'].max(),
            'min_area_m2': gdf['area_m2'].min(),
            'avg_confidence': gdf['confidence'].mean(),
            'high_confidence_count': len(gdf[gdf['confidence'] >= 0.8]),
            'medium_confidence_count': len(gdf[(gdf['confidence'] >= 0.5) & (gdf['confidence'] < 0.8)]),
            'low_confidence_count': len(gdf[gdf['confidence'] < 0.5]),
            'avg_intensity': gdf['anomaly_intensity'].mean(),
            'density_per_km2': (len(gdf) / (gdf['area_m2'].sum() / 1e6)) if gdf['area_m2'].sum() > 0 else 0,
            'clustering_score': gdf['compactness'].mean()
        }
    
    def _classify_points(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        تصنيف النقاط حسب الأهمية
        """
        if gdf.empty:
            return gdf
        
        classified = gdf.copy()
        
        # تصنيف حسب الثقة
        conditions = [
            classified['confidence'] >= 0.8,
            (classified['confidence'] >= 0.6) & (classified['confidence'] < 0.8),
            classified['confidence'] < 0.6
        ]
        choices = ['high', 'medium', 'low']
        classified['confidence_level'] = np.select(conditions, choices, default='low')
        
        # تصنيف حسب الحجم
        if len(classified) > 1:
            area_percentiles = classified['area_m2'].quantile([0.33, 0.66])
            area_conditions = [
                classified['area_m2'] >= area_percentiles[0.66],
                (classified['area_m2'] >= area_percentiles[0.33]) & (classified['area_m2'] < area_percentiles[0.66]),
                classified['area_m2'] < area_percentiles[0.33]
            ]
            area_choices = ['large', 'medium', 'small']
            classified['size_category'] = np.select(area_conditions, area_choices, default='small')
        else:
            classified['size_category'] = 'medium'
        
        # حساب درجة الأهمية
        classified['importance_score'] = (
            classified['confidence'] * 0.4 +
            (classified['area_m2'] / classified['area_m2'].max()) * 0.3 +
            classified['compactness'] * 0.3
        )
        
        # تصنيف الأهمية
        importance_conditions = [
            classified['importance_score'] >= 0.7,
            (classified['importance_score'] >= 0.4) & (classified['importance_score'] < 0.7),
            classified['importance_score'] < 0.4
        ]
        importance_choices = ['high_priority', 'medium_priority', 'low_priority']
        classified['priority'] = np.select(importance_conditions, importance_choices, default='low_priority')
        
        # التوصيات
        classified['recommended_action'] = classified.apply(self._get_recommended_action, axis=1)
        
        return classified
    
    def _get_recommended_action(self, site) -> str:
        """
        توليد توصية
        """
        if site['priority'] == 'high_priority' and site['confidence'] >= 0.8:
            return "Field verification recommended - High probability"
        elif site['confidence'] >= 0.6:
            return "Further analysis recommended - Medium confidence"
        else:
            return "Monitor for changes - Low confidence"
    
    def _generate_detailed_report(self, gdf: gpd.GeoDataFrame, stats: Dict) -> Dict:
        """
        إنشاء تقرير مفصل
        """
        report = {
            'executive_summary': {
                'total_sites': len(gdf),
                'high_priority_sites': len(gdf[gdf['priority'] == 'high_priority']),
                'total_area_covered': f"{stats.get('total_area_m2', 0):.0f} m²",
                'average_confidence': f"{stats.get('avg_confidence', 0):.2%}"
            },
            'top_sites': [],
            'recommendations': []
        }
        
        if not gdf.empty:
            top_sites = gdf.nlargest(min(5, len(gdf)), 'importance_score')
            for idx, site in top_sites.iterrows():
                report['top_sites'].append({
                    'site_id': site['cluster_id'],
                    'coordinates': {
                        'latitude': site['centroid_lat'],
                        'longitude': site['centroid_lon']
                    },
                    'confidence': f"{site['confidence']:.2%}",
                    'area': f"{site['area_m2']:.0f} m²",
                    'priority': site['priority'],
                    'recommended_action': site['recommended_action']
                })
            
            report['recommendations'] = self._generate_recommendations(stats)
        
        return report
    
    def _generate_recommendations(self, stats: Dict) -> List[str]:
        """
        توليد قائمة التوصيات
        """
        recommendations = []
        
        if stats.get('high_confidence_count', 0) > 0:
            recommendations.append(
                f"{stats['high_confidence_count']} high-confidence sites detected. "
                "Consider field verification."
            )
        
        if stats.get('total_area_m2', 0) > 10000:
            recommendations.append(
                f"Large total area ({stats['total_area_m2']:.0f} m²) detected. "
                "Consider phased investigation."
            )
        
        return recommendations

    def export_to_formats(
        self,
        gdf: gpd.GeoDataFrame,
        output_dir: str,
        base_name: str,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        تصدير النتائج
        """
        if formats is None:
            formats = self.config['output']['formats']
        
        exported_files = {}
        
        for fmt in formats:
            try:
                if fmt.lower() == 'geojson':
                    path = f"{output_dir}/{base_name}.geojson"
                    gdf.to_file(path, driver='GeoJSON')
                    exported_files['geojson'] = path
                
                elif fmt.lower() == 'csv':
                    path = f"{output_dir}/{base_name}.csv"
                    csv_data = gdf[['cluster_id', 'centroid_lon', 'centroid_lat', 
                                   'confidence', 'area_m2', 'priority']].copy()
                    csv_data.to_csv(path, index=False)
                    exported_files['csv'] = path
                    
            except Exception as e:
                self.logger.error(f"خطأ في تصدير {fmt}: {e}")
        
        return exported_files
