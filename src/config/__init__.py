"""
حزمة الإعدادات والتكوين - Heritage Sentinel Pro

Unified configuration system with:
- Environment variable merging (.env support)
- Complete default configuration
- Validation
- SentinelHub integration
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_default_config() -> Dict[str, Any]:
    """
    Get complete default configuration with all required keys
    
    This ensures the system works even without config.yaml
    """
    return {
        'app': {
            'name': 'Heritage Sentinel Pro',
            'version': '1.0.0',
            'debug': False,
            'log_level': 'INFO'
        },
        'satellite': {
            'providers': {
                'sentinel': {
                    'resolution': 10,
                    'bands': {
                        'optical': ['B02', 'B03', 'B04', 'B08', 'B11', 'B12'],
                        'sar': ['VV', 'VH']
                    },
                    'client_id': None,
                    'client_secret': None,
                    'instance_id': None
                }
            },
            'default_cloud_cover': 30,
            'max_cloud_cover': 80
        },
        'processing': {
            'coordinate_extraction': {
                'min_anomaly_area': 100,
                'confidence_threshold': 0.7,
                'cluster_distance': 50,
                'min_cluster_size': 3
            },
            'anomaly_detection': {
                'contamination': 0.1,
                'n_neighbors': 20,
                'algorithm': 'isolation_forest'
            },
            'spectral_indices': {
                'ndvi': {
                    'enabled': True,
                    'bands': ['B08', 'B04']
                },
                'ndwi': {
                    'enabled': True,
                    'bands': ['B03', 'B08']
                },
                'bai': {
                    'enabled': True,
                    'bands': ['B08', 'B12']
                }
            }
        },
        'output': {
            'formats': ['geojson', 'csv', 'shapefile'],
            'coordinate_system': 'EPSG:4326'
        },
        'paths': {
            'outputs': 'outputs',
            'exports': 'exports',
            'data': 'data',
            'cache': '.cache',
            'logs': 'logs'
        }
    }


def merge_env_variables(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge environment variables into configuration
    
    Supports:
    - SENTINELHUB_CLIENT_ID, SENTINELHUB_CLIENT_SECRET, SENTINELHUB_INSTANCE_ID
    - APP_DEBUG, LOG_LEVEL
    """
    # SentinelHub credentials
    if 'SENTINELHUB_CLIENT_ID' in os.environ:
        config['satellite']['providers']['sentinel']['client_id'] = os.getenv('SENTINELHUB_CLIENT_ID')
    if 'SENTINELHUB_CLIENT_SECRET' in os.environ:
        config['satellite']['providers']['sentinel']['client_secret'] = os.getenv('SENTINELHUB_CLIENT_SECRET')
    if 'SENTINELHUB_INSTANCE_ID' in os.environ:
        config['satellite']['providers']['sentinel']['instance_id'] = os.getenv('SENTINELHUB_INSTANCE_ID')
    
    # Application settings
    if 'APP_DEBUG' in os.environ:
        config['app']['debug'] = os.getenv('APP_DEBUG', 'false').lower() == 'true'
    if 'LOG_LEVEL' in os.environ:
        config['app']['log_level'] = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    return config


def validate_config(config: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate configuration for required keys
    
    Returns:
        (is_valid, warnings_list)
    """
    warnings = []
    
    # Check critical paths
    required_keys = {
        'app.name': lambda c: 'app' in c and 'name' in c['app'],
        'satellite.providers.sentinel': lambda c: 'satellite' in c and 'providers' in c['satellite'] and 'sentinel' in c['satellite']['providers'],
        'processing.coordinate_extraction': lambda c: 'processing' in c and 'coordinate_extraction' in c['processing'],
        'paths.outputs': lambda c: 'paths' in c and 'outputs' in c['paths']
    }
    
    for key, check in required_keys.items():
        if not check(config):
            warnings.append(f"Missing configuration: {key}")
    
    return len(warnings) == 0, warnings


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration with fallback and environment variable merging
    
    Priority:
    1. Streamlit secrets (if available)
    2. Specified config_path
    3. config/config.yaml (if exists)
    4. Default configuration
    5. Environment variable overlay
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Complete configuration dictionary
    """
    # Start with default configuration
    config = get_default_config()
    
    # Determine config file path
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    else:
        config_path = Path(config_path)
    
    # Load from file if exists
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    # Deep merge file config over defaults
                    config = deep_merge(config, file_config)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            print("Using default configuration")
    
    # Merge environment variables
    config = merge_env_variables(config)
    
    # Merge Streamlit secrets (highest priority for credentials)
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            # Merge sentinelhub secrets
            if 'sentinelhub' in st.secrets:
                if 'sentinelhub' not in config:
                    config['sentinelhub'] = {}
                # Convert Streamlit secrets to dict and merge
                sh_secrets = dict(st.secrets['sentinelhub'])
                config['sentinelhub'].update(sh_secrets)
                
                # Log success (without revealing secrets)
                if sh_secrets.get('client_id') and sh_secrets.get('client_secret'):
                    print("✓ Sentinel Hub OAuth credentials loaded from Streamlit secrets")
            
            # Merge gee secrets
            if 'gee' in st.secrets:
                if 'gee' not in config:
                    config['gee'] = {}
                config['gee'].update(dict(st.secrets['gee']))
    except (ImportError, FileNotFoundError, AttributeError) as e:
        # Not in Streamlit environment or secrets not configured
        pass
    
    # Validate
    is_valid, warnings = validate_config(config)
    if not is_valid:
        print(f"Configuration warnings: {warnings}")
    
    return config


def deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Deep merge two dictionaries
    
    Args:
        base: Base dictionary
        override: Dictionary with overriding values
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result

