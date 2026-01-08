"""
أدوات التحقق والتحقق من صحة البيانات
"""
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, Point
from typing import Union, List, Dict, Any

def validate_aoi(geometry) -> Dict[str, Any]:
    """
    التحقق من صحة منطقة الاهتمام (AOI)
    
    Args:
        geometry: كائن Shapely
    
    Returns:
        قاموس يحتوي على نتائج التحقق
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # التحقق من نوع geometry
    if not isinstance(geometry, (Polygon, Point)):
        results['valid'] = False
        results['errors'].append("يجب أن يكون AOI من نوع Polygon أو Point")
        return results
    
    # التحقق من صحة geometry
    if not geometry.is_valid:
        results['valid'] = False
        results['errors'].append("AOI غير صالح هندسياً")
        return results
    
    # التحقق من المساحة (للمضلعات)
    if isinstance(geometry, Polygon):
        area_deg = geometry.area
        
        # تقريب: 1 درجة ≈ 111 كم
        area_km2 = area_deg * (111 ** 2)
        
        if area_km2 > 1000:
            results['warnings'].append(f"المساحة كبيرة جداً ({area_km2:.0f} كم²). قد تستغرق المعالجة وقتاً طويلاً")
        
        if area_km2 < 0.01:
            results['warnings'].append(f"المساحة صغيرة جداً ({area_km2:.4f} كم²)")
    
    # التحقق من الحدود
    bounds = geometry.bounds
    minx, miny, maxx, maxy = bounds
    
    if not (-180 <= minx <= 180 and -180 <= maxx <= 180):
        results['valid'] = False
        results['errors'].append("خط الطول خارج النطاق الصحيح (-180 إلى 180)")
    
    if not (-90 <= miny <= 90 and -90 <= maxy <= 90):
        results['valid'] = False
        results['errors'].append("خط العرض خارج النطاق الصحيح (-90 إلى 90)")
    
    return results

def validate_date_range(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    التحقق من صحة الفترة الزمنية
    
    Args:
        start_date: تاريخ البداية (YYYY-MM-DD)
        end_date: تاريخ النهاية (YYYY-MM-DD)
    
    Returns:
        قاموس نتائج التحقق
    """
    from datetime import datetime
    
    results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # التحقق من الترتيب
        if start > end:
            results['valid'] = False
            results['errors'].append("تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
        
        # التحقق من المدة
        duration_days = (end - start).days
        
        if duration_days > 365:
            results['warnings'].append(f"الفترة طويلة ({duration_days} يوم). قد يؤدي إلى كمية كبيرة من البيانات")
        
        if duration_days < 7:
            results['warnings'].append(f"الفترة قصيرة ({duration_days} يوم). قد لا تحتوي على صور كافية")
        
        # التحقق من التاريخ المستقبلي
        now = datetime.now()
        if end > now:
            results['valid'] = False
            results['errors'].append("تاريخ النهاية في المستقبل")
    
    except ValueError as e:
        results['valid'] = False
        results['errors'].append(f"تنسيق تاريخ غير صحيح: {e}")
    
    return results

def validate_bands(bands: List[str], satellite: str = "sentinel-2") -> Dict[str, Any]:
    """
    التحقق من صحة النطاقات المطلوبة
    
    Args:
        bands: قائمة النطاقات
        satellite: نوع القمر الصناعي
    
    Returns:
        قاموس نتائج التحقق
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # نطاقات صالحة لكل قمر صناعي
    valid_bands = {
        'sentinel-2': ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 
                      'B08', 'B8A', 'B09', 'B10', 'B11', 'B12'],
        'landsat-8': ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11']
    }
    
    if satellite.lower() not in valid_bands:
        results['warnings'].append(f"قمر صناعي غير معروف: {satellite}")
        return results
    
    # التحقق من كل نطاق
    for band in bands:
        if band not in valid_bands[satellite.lower()]:
            results['valid'] = False
            results['errors'].append(f"نطاق غير صحيح: {band}")
    
    # التوصية بنطاقات أساسية
    essential_bands = {
        'sentinel-2': ['B04', 'B08', 'B11'],
        'landsat-8': ['B4', 'B5', 'B6']
    }
    
    missing_essential = set(essential_bands[satellite.lower()]) - set(bands)
    if missing_essential:
        results['warnings'].append(f"نطاقات أساسية مفقودة: {missing_essential}")
    
    return results

def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    التحقق من صحة ملف التكوين
    
    Args:
        config: قاموس التكوين
    
    Returns:
        قاموس نتائج التحقق
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # الحقول المطلوبة
    required_fields = [
        'app.name',
        'satellite.providers',
        'processing.anomaly_detection',
        'output.formats',
        'paths.data_dir'
    ]
    
    for field in required_fields:
        keys = field.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                results['valid'] = False
                results['errors'].append(f"حقل مطلوب مفقود: {field}")
                break
    
    # التحقق من القيم
    if 'processing' in config and 'anomaly_detection' in config['processing']:
        contamination = config['processing']['anomaly_detection'].get('contamination', 0.1)
        
        if not (0 < contamination < 0.5):
            results['warnings'].append(f"قيمة contamination غير نموذجية: {contamination}")
    
    return results

def validate_output_format(format_name: str) -> bool:
    """
    التحقق من صحة تنسيق الإخراج
    
    Args:
        format_name: اسم التنسيق
    
    Returns:
        True إذا كان صالحاً
    """
    valid_formats = [
        'geojson', 'kml', 'shapefile', 'csv', 
        'excel', 'geotiff', 'png', 'pdf'
    ]
    
    return format_name.lower() in valid_formats

def sanitize_filename(filename: str) -> str:
    """
    تنظيف اسم الملف من الأحرف غير الصالحة
    
    Args:
        filename: اسم الملف
    
    Returns:
        اسم ملف منظف
    """
    import re
    
    # إزالة الأحرف غير المسموحة
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # تحديد الطول الأقصى
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized
