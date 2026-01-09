"""
PROMPT 3 Test: Real Sentinel Hub Band Download + NDVI/NDWI Computation
Tests actual imagery download (requires credentials).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers import SentinelHubProvider
from src.config import load_config
from datetime import datetime, timedelta
import logging
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_provider_init():
    """Test 1: Provider initialization."""
    print("\n[Test 1] SentinelHubProvider initialization...")
    
    config = load_config()
    provider = SentinelHubProvider(config, logger)
    
    if provider.available:
        print("   ✓ Provider initialized and available")
        return True, provider
    else:
        print("   ✗ Provider not available (credentials missing?)")
        return False, None


def test_scene_search(provider):
    """Test 2: Scene search."""
    print("\n[Test 2] Scene search...")
    
    if not provider:
        print("   ⊘ Skipped (provider not available)")
        return False
    
    # Jerusalem area
    bbox = (35.20, 31.94, 35.26, 32.00)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    scenes = provider.search_scenes(bbox, start_date, end_date, max_cloud_cover=20.0)
    
    if len(scenes) > 0:
        print(f"   ✓ Found {len(scenes)} scenes")
        print(f"   First scene: {scenes[0]['id']}, cloud: {scenes[0]['cloud_cover']:.1f}%")
        return True
    else:
        print("   ✗ No scenes found")
        return False


def test_band_download(provider):
    """Test 3: Band download (small area)."""
    print("\n[Test 3] Band download (may take 30-60 seconds)...")
    
    if not provider:
        print("   ⊘ Skipped (provider not available)")
        return False
    
    # Very small bbox for quick test
    bbox = (35.230, 31.950, 35.236, 31.956)  # ~500m x 500m
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    try:
        result = provider.fetch_band_stack(
            bbox=bbox,
            time_range=(start_date, end_date),
            bands=['B04', 'B08'],  # Red, NIR
            resolution=20,  # 20m for faster download
            max_cloud_cover=20.0
        )
        
        if result.status == 'SUCCESS':
            print(f"   ✓ Downloaded successfully")
            print(f"   Scenes processed: {result.scenes_processed}")
            print(f"   Bands: {list(result.bands.keys())}")
            
            # Check data shape
            for band_name, band_data in result.bands.items():
                shape = band_data.data.shape
                print(f"   {band_name} shape: {shape}")
            
            return True, result
        else:
            print(f"   ✗ Download failed: {result.failure_reason}")
            return False, None
            
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return False, None


def test_ndvi_computation(provider, imagery_result):
    """Test 4: NDVI computation from real data."""
    print("\n[Test 4] NDVI computation...")
    
    if not provider or not imagery_result:
        print("   ⊘ Skipped (no imagery data)")
        return False
    
    try:
        red_band = imagery_result.bands.get('B04')
        nir_band = imagery_result.bands.get('B08')
        
        if not red_band or not nir_band:
            print("   ✗ Required bands not available")
            return False
        
        ndvi = provider.compute_ndvi(red_band, nir_band)
        
        if ndvi.computed_from_real_data:
            print(f"   ✓ NDVI computed successfully")
            print(f"   Formula: {ndvi.formula}")
            print(f"   Shape: {ndvi.data.shape}")
            print(f"   Overall mean: {ndvi.stats['overall']['mean']:.3f}")
            print(f"   Overall std: {ndvi.stats['overall']['std']:.3f}")
            print(f"   Range: [{ndvi.stats['overall']['min']:.3f}, {ndvi.stats['overall']['max']:.3f}]")
            return True
        else:
            print("   ✗ NDVI not marked as real data")
            return False
            
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return False


def test_ndvi_values_reasonable(provider, imagery_result):
    """Test 5: NDVI values are in reasonable range."""
    print("\n[Test 5] NDVI value validation...")
    
    if not provider or not imagery_result:
        print("   ⊘ Skipped (no imagery data)")
        return False
    
    try:
        red_band = imagery_result.bands.get('B04')
        nir_band = imagery_result.bands.get('B08')
        
        ndvi = provider.compute_ndvi(red_band, nir_band)
        
        # NDVI should be in [-1, 1]
        data_min = ndvi.stats['overall']['min']
        data_max = ndvi.stats['overall']['max']
        
        if data_min >= -1 and data_max <= 1:
            print(f"   ✓ NDVI values in valid range [-1, 1]")
            print(f"   Actual range: [{data_min:.3f}, {data_max:.3f}]")
            return True
        else:
            print(f"   ✗ NDVI values out of range: [{data_min:.3f}, {data_max:.3f}]")
            return False
            
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("PROMPT 3: Sentinel Hub Real Data Download Tests")
    print("="*60)
    print("\n⚠️  WARNING: These tests require:")
    print("  1. Valid Sentinel Hub OAuth credentials")
    print("  2. Internet connection")
    print("  3. May take 1-2 minutes to complete")
    print("="*60)
    
    # Test 1: Init
    success, provider = test_provider_init()
    results = [success]
    
    if not provider:
        print("\n" + "="*60)
        print("SKIPPED: Provider not available (credentials not configured)")
        print("Add credentials to .streamlit/secrets.toml or environment")
        print("="*60)
        sys.exit(1)
    
    # Test 2: Search
    success = test_scene_search(provider)
    results.append(success)
    
    # Test 3: Download
    success, imagery_result = test_band_download(provider)
    results.append(success)
    
    # Test 4: NDVI
    success = test_ndvi_computation(provider, imagery_result)
    results.append(success)
    
    # Test 5: NDVI validation
    success = test_ndvi_values_reasonable(provider, imagery_result)
    results.append(success)
    
    # Summary
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL TESTS PASSED - PROMPT 3 COMPLETE")
        print("\nReal Sentinel Hub data download is working!")
    else:
        print("✗ SOME TESTS FAILED - Review above")
    print("="*60)
    
    sys.exit(0 if passed == total else 1)
