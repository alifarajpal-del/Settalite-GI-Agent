"""
اختبارات لخدمة كشف الشذوذ
"""
import pytest
import numpy as np
from numpy.random import default_rng
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.services.detection_service import AnomalyDetectionService
from src.utils.logging_utils import setup_logger

def test_anomaly_detection():
    """اختبار كشف الشذوذ"""
    # إعداد التكوين
    config = {
        'paths': {'outputs': 'outputs'},
        'processing': {
            'anomaly_detection': {
                'method': 'isolation_forest',
                'contamination': 0.1
            }
        }
    }
    
    logger = setup_logger('outputs')
    detector = AnomalyDetectionService(config, logger)
    
    # إنشاء بيانات اختبار
    rng = default_rng()
    indices = {
        'NDVI': rng.standard_normal((100, 100)),
        'NDWI': rng.standard_normal((100, 100))
    }
    
    # تشغيل الكشف
    result = detector.detect_anomalies(indices)
    
    # التحقق من النتائج
    assert 'anomaly_map' in result
    assert 'anomaly_surface' in result
    assert 'statistics' in result
    assert result['statistics']['total_pixels'] == 10000
