"""
خدمة التصدير
"""
import os
import geopandas as gpd
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')

class ExportService:
    """
    خدمة تصدير النتائج بتنسيقات متعددة
    """
    
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger
    
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
        
        # إنشاء المجلد إذا لم يكن موجوداً
        os.makedirs(output_dir, exist_ok=True)
        
        # إعادة إسقاط إذا لزم الأمر
        if gdf.crs != output_crs:
            gdf = gdf.to_crs(output_crs)
        
        exported = {}
        
        for fmt in formats:
            try:
                if fmt.lower() == 'geojson':
                    path = os.path.join(output_dir, f"{base_name}.geojson")
                    gdf.to_file(path, driver='GeoJSON')
                    exported['geojson'] = path
                
                elif fmt.lower() == 'csv':
                    path = os.path.join(output_dir, f"{base_name}.csv")
                    df = gdf.copy()
                    df['longitude'] = df.geometry.x.round(precision)
                    df['latitude'] = df.geometry.y.round(precision)
                    df = df.drop(columns=['geometry'])
                    df.to_csv(path, index=False)
                    exported['csv'] = path
                
                elif fmt.lower() == 'excel':
                    path = os.path.join(output_dir, f"{base_name}.xlsx")
                    df = gdf.copy()
                    df['longitude'] = df.geometry.x.round(precision)
                    df['latitude'] = df.geometry.y.round(precision)
                    df = df.drop(columns=['geometry'])
                    df.to_excel(path, index=False)
                    exported['excel'] = path
                
                self.logger.info(f"تم التصدير بنجاح: {fmt}")
                
            except Exception as e:
                self.logger.error(f"خطأ في تصدير {fmt}: {e}")
        
        self.logger.info(f"تم تصدير {len(exported)} ملف")
        return exported
