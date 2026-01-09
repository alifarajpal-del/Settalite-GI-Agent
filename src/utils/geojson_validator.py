"""
GeoJSON Export Validator for Heritage Sentinel Pro
Ensures valid GeoJSON structure and coordinates
Prevents corrupted exports that fail to load in QGIS/geojson.io
"""
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

# Valid coordinate ranges
VALID_LAT_RANGE = (-90.0, 90.0)
VALID_LON_RANGE = (-180.0, 180.0)


def validate_geojson_structure(geojson_dict: Dict) -> Tuple[bool, List[str]]:
    """
    Validate GeoJSON structure according to RFC 7946.
    
    Args:
        geojson_dict: Dictionary representing GeoJSON object
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check top-level type
    if 'type' not in geojson_dict:
        errors.append("Missing 'type' field at root level")
        return False, errors
    
    if geojson_dict['type'] != 'FeatureCollection':
        errors.append(f"Expected type 'FeatureCollection', got '{geojson_dict['type']}'")
    
    # Check features array
    if 'features' not in geojson_dict:
        errors.append("Missing 'features' array")
        return False, errors
    
    features = geojson_dict['features']
    if not isinstance(features, list):
        errors.append("'features' must be an array")
        return False, errors
    
    # Validate each feature
    for i, feature in enumerate(features):
        feature_errors = _validate_feature(feature, i)
        errors.extend(feature_errors)
    
    return len(errors) == 0, errors


def _validate_feature(feature: Dict, index: int) -> List[str]:
    """
    Validate a single GeoJSON feature.
    
    Args:
        feature: Feature dictionary
        index: Feature index for error reporting
    
    Returns:
        List of error messages
    """
    errors = []
    prefix = f"Feature {index}"
    
    # Check type
    if 'type' not in feature:
        errors.append(f"{prefix}: Missing 'type' field")
        return errors
    
    if feature['type'] != 'Feature':
        errors.append(f"{prefix}: Expected type 'Feature', got '{feature['type']}'")
    
    # Check geometry
    if 'geometry' not in feature:
        errors.append(f"{prefix}: Missing 'geometry' field")
    else:
        geometry_errors = _validate_geometry(feature['geometry'], index)
        errors.extend(geometry_errors)
    
    # Check properties (optional but recommended)
    if 'properties' not in feature:
        logger.debug(f"{prefix}: Missing 'properties' field (optional)")
    elif not isinstance(feature['properties'], dict):
        errors.append(f"{prefix}: 'properties' must be an object")
    
    return errors


def _validate_geometry(geometry: Dict, feature_index: int) -> List[str]:
    """
    Validate geometry object.
    
    Args:
        geometry: Geometry dictionary
        feature_index: Feature index for error reporting
    
    Returns:
        List of error messages
    """
    errors = []
    prefix = f"Feature {feature_index} geometry"
    
    if 'type' not in geometry:
        errors.append(f"{prefix}: Missing 'type' field")
        return errors
    
    geom_type = geometry['type']
    
    if 'coordinates' not in geometry:
        errors.append(f"{prefix}: Missing 'coordinates' field")
        return errors
    
    coords = geometry['coordinates']
    
    # Validate based on geometry type
    if geom_type == 'Point':
        coord_errors = _validate_point_coordinates(coords, feature_index)
        errors.extend(coord_errors)
    elif geom_type == 'LineString':
        if not isinstance(coords, list) or len(coords) < 2:
            errors.append(f"{prefix}: LineString must have at least 2 positions")
        else:
            for i, pos in enumerate(coords):
                pos_errors = _validate_position(pos, feature_index, i)
                errors.extend(pos_errors)
    elif geom_type == 'Polygon':
        if not isinstance(coords, list) or len(coords) == 0:
            errors.append(f"{prefix}: Polygon must have at least 1 ring")
        else:
            for ring_i, ring in enumerate(coords):
                if not isinstance(ring, list) or len(ring) < 4:
                    errors.append(f"{prefix}: Ring {ring_i} must have at least 4 positions")
                else:
                    for pos_i, pos in enumerate(ring):
                        pos_errors = _validate_position(pos, feature_index, pos_i)
                        errors.extend(pos_errors)
    
    return errors


def _validate_point_coordinates(coords: List, feature_index: int) -> List[str]:
    """Validate Point coordinates [lon, lat]"""
    return _validate_position(coords, feature_index, 0)


def _validate_position(position: List, feature_index: int, pos_index: int) -> List[str]:
    """
    Validate a position [lon, lat].
    
    Args:
        position: Position array [lon, lat]
        feature_index: Feature index
        pos_index: Position index within feature
    
    Returns:
        List of error messages
    """
    errors = []
    prefix = f"Feature {feature_index} position {pos_index}"
    
    if not isinstance(position, (list, tuple)):
        errors.append(f"{prefix}: Position must be an array")
        return errors
    
    if len(position) < 2:
        errors.append(f"{prefix}: Position must have at least 2 elements [lon, lat]")
        return errors
    
    lon, lat = position[0], position[1]
    
    # Check for numeric values
    if not isinstance(lon, (int, float)) or np.isnan(lon) or np.isinf(lon):
        errors.append(f"{prefix}: Invalid longitude value: {lon}")
    elif not (VALID_LON_RANGE[0] <= lon <= VALID_LON_RANGE[1]):
        errors.append(f"{prefix}: Longitude {lon} out of range [-180, 180]")
    
    if not isinstance(lat, (int, float)) or np.isnan(lat) or np.isinf(lat):
        errors.append(f"{prefix}: Invalid latitude value: {lat}")
    elif not (VALID_LAT_RANGE[0] <= lat <= VALID_LAT_RANGE[1]):
        errors.append(f"{prefix}: Latitude {lat} out of range [-90, 90]")
    
    return errors


def sanitize_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitize coordinates by removing invalid rows.
    
    Args:
        df: DataFrame with 'lat' and 'lon' columns
    
    Returns:
        DataFrame with only valid coordinates
    """
    initial_count = len(df)
    
    # Check for required columns
    if 'lat' not in df.columns or 'lon' not in df.columns:
        logger.error("Missing lat/lon columns for sanitization")
        return df
    
    # Remove NaN/None values
    df = df.dropna(subset=['lat', 'lon'])
    
    # Remove infinite values
    df = df[np.isfinite(df['lat']) & np.isfinite(df['lon'])]
    
    # Clip coordinates to valid ranges (with warning)
    lat_out_of_range = ((df['lat'] < VALID_LAT_RANGE[0]) | (df['lat'] > VALID_LAT_RANGE[1]))
    lon_out_of_range = ((df['lon'] < VALID_LON_RANGE[0]) | (df['lon'] > VALID_LON_RANGE[1]))
    
    if lat_out_of_range.any():
        logger.warning(f"Found {lat_out_of_range.sum()} rows with latitude out of range - dropping")
        df = df[~lat_out_of_range]
    
    if lon_out_of_range.any():
        logger.warning(f"Found {lon_out_of_range.sum()} rows with longitude out of range - dropping")
        df = df[~lon_out_of_range]
    
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.info(f"Sanitized coordinates: dropped {dropped_count} invalid rows")
    
    return df


def create_valid_geojson(df_canonical: pd.DataFrame) -> bytes:
    """
    Create valid GeoJSON FeatureCollection from canonical dataframe.
    
    Args:
        df_canonical: DataFrame with canonical schema (id, lat, lon, etc.)
    
    Returns:
        GeoJSON as UTF-8 encoded bytes
    
    Raises:
        ValueError: If dataframe doesn't have required columns
    """
    # Validate input
    if 'lat' not in df_canonical.columns or 'lon' not in df_canonical.columns:
        raise ValueError("DataFrame must have 'lat' and 'lon' columns")
    
    # Sanitize coordinates
    df_clean = sanitize_coordinates(df_canonical.copy())
    
    if len(df_clean) == 0:
        logger.warning("No valid features after sanitization - creating empty FeatureCollection")
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        return json.dumps(geojson, ensure_ascii=False, indent=2).encode('utf-8')
    
    # Build features
    features = []
    
    for idx, row in df_clean.iterrows():
        try:
            # Create geometry (GeoJSON uses [lon, lat] order)
            geometry = {
                "type": "Point",
                "coordinates": [float(row['lon']), float(row['lat'])]
            }
            
            # Create properties (exclude lat/lon/geometry from properties)
            properties = {}
            for col in df_clean.columns:
                if col not in ['lat', 'lon', 'geometry']:
                    value = row[col]
                    
                    # Convert to JSON-serializable type
                    if pd.isna(value):
                        properties[col] = None
                    elif isinstance(value, (np.integer, np.floating)):
                        properties[col] = float(value)
                    elif isinstance(value, (int, float, str, bool)):
                        properties[col] = value
                    else:
                        properties[col] = str(value)
            
            # Create feature
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties
            }
            
            features.append(feature)
        
        except Exception as e:
            logger.warning(f"Failed to create feature for row {idx}: {e}")
            continue
    
    # Create FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "crs": {
            "type": "name",
            "properties": {
                "name": "EPSG:4326"
            }
        }
    }
    
    # Validate before returning
    is_valid, errors = validate_geojson_structure(geojson)
    if not is_valid:
        logger.error(f"Generated GeoJSON is invalid: {errors}")
        # Still return it, but log the issues
    
    # Convert to bytes
    json_str = json.dumps(geojson, ensure_ascii=False, indent=2)
    return json_str.encode('utf-8')


def quick_geojson_test(geojson_bytes: bytes) -> bool:
    """
    Quick test if GeoJSON is valid.
    
    Args:
        geojson_bytes: GeoJSON as bytes
    
    Returns:
        True if valid, False otherwise
    """
    try:
        # Try to parse JSON
        geojson_dict = json.loads(geojson_bytes.decode('utf-8'))
        
        # Validate structure
        is_valid, errors = validate_geojson_structure(geojson_dict)
        
        if not is_valid:
            logger.error(f"GeoJSON validation failed: {errors[:3]}...")  # Show first 3 errors
        
        return is_valid
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"GeoJSON test failed: {e}")
        return False


def get_geojson_statistics(geojson_bytes: bytes) -> Dict[str, Any]:
    """
    Get statistics about a GeoJSON file.
    
    Args:
        geojson_bytes: GeoJSON as bytes
    
    Returns:
        Dictionary with statistics
    """
    stats = {
        'size_bytes': len(geojson_bytes),
        'size_kb': round(len(geojson_bytes) / 1024, 2),
        'feature_count': 0,
        'valid': False,
        'errors': []
    }
    
    try:
        geojson_dict = json.loads(geojson_bytes.decode('utf-8'))
        
        # Get feature count
        if 'features' in geojson_dict:
            stats['feature_count'] = len(geojson_dict['features'])
        
        # Validate
        is_valid, errors = validate_geojson_structure(geojson_dict)
        stats['valid'] = is_valid
        stats['errors'] = errors
    
    except Exception as e:
        stats['errors'] = [str(e)]
    
    return stats
