"""
خدمة التصدير - Export Service
Handles exporting detections to multiple formats with validation
"""
import os
import geopandas as gpd
import pandas as pd
from typing import List, Dict
import warnings
import logging

# Import GeoJSON validator
from src.utils.geojson_validator import create_valid_geojson, quick_geojson_test, get_geojson_statistics

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class ExportService:
    """
    خدمة تصدير النتائج بتنسيقات متعددة
    """
    
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger
    
    
    def _export_geojson(self, gdf, output_dir, base_name):
        """Export to GeoJSON format"""
        path = os.path.join(output_dir, f"{base_name}.geojson")
        df_export = gdf.copy()
        if 'geometry' in df_export.columns:
            if 'lat' not in df_export.columns:
                df_export['lat'] = df_export.geometry.y
            if 'lon' not in df_export.columns:
                df_export['lon'] = df_export.geometry.x
        
        geojson_bytes = create_valid_geojson(df_export)
        with open(path, 'wb') as f:
            f.write(geojson_bytes)
        
        is_valid = quick_geojson_test(geojson_bytes)
        if is_valid:
            logger.info("✓ GeoJSON validation passed")
        else:
            logger.warning("⚠ GeoJSON validation failed")
        
        stats = get_geojson_statistics(geojson_bytes)
        logger.info(f"  Size: {stats['size_kb']} KB, Features: {stats['feature_count']}")
        return path
    
    def _export_tabular(self, gdf, output_dir, base_name, fmt, precision):
        """Export to CSV or Excel format"""
        ext = 'csv' if fmt.lower() == 'csv' else 'xlsx'
        path = os.path.join(output_dir, f"{base_name}.{ext}")
        df = gdf.copy()
        df['longitude'] = df.geometry.x.round(precision)
        df['latitude'] = df.geometry.y.round(precision)
        df = df.drop(columns=['geometry'])
        
        if fmt.lower() == 'csv':
            df.to_csv(path, index=False)
        else:
            df.to_excel(path, index=False)
        return path
    
    def export_all(
        self,
        gdf: gpd.GeoDataFrame,
        formats: List[str],
        output_dir: str,
        base_name: str,
        output_crs: str = "EPSG:4326",
        precision: int = 6
    ) -> Dict[str, str]:
        """
        تصدير البيانات بتنسيقات متعددة
        
        Args:
            gdf: GeoDataFrame
            formats: قائمة التنسيقات
            output_dir: مجلد الإخراج
            base_name: اسم الملف الأساسي
            output_crs: نظام الإحداثيات
            precision: دقة الإحداثيات
        
        Returns:
            قاموس المسارات المصدرة
        """
        self.logger.info("بدء تصدير النتائج...")
        os.makedirs(output_dir, exist_ok=True)
        
        if gdf.crs != output_crs:
            gdf = gdf.to_crs(output_crs)
        
        exported = {}
        for fmt in formats:
            try:
                if fmt.lower() == 'geojson':
                    path = self._export_geojson(gdf, output_dir, base_name)
                    exported['geojson'] = path
                elif fmt.lower() in ('csv', 'excel'):
                    path = self._export_tabular(gdf, output_dir, base_name, fmt, precision)
                    exported[fmt.lower()] = path
                
                self.logger.info(f"تم التصدير بنجاح: {fmt}")
            except Exception as e:
                self.logger.error(f"خطأ في تصدير {fmt}: {e}")
        
        self.logger.info(f"تم تصدير {len(exported)} ملف")
        return exported
