"""
Test STAC Provider with live Sentinel-2 data.
Tests search_scenes and fetch_band_stack methods.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers.stac_provider import StacProvider
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_stac_provider():
    """Test STAC provider with Petra region."""
    
    print("=" * 70)
    print("🧪 Testing STAC Provider - Live Sentinel-2 Data")
    print("=" * 70)
    
    # Initialize provider
    print("\n📦 Initializing STAC Provider...")
    provider = StacProvider(logger=logger)
    
    if not provider.available:
        print(f"❌ STAC Provider not available: {provider._unavailable_reason}")
        return False
    
    print("✅ STAC Provider initialized successfully")
    print(f"   Catalog: {provider.EARTH_SEARCH_STAC_URL}")
    print(f"   Collection: {provider.COLLECTION}")
    
    # Test area: Petra, Jordan (31.68797, 35.16805) with 2000m radius
    # ~2km = ~0.018 degrees
    center_lat = 35.16805
    center_lon = 31.68797
    radius_deg = 0.018
    
    bbox = (
        center_lon - radius_deg,  # min_lon
        center_lat - radius_deg,  # min_lat
        center_lon + radius_deg,  # max_lon
        center_lat + radius_deg   # max_lat
    )
    
    # Last 36 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 3)
    
    print(f"\n📍 Test Location: Petra, Jordan")
    print(f"   Center: ({center_lon:.5f}, {center_lat:.5f})")
    print(f"   BBox: {bbox}")
    print(f"   Radius: ~2km")
    print(f"   Time Range: {start_date.date()} to {end_date.date()}")
    
    # Test 1: Search scenes
    print("\n" + "=" * 70)
    print("TEST 1: Search Scenes")
    print("=" * 70)
    
    try:
        scenes = provider.search_scenes(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=30.0,
            max_results=50
        )
        
        print(f"\n✅ Search successful!")
        print(f"   Scenes found: {len(scenes)}")
        
        if len(scenes) == 0:
            print("❌ FAIL: Expected at least 1 scene")
            return False
        
        # Show first 3 scenes
        print(f"\n📊 First {min(3, len(scenes))} scenes:")
        for i, scene in enumerate(scenes[:3]):
            print(f"\n   Scene {i + 1}:")
            print(f"      ID: {scene['id']}")
            print(f"      Date: {scene['datetime'].date()}")
            print(f"      Cloud: {scene['cloud_cover']:.1f}%")
            print(f"      Coverage: {scene.get('data_coverage', 'N/A')}")
            print(f"      Assets: {len(scene.get('assets', {}))}")
            
            # Show band assets (first scene only)
            if i == 0:
                band_assets = [k for k in scene.get('assets', {}).keys() if k.startswith('B') or k.startswith('b')]
                print(f"      Band assets: {', '.join(sorted(band_assets)[:10])}")
        
        print("\n✅ TEST 1 PASSED: Scenes found and parsed correctly")
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Fetch band stack
    print("\n" + "=" * 70)
    print("TEST 2: Fetch Band Stack")
    print("=" * 70)
    
    try:
        result = provider.fetch_band_stack(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            bands=["B02", "B03", "B04", "B08"],
            max_cloud_cover=30.0,
            max_scenes=2,
            target_resolution=100
        )
        
        print(f"\n📊 Result Status: {result.status}")
        print(f"   Provider: {result.provider_name}")
        print(f"   Scenes Found: {result.scenes_count}")
        print(f"   Scenes Processed: {result.scenes_processed}")
        
        if result.status == 'FAILED':
            print(f"❌ Band fetch failed: {result.failure_reason}")
            return False
        
        if result.status != 'SUCCESS':
            print(f"⚠️ Unexpected status: {result.status}")
            return False
        
        print(f"\n✅ Download successful!")
        print(f"\n📦 Bands downloaded:")
        for band_name, band_data in result.bands.items():
            print(f"   {band_name}:")
            print(f"      Shape: {band_data.data.shape}")
            print(f"      Dtype: {band_data.data.dtype}")
            print(f"      Resolution: {band_data.resolution}")
            print(f"      Timestamps: {len(band_data.timestamps)}")
            print(f"      Value range: [{band_data.data.min():.0f}, {band_data.data.max():.0f}]")
        
        if len(result.bands) == 0:
            print("❌ FAIL: Expected at least 1 band")
            return False
        
        # Check if bands have data
        for band_name, band_data in result.bands.items():
            if band_data.data.size == 0:
                print(f"❌ FAIL: Band {band_name} has no data")
                return False
        
        print(f"\n📊 Indices computed:")
        for index_name, index_ts in result.indices.items():
            print(f"   {index_name}:")
            print(f"      Formula: {index_ts.formula}")
            print(f"      Shape: {index_ts.data.shape}")
            print(f"      Value range: [{index_ts.data.min():.3f}, {index_ts.data.max():.3f}]")
        
        print("\n✅ TEST 2 PASSED: Bands downloaded and indices computed")
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 STAC Provider Live Test Suite")
    print("=" * 70)
    
    success = test_stac_provider()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ TESTS FAILED")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
