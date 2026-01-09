"""
Coordinate Parser for Heritage Sentinel Pro
Supports multiple formats: Decimal, DMS, Google Maps/Earth URLs
"""
import re
from typing import Tuple
from urllib.parse import urlparse, parse_qs


def parse_coords(text: str) -> Tuple[float, float]:
    """
    Parse coordinates from various formats.
    
    Supported formats:
    1. Decimal: "31.9522, 35.2332" or "31.9522 35.2332"
    2. DMS: "31°57'08\"N 35°14'00\"E" or "31 57 08 N, 35 14 00 E"
    3. URLs: Google Maps/Earth URLs with @lat,lon or ?q=lat,lon or ?ll=lat,lon
    
    Args:
        text: Input text containing coordinates
        
    Returns:
        Tuple of (latitude, longitude) as floats
        
    Raises:
        ValueError: If coordinates cannot be parsed or are invalid
    """
    if not text or not isinstance(text, str):
        raise ValueError("Input must be a non-empty string")
    
    text = text.strip()
    
    # Try URL parsing first
    if 'maps' in text.lower() or 'earth' in text.lower() or text.startswith('http'):
        try:
            coords = _parse_url(text)
            if coords:
                return normalize_latlon(*coords)
        except Exception:
            pass  # Fall through to other parsers
    
    # Try DMS format
    try:
        coords = _parse_dms(text)
        if coords:
            return normalize_latlon(*coords)
    except Exception:
        pass
    
    # Try decimal format
    try:
        coords = _parse_decimal(text)
        if coords:
            return normalize_latlon(*coords)
    except Exception:
        pass
    
    # If all parsers fail, provide helpful error
    raise ValueError(
        "Could not parse coordinates. Please use one of these formats:\n"
        "• Decimal: 31.9522, 35.2332\n"
        "• DMS: 31°57'08\"N 35°14'00\"E\n"
        "• Google Maps URL: https://www.google.com/maps/@31.9522,35.2332,15z\n"
        "\nExamples:\n"
        "31.9522, 35.2332\n"
        "31°57'08\"N 35°14'00\"E\n"
        "https://maps.google.com/?q=31.9522,35.2332"
    )


def normalize_latlon(lat: float, lon: float) -> Tuple[float, float]:
    """
    Validate and normalize latitude/longitude.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        
    Returns:
        Tuple of (lat, lon) rounded to 6 decimal places
        
    Raises:
        ValueError: If coordinates are out of bounds
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid numeric coordinates: lat={lat}, lon={lon}")
    
    if not -90 <= lat <= 90:
        raise ValueError(f"Latitude {lat} is out of bounds (-90 to 90)")
    
    if not -180 <= lon <= 180:
        raise ValueError(f"Longitude {lon} is out of bounds (-180 to 180)")
    
    # Round to 6 decimal places (~0.11m precision)
    return round(lat, 6), round(lon, 6)


def _parse_decimal(text: str) -> Tuple[float, float]:
    """Parse decimal degree coordinates."""
    # Remove common noise
    text = re.sub(r'[^\d\.\-,\s°]', ' ', text)
    
    # Find all decimal numbers (positive or negative)
    numbers = re.findall(r'-?\d+\.?\d*', text)
    
    if len(numbers) < 2:
        raise ValueError("Not enough numbers found for lat/lon pair")
    
    # Try first two numbers as lat, lon
    lat = float(numbers[0])
    lon = float(numbers[1])
    
    # Basic sanity check: lat should be smaller absolute value for most cases
    # But we'll validate properly in normalize_latlon
    return lat, lon


def _parse_dms(text: str) -> Tuple[float, float]:
    """Parse Degree-Minute-Second coordinates."""
    # Pattern for DMS: 31°57'08"N or 31 57 08 N or 31°57'08.5"N
    dms_pattern = r'(\d+)[°\s]+(\d+)[\'′\s]+(\d+(?:\.\d+)?)[\"″\s]*([NSEW])?'
    
    matches = re.findall(dms_pattern, text, re.IGNORECASE)
    
    if len(matches) < 2:
        raise ValueError("Could not parse DMS coordinates")
    
    # First match should be latitude
    lat_deg, lat_min, lat_sec, lat_dir = matches[0]
    lat = float(lat_deg) + float(lat_min)/60 + float(lat_sec)/3600
    if lat_dir and lat_dir.upper() == 'S':
        lat = -lat
    
    # Second match should be longitude
    lon_deg, lon_min, lon_sec, lon_dir = matches[1]
    lon = float(lon_deg) + float(lon_min)/60 + float(lon_sec)/3600
    if lon_dir and lon_dir.upper() == 'W':
        lon = -lon
    
    return lat, lon


def _parse_url(text: str) -> Tuple[float, float]:
    """Parse coordinates from Google Maps/Earth URLs."""
    # Handle common URL patterns
    
    # Pattern 1: @lat,lon,zoom (Google Maps)
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', text)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    # Pattern 2: ?q=lat,lon or &q=lat,lon (query parameter)
    parsed = urlparse(text)
    query_params = parse_qs(parsed.query)
    
    if 'q' in query_params:
        q = query_params['q'][0]
        # Try to extract lat,lon from query
        coords = re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', q)
        if coords:
            return float(coords.group(1)), float(coords.group(2))
    
    # Pattern 3: ll=lat,lon (lat/lon parameter)
    if 'll' in query_params:
        ll = query_params['ll'][0]
        parts = ll.split(',')
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
    
    # Pattern 4: Direct in path like /place/lat,lon
    path_coords = re.search(r'/(-?\d+\.\d+),(-?\d+\.\d+)', parsed.path)
    if path_coords:
        return float(path_coords.group(1)), float(path_coords.group(2))
    
    raise ValueError("Could not extract coordinates from URL")


# Convenience function for validation
def is_valid_coords(lat: float, lon: float) -> bool:
    """Check if coordinates are valid without raising exception."""
    try:
        normalize_latlon(lat, lon)
        return True
    except ValueError:
        return False
