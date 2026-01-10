"""
أدوات جغرافية ومعالجة الإحداثيات
"""
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import transform
import pyproj
from typing import Tuple, List, Union
import geopandas as gpd

# Constants
EPSG_4326 = "EPSG:4326"  # WGS84
EPSG_3857 = "EPSG:3857"  # Web Mercator

def calculate_area_meters(geometry, crs: str = EPSG_4326) -> float:
    """
    حساب مساحة geometry بالمتر المربع
    
    Args:
        geometry: كائن Shapely geometry
        crs: نظام الإحداثيات الأصلي
    
    Returns:
        المساحة بالمتر المربع
    """
    if crs == EPSG_4326:
        # تحويل إلى نظام متري (Web Mercator)
        project = pyproj.Transformer.from_crs(
            EPSG_4326,
            EPSG_3857,
            always_xy=True
        ).transform
        
        geometry_projected = transform(project, geometry)
        return geometry_projected.area
    else:
        return geometry.area

def calculate_distance_meters(
    point1: Tuple[float, float],
    point2: Tuple[float, float],
    crs: str = EPSG_4326
) -> float:
    """
    حساب المسافة بين نقطتين بالمتر
    
    Args:
        point1: (lon, lat) أو (x, y)
        point2: (lon, lat) أو (x, y)
        crs: نظام الإحداثيات
    
    Returns:
        المسافة بالمتر
    """
    if crs == EPSG_4326:
        # استخدام صيغة Haversine
        lon1, lat1 = point1
        lon2, lat2 = point2
        
        R = 6371000  # نصف قطر الأرض بالمتر
        
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        delta_phi = np.radians(lat2 - lat1)
        delta_lambda = np.radians(lon2 - lon1)
        
        a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    else:
        # حساب مباشر للأنظمة المترية
        return np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def create_buffer(geometry, distance_meters: float, crs: str = EPSG_4326):
    """
    إنشاء منطقة عازلة حول geometry
    
    Args:
        geometry: كائن Shapely
        distance_meters: المسافة العازلة بالمتر
        crs: نظام الإحداثيات
    
    Returns:
        geometry جديد مع المنطقة العازلة
    """
    if crs == EPSG_4326:
        # تحويل لنظام متري
        project_to_metric = pyproj.Transformer.from_crs(
            EPSG_4326,
            EPSG_3857,
            always_xy=True
        ).transform
        
        project_to_geo = pyproj.Transformer.from_crs(
            "EPSG:3857",
            "EPSG:4326",
            always_xy=True
        ).transform
        
        # تطبيق Buffer في النظام المتري
        geometry_metric = transform(project_to_metric, geometry)
        buffered_metric = geometry_metric.buffer(distance_meters)
        buffered_geo = transform(project_to_geo, buffered_metric)
        
        return buffered_geo
    else:
        return geometry.buffer(distance_meters)

def reproject_geometry(geometry, from_crs: str, to_crs: str):
    """
    إعادة إسقاط geometry إلى نظام إحداثيات آخر
    
    Args:
        geometry: كائن Shapely
        from_crs: النظام الأصلي
        to_crs: النظام المستهدف
    
    Returns:
        geometry مُعاد إسقاطه
    """
    project = pyproj.Transformer.from_crs(
        from_crs,
        to_crs,
        always_xy=True
    ).transform
    
    return transform(project, geometry)

def create_grid(
    bounds: Tuple[float, float, float, float],
    cell_size: float,
    crs: str = EPSG_4326
) -> gpd.GeoDataFrame:
    """
    إنشاء شبكة من المربعات
    
    Args:
        bounds: (minx, miny, maxx, maxy)
        cell_size: حجم الخلية
        crs: نظام الإحداثيات
    
    Returns:
        GeoDataFrame يحتوي على الشبكة
    """
    minx, miny, maxx, maxy = bounds
    
    cols = np.arange(minx, maxx, cell_size)
    rows = np.arange(miny, maxy, cell_size)
    
    polygons = []
    for x in cols:
        for y in rows:
            polygons.append(box(x, y, x + cell_size, y + cell_size))
    
    grid = gpd.GeoDataFrame({'geometry': polygons}, crs=crs)
    return grid

def validate_coordinates(
    lat: float,
    lon: float,
    bounds: Tuple[float, float, float, float] = None
) -> bool:
    """
    التحقق من صحة الإحداثيات
    
    Args:
        lat: خط العرض
        lon: خط الطول
        bounds: حدود مسموحة (minx, miny, maxx, maxy)
    
    Returns:
        True إذا كانت صالحة
    """
    # فحص نطاق الإحداثيات العالمي
    if not (-90 <= lat <= 90):
        return False
    if not (-180 <= lon <= 180):
        return False
    
    # فحص الحدود المخصصة
    if bounds:
        minx, miny, maxx, maxy = bounds
        if not (minx <= lon <= maxx and miny <= lat <= maxy):
            return False
    
    return True

def get_utm_zone(lon: float, lat: float) -> str:
    """
    الحصول على منطقة UTM المناسبة للإحداثيات
    
    Args:
        lon: خط الطول
        lat: خط العرض
    
    Returns:
        كود EPSG لمنطقة UTM
    """
    zone_number = int((lon + 180) / 6) + 1
    
    if lat >= 0:
        # نصف الكرة الشمالي
        epsg_code = 32600 + zone_number
    else:
        # نصف الكرة الجنوبي
        epsg_code = 32700 + zone_number
    
    return f"EPSG:{epsg_code}"

def simplify_geometry(geometry, tolerance: float = 0.0001):
    """
    تبسيط geometry للحد من نقاط الرؤوس
    
    Args:
        geometry: كائن Shapely
        tolerance: مستوى التسامح
    
    Returns:
        geometry مُبسط
    """
    return geometry.simplify(tolerance, preserve_topology=True)
