"""
Integration test for SentinelHub live fetch (search + band download).
Skipped if credentials are missing.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_sentinelhub_search_and_download():
    """
    Integration test: search scenes and download bands for a known AOI.
    Location: lat=31.68797, lon=35.16805 (Jerusalem area)
    """
    from src.providers.sentinelhub_provider import SentinelHubProvider
    from src.config import load_config
    import logging
    
    # Check credentials
    if not os.getenv('SENTINELHUB_CLIENT_ID') and not os.getenv('SENTINELHUB_CLIENT_SECRET'):
        print("SKIP: SentinelHub credentials not available")
        return
    
    # Setup
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_live_fetch")
    
    config = load_config()
    provider = SentinelHubProvider(config, logger)
    
    if not provider.available:
        print(f"SKIP: SentinelHub not available: {provider._unavailable_reason}")
        return
    
    # Test parameters
    center_lat = 31.68797
    center_lon = 35.16805
    radius_deg = 2000 / 111000  # ~2000m to degrees
    
    bbox = (
        center_lon - radius_deg,
        center_lat - radius_deg,
        center_lon + radius_deg,
        center_lat + radius_deg
    )
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=36*30)  # 36 months
    max_cloud_cover = 80
    
    print(f"\n{'='*70}")
    print(f"TEST: SentinelHub Live Search & Download")
    print(f"{'='*70}")
    print(f"Location: ({center_lat}, {center_lon})")
    print(f"BBox: {bbox}")
    print(f"Time range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Max cloud cover: {max_cloud_cover}%")
    
    # STEP 1: Search scenes
    print(f"\n--- STEP 1: Search Scenes ---")
    scenes, error = provider.search_scenes(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover
    )
    
    if error:
        raise AssertionError(f"Scene search failed: {error}")
    
    assert isinstance(scenes, list), f"Expected list, got {type(scenes).__name__}"
    assert len(scenes) > 0, "No scenes found - increase time range or cloud cover"
    
    print(f"✓ Found {len(scenes)} scenes")
    print(f"  First scene:")
    print(f"    - ID: {scenes[0]['id']}")
    print(f"    - Datetime: {scenes[0]['datetime']}")
    print(f"    - Cloud cover: {scenes[0]['cloud_cover']:.1f}%")
    
    # STEP 2: Download bands
    print(f"\n--- STEP 2: Download Bands ---")
    bands_to_fetch = ['B02', 'B03', 'B04']  # Blue, Green, Red
    
    result = provider.fetch_band_stack(
        bbox=bbox,
        time_range=(start_date, end_date),
        bands=bands_to_fetch,
        resolution=60,  # Lower resolution for faster test
        max_cloud_cover=max_cloud_cover
    )
    
    assert result.status == 'SUCCESS', f"Band download failed: {result.failure_reason}"
    assert isinstance(result.bands, dict), f"Expected bands dict, got {type(result.bands).__name__}"
    assert len(result.bands) > 0, "No bands returned"
    
    print(f"✓ Downloaded {len(result.bands)} bands")
    print(f"  Scenes processed: {result.scenes_processed}")
    
    for band_name in bands_to_fetch:
        assert band_name in result.bands, f"Band {band_name} missing"
        band_data = result.bands[band_name]
        assert band_data.data.shape[0] > 0, f"Band {band_name} has zero timesteps"
        assert band_data.data.shape[1] > 0, f"Band {band_name} has zero height"
        assert band_data.data.shape[2] > 0, f"Band {band_name} has zero width"
        print(f"  {band_name}: shape={band_data.data.shape}, timestamps={len(band_data.timestamps)}")
    
    print(f"\n{'='*70}")
    print(f"✓ Integration test PASSED")
    print(f"{'='*70}")


if __name__ == "__main__":
    # Run test directly
    test_sentinelhub_search_and_download()
