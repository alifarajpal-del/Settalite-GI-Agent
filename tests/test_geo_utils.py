"""
اختبارات للأدوات الجغرافية
"""
import pytest
import numpy as np
from shapely.geometry import Point, Polygon
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.utils.geo_utils import (
    calculate_area_meters,
    calculate_distance_meters,
    validate_coordinates
)

def test_validate_coordinates():
    """اختبار التحقق من صحة الإحداثيات"""
    assert validate_coordinates(30.0, 31.0) == True
    assert validate_coordinates(100.0, 31.0) == False
    assert validate_coordinates(30.0, 200.0) == False

def test_calculate_distance():
    """اختبار حساب المسافة"""
    point1 = (30.0, 31.0)
    point2 = (30.1, 31.1)
    
    distance = calculate_distance_meters(point1, point2)
    assert distance > 0
    assert distance < 20000  # يجب أن تكون أقل من 20 كم

def test_calculate_area():
    """اختبار حساب المساحة"""
    polygon = Polygon([
        (30.0, 31.0),
        (30.1, 31.0),
        (30.1, 31.1),
        (30.0, 31.1),
        (30.0, 31.0)
    ])
    
    area = calculate_area_meters(polygon)
    assert area > 0
