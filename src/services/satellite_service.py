"""
خدمة جلب بيانات الأقمار الصناعية
"""
import numpy as np
from numpy.random import default_rng
from datetime import datetime
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')

class SatelliteService:
    """
    خدمة لجلب ومعالجة بيانات الأقمار الصناعية
    """
    
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger
        self.sentinel_config = config['satellite']['providers']['sentinel']
        self._rasterio_available = None
    
    def _has_rasterio(self) -> bool:
        """فحص توفر مكتبة rasterio"""
        if self._rasterio_available is None:
            try:
                import rasterio
                self._rasterio_available = True
            except ImportError:
                self._rasterio_available = False
        return self._rasterio_available
    
    def download_sentinel_data(
        self,
        aoi_geometry,
        start_date: str,
        end_date: str,
        max_cloud_cover: int = 30
    ) -> Dict:
        """
        جلب بيانات Sentinel-2
        
        Args:
            aoi_geometry: منطقة الاهتمام (GeoDataFrame أو Shapely geometry)
            start_date: تاريخ البداية (YYYY-MM-DD)
            end_date: تاريخ النهاية (YYYY-MM-DD)
            max_cloud_cover: أقصى نسبة للغيوم (0-100)
        
        Returns:
            قاموس يحتوي على البيانات: bands, metadata, transform, crs, bounds
        
        Raises:
            ValueError: إذا كان aoi_geometry فارغاً أو غير صالح
        """
        # فحص صحة aoi_geometry
        if aoi_geometry is None:
            raise ValueError("aoi_geometry لا يمكن أن يكون None")
        
        self.logger.info(f"جلب بيانات Sentinel-2 من {start_date} إلى {end_date}")
        self.logger.info(f"منطقة الاهتمام: {aoi_geometry.bounds if hasattr(aoi_geometry, 'bounds') else 'غير محددة'}")
        
        try:
            # في بيئة إنتاجية، استخدم sentinelhub أو sentinelsat
            # هنا نستخدم بيانات تجريبية
            rng = default_rng(42)
            
            # محاكاة البيانات باستخدام aoi_geometry
            bands_data = self._simulate_satellite_data(aoi_geometry)
            
            result = {
                'bands': bands_data,
                'metadata': {
                    'satellite': 'Sentinel-2',
                    'acquisition_date': end_date,
                    'cloud_cover': rng.integers(0, max_cloud_cover),
                    'resolution': self.sentinel_config['resolution']
                },
                'transform': self._get_transform(aoi_geometry) if self._has_rasterio() else None,
                'crs': 'EPSG:4326',
                'bounds': aoi_geometry.bounds
            }
            
            self.logger.info("تم جلب البيانات بنجاح")
            return result
            
        except Exception as e:
            self.logger.error(f"خطأ في جلب البيانات: {e}")
            raise
    
    def _simulate_satellite_data(self, aoi_geometry) -> Dict[str, np.ndarray]:
        """
        محاكاة بيانات الأقمار الصناعية للتطوير والاختبار
        
        Args:
            aoi_geometry: منطقة الاهتمام لحساب حجم الصورة
        
        Returns:
            قاموس من اسم النطاق إلى مصفوفة numpy بقيم الانعكاسية (0-1)
        """
        rng = default_rng(42)
        bounds = aoi_geometry.bounds
        
        # حساب العرض والارتفاع بناءً على حدود AOI
        width = int((bounds[2] - bounds[0]) * 1000)  # تحويل من درجات إلى تقريبي بالأمتار
        height = int((bounds[3] - bounds[1]) * 1000)
        
        # تحديد الحجم
        width = min(max(width, 100), 1000)
        height = min(max(height, 100), 1000)
        
        bands = {}
        for band_name in self.sentinel_config['bands']['optical']:
            # إنشاء بيانات عشوائية واقعية
            if band_name in ['B02', 'B03', 'B04']:  # RGB
                data = rng.normal(0.3, 0.1, (height, width))
            elif band_name == 'B08':  # NIR
                data = rng.normal(0.5, 0.15, (height, width))
            else:  # SWIR
                data = rng.normal(0.2, 0.08, (height, width))
            
            # إضافة بعض الشذوذ
            num_anomalies = rng.integers(5, 15)
            for _ in range(num_anomalies):
                y = rng.integers(0, height)
                x = rng.integers(0, width)
                size = rng.integers(5, 20)
                
                y_start = max(0, y - size)
                y_end = min(height, y + size)
                x_start = max(0, x - size)
                x_end = min(width, x + size)
                
                data[y_start:y_end, x_start:x_end] *= 0.7
            
            bands[band_name] = np.clip(data, 0, 1)
        
        return bands
    
    def _get_transform(self, aoi_geometry):
        """
        Get coordinate transform (requires rasterio)
        
        Raises:
            DependencyMissingError: If rasterio is not installed
        """
        try:
            from rasterio.transform import from_bounds
        except ImportError:
            from src.utils.dependency_errors import DependencyMissingError
            raise DependencyMissingError(
                missing_libs=['rasterio'],
                operation='satellite data coordinate transform',
                install_hint='pip install -r requirements_core.txt -r requirements_geo.txt',
                is_critical=True
            )
        
        bounds = aoi_geometry.bounds
        width = 500
        height = 500
        
        return from_bounds(
            bounds[0], bounds[1], bounds[2], bounds[3],
            width, height
        )
    
    def search_available_images(
        self,
        start_date: str,
        end_date: str,
        max_cloud_cover: int = 30
    ) -> List[Dict]:
        """
        البحث عن الصور المتاحة
        
        Returns:
            قائمة بالصور المتاحة
        """
        self.logger.info("البحث عن الصور المتاحة...")
        
        # في بيئة إنتاجية، استخدم API البحث الفعلي
        # هنا محاكاة بسيطة
        
        images = []
        rng = default_rng(42)
        num_images = rng.integers(3, 10)
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        for i in range(num_images):
            acquisition_date = start + (end - start) * rng.random()
            
            images.append({
                'id': f"S2_{acquisition_date.strftime('%Y%m%d')}_{i}",
                'date': acquisition_date.strftime("%Y-%m-%d"),
                'cloud_cover': rng.integers(0, max_cloud_cover),
                'satellite': 'Sentinel-2',
                'processing_level': 'Level-2A'
            })
        
        images.sort(key=lambda x: x['date'])
        
        self.logger.info(f"تم العثور على {len(images)} صورة")
        return images
