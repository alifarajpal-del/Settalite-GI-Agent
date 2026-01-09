"""
Schema Normalizer for Heritage Sentinel Pro
Ensures consistent data structure across all data sources (mock, synthetic, real)
Prevents UI/pipeline breakage due to column name changes
"""
import pandas as pd
import numpy as np
from typing import Union, Tuple, List
import logging

logger = logging.getLogger(__name__)

# Canonical column mapping (Arabic → English)
COLUMN_MAPPING = {
    # Arabic columns from MockDataService
    'ID الموقع': 'id',
    'خط الطول': 'lon',
    'خط العرض': 'lat',
    'الثقة (%)': 'confidence',
    'المساحة (م²)': 'area_m2',
    'الأولوية': 'priority',
    'الأولوية (EN)': 'priority',  # Already English
    'النوع المحتمل': 'site_type',
    'شدة الشذوذ': 'anomaly_intensity',
    'التوصية': 'recommendation',
    'تاريخ الاكتشاف': 'detection_date',
    
    # English columns (pass through)
    'id': 'id',
    'lon': 'lon',
    'lat': 'lat',
    'longitude': 'lon',
    'latitude': 'lat',
    'confidence': 'confidence',
    'area_m2': 'area_m2',
    'priority': 'priority',
    'site_type': 'site_type',
    'geometry': 'geometry'
}

# Required columns for valid output
REQUIRED_COLUMNS = ['id', 'lat', 'lon', 'confidence', 'priority', 'area_m2']

# Priority levels
PRIORITY_LEVELS = ['high', 'medium', 'low']


def normalize_detections(df_or_gdf) -> 'pd.DataFrame':
    """
    Normalize detection data to canonical schema.
    
    Canonical schema (ENGLISH, stable):
    - id: string
    - lat: float [-90, 90]
    - lon: float [-180, 180]
    - confidence: float [0, 100]
    - priority: "high"|"medium"|"low"
    - area_m2: float > 0
    - site_type: string (optional)
    - geometry: Point (geopandas)
    
    Args:
        df_or_gdf: DataFrame or GeoDataFrame with detection data
    
    Returns:
        DataFrame with canonical columns and validated data
    
    Raises:
        ValueError: If critical columns (lat/lon) are missing after mapping
    """
    if df_or_gdf is None or (hasattr(df_or_gdf, 'empty') and df_or_gdf.empty):
        # Return empty dataframe with canonical schema
        return pd.DataFrame(columns=REQUIRED_COLUMNS + ['site_type', 'geometry'])
    
    df = df_or_gdf.copy()
    
    # Step 1: Map column names
    df = _map_column_names(df)
    
    # Step 2: Validate required columns
    if not _validate_required_columns(df):
        raise ValueError(
            f"Missing critical columns after normalization. "
            f"Required: {REQUIRED_COLUMNS}, Found: {list(df.columns)}"
        )
    
    # Step 3: Clamp and normalize values
    df['confidence'] = _clamp_confidence(df['confidence'])
    df['priority'] = _normalize_priority(df['priority'], df['confidence'])
    df['lat'] = _clamp_latitude(df['lat'])
    df['lon'] = _clamp_longitude(df['lon'])
    df['area_m2'] = _normalize_area(df.get('area_m2'))
    
    # Step 4: Ensure proper data types
    df['id'] = df['id'].astype(str)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce')
    df['area_m2'] = pd.to_numeric(df['area_m2'], errors='coerce')
    
    # Step 5: Drop rows with invalid coordinates
    initial_count = len(df)
    df = df.dropna(subset=['lat', 'lon'])
    dropped_count = initial_count - len(df)
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows with invalid coordinates")
    
    # Step 6: Convert to GeoDataFrame if geometry exists or can be created
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        
        if 'geometry' not in df.columns or df['geometry'].isna().any():
            # Create geometry from lat/lon
            df['geometry'] = [Point(lon, lat) for lon, lat in zip(df['lon'], df['lat'])]
        
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
        
        logger.info(f"Normalized {len(gdf)} detections to canonical schema")
        return gdf
    
    except ImportError:
        logger.warning("GeoPandas not available - returning DataFrame without geometry")
        return df


def _map_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map column names to canonical English names.
    
    Args:
        df: DataFrame with potentially mixed column names
    
    Returns:
        DataFrame with English column names
    """
    # Build rename dictionary for columns present in dataframe
    rename_dict = {}
    for col in df.columns:
        if col in COLUMN_MAPPING:
            rename_dict[col] = COLUMN_MAPPING[col]
    
    if rename_dict:
        df = df.rename(columns=rename_dict)
        logger.debug(f"Mapped columns: {list(rename_dict.keys())} → {list(rename_dict.values())}")
    
    return df


def _validate_required_columns(df: pd.DataFrame) -> bool:
    """
    Check if required columns are present after mapping.
    
    Args:
        df: DataFrame to validate
    
    Returns:
        True if all required columns present, False otherwise
    """
    # Check for coordinates (critical)
    has_lat = 'lat' in df.columns or 'خط العرض' in df.columns
    has_lon = 'lon' in df.columns or 'خط الطول' in df.columns
    
    if not (has_lat and has_lon):
        return False
    
    # Generate missing non-critical columns with defaults
    if 'id' not in df.columns:
        df['id'] = [f"SITE_{i+1:04d}" for i in range(len(df))]
        logger.info("Generated missing 'id' column")
    
    if 'confidence' not in df.columns:
        df['confidence'] = 50.0  # Neutral default
        logger.info("Generated missing 'confidence' column with default 50.0")
    
    if 'area_m2' not in df.columns:
        df['area_m2'] = 1000.0  # Default area estimate
        logger.info("Generated missing 'area_m2' column with default 1000.0")
    
    if 'priority' not in df.columns:
        # Will be derived from confidence in _normalize_priority
        df['priority'] = 'medium'
    
    return True


def _clamp_confidence(values: pd.Series) -> pd.Series:
    """
    Clamp confidence values to [0, 100] range.
    
    Args:
        values: Series of confidence values
    
    Returns:
        Series with clamped values
    """
    # Handle missing values
    values = values.fillna(50.0)
    
    # Clamp to valid range
    values = values.clip(0.0, 100.0)
    
    return values


def _normalize_priority(priority_values: pd.Series, confidence_values: pd.Series) -> pd.Series:
    """
    Normalize priority levels to canonical values.
    
    Rules:
    - high: confidence >= 80
    - medium: confidence >= 60
    - low: confidence < 60
    
    Args:
        priority_values: Series of priority values (may be in Arabic or English)
        confidence_values: Series of confidence values for derivation
    
    Returns:
        Series with normalized priority values
    """
    normalized = []
    
    for priority, confidence in zip(priority_values, confidence_values):
        # First try to use existing priority if valid
        if isinstance(priority, str):
            priority_lower = priority.lower()
            
            # Map Arabic to English
            if priority_lower in ['عالي', 'high']:
                normalized.append('high')
                continue
            elif priority_lower in ['متوسط', 'medium']:
                normalized.append('medium')
                continue
            elif priority_lower in ['منخفض', 'low']:
                normalized.append('low')
                continue
        
        # Derive from confidence if priority invalid
        if pd.isna(confidence):
            confidence = 50.0
        
        if confidence >= 80:
            normalized.append('high')
        elif confidence >= 60:
            normalized.append('medium')
        else:
            normalized.append('low')
    
    return pd.Series(normalized, index=priority_values.index)


def _clamp_latitude(values: pd.Series) -> pd.Series:
    """
    Clamp latitude values to [-90, 90] range.
    
    Args:
        values: Series of latitude values
    
    Returns:
        Series with clamped values
    """
    values = pd.to_numeric(values, errors='coerce')
    values = values.clip(-90.0, 90.0)
    return values


def _clamp_longitude(values: pd.Series) -> pd.Series:
    """
    Clamp longitude values to [-180, 180] range.
    
    Args:
        values: Series of longitude values
    
    Returns:
        Series with clamped values
    """
    values = pd.to_numeric(values, errors='coerce')
    
    # Handle values wrapped around (e.g., 185 → -175)
    values = ((values + 180) % 360) - 180
    
    return values


def _normalize_area(values: pd.Series) -> pd.Series:
    """
    Normalize area values, ensuring positive values.
    
    Args:
        values: Series of area values
    
    Returns:
        Series with normalized area values
    """
    if values is None:
        return pd.Series([1000.0] * len(values))
    
    values = pd.to_numeric(values, errors='coerce')
    values = values.fillna(1000.0)  # Default area
    
    # Ensure positive
    values = values.abs()
    
    # Set minimum area (avoid zeros)
    values = values.clip(lower=100.0)
    
    return values


def get_canonical_schema() -> List[str]:
    """
    Get list of canonical column names.
    
    Returns:
        List of canonical column names
    """
    return REQUIRED_COLUMNS + ['site_type', 'geometry']


def validate_dataframe_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate if dataframe conforms to canonical schema.
    
    Args:
        df: DataFrame to validate
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required columns
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors
    
    # Check data types and ranges
    if 'lat' in df.columns:
        invalid_lat = df[(df['lat'] < -90) | (df['lat'] > 90)]
        if len(invalid_lat) > 0:
            errors.append(f"Found {len(invalid_lat)} rows with invalid latitude")
    
    if 'lon' in df.columns:
        invalid_lon = df[(df['lon'] < -180) | (df['lon'] > 180)]
        if len(invalid_lon) > 0:
            errors.append(f"Found {len(invalid_lon)} rows with invalid longitude")
    
    if 'confidence' in df.columns:
        invalid_conf = df[(df['confidence'] < 0) | (df['confidence'] > 100)]
        if len(invalid_conf) > 0:
            errors.append(f"Found {len(invalid_conf)} rows with invalid confidence")
    
    if 'priority' in df.columns:
        invalid_priority = df[~df['priority'].isin(PRIORITY_LEVELS)]
        if len(invalid_priority) > 0:
            errors.append(f"Found {len(invalid_priority)} rows with invalid priority")
    
    return len(errors) == 0, errors
