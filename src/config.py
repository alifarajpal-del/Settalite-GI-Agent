"""
وحدة تحميل وإدارة التكوينات
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    تحميل ملف التكوين الرئيسي
    
    Args:
        config_path: مسار ملف التكوين (اختياري)
    
    Returns:
        قاموس يحتوي على جميع الإعدادات
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # دمج المتغيرات البيئية
    config = merge_env_variables(config)
    
    return config

def merge_env_variables(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    دمج المتغيرات البيئية مع التكوين
    """
    # Sentinel Hub credentials
    if 'SENTINELHUB_CLIENT_ID' in os.environ:
        if 'sentinel' not in config['satellite']['providers']:
            config['satellite']['providers']['sentinel'] = {}
        config['satellite']['providers']['sentinel']['client_id'] = os.getenv('SENTINELHUB_CLIENT_ID')
        config['satellite']['providers']['sentinel']['client_secret'] = os.getenv('SENTINELHUB_CLIENT_SECRET')
        config['satellite']['providers']['sentinel']['instance_id'] = os.getenv('SENTINELHUB_INSTANCE_ID')
    
    # Application settings
    if 'APP_DEBUG' in os.environ:
        config['app']['debug'] = os.getenv('APP_DEBUG', 'false').lower() == 'true'
    
    if 'LOG_LEVEL' in os.environ:
        config['app']['log_level'] = os.getenv('LOG_LEVEL', 'INFO')
    
    return config

def save_config(config: Dict[str, Any], config_path: str = None):
    """
    حفظ التكوين إلى ملف
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

class Config:
    """
    كلاس لإدارة التكوينات بشكل كائني
    """
    def __init__(self, config_path: str = None):
        self._config = load_config(config_path)
    
    def get(self, key: str, default=None):
        """
        الحصول على قيمة من التكوين باستخدام notation النقطة
        مثال: config.get('satellite.providers.sentinel.resolution')
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        تعيين قيمة في التكوين
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def raw(self) -> Dict[str, Any]:
        """
        الحصول على التكوين الكامل كقاموس
        """
        return self._config
