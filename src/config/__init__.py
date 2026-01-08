"""
حزمة الإعدادات والتكوين - Heritage Sentinel Pro
"""
import yaml
from pathlib import Path

def load_config(config_path='config/config.yaml'):
    """
    تحميل ملف التكوين الرئيسي
    
    Args:
        config_path: مسار ملف التكوين
        
    Returns:
        dict: بيانات التكوين
    """
    config_file = Path(config_path)
    
    # إذا لم يوجد الملف، استخدم تكوين افتراضي
    if not config_file.exists():
        return {
            'app': {
                'name': 'Heritage Sentinel Pro',
                'version': '1.0.0'
            },
            'satellite': {
                'providers': {
                    'sentinel': {
                        'resolution': 10
                    }
                }
            },
            'processing': {
                'coordinate_extraction': {
                    'min_anomaly_area': 100,
                    'confidence_threshold': 0.7,
                    'cluster_distance': 50
                }
            },
            'output': {
                'formats': ['geojson', 'csv']
            },
            'paths': {
                'outputs': 'outputs',
                'exports': 'exports',
                'data': 'data'
            }
        }
    
    # تحميل من الملف
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
