"""
PROMPT 1 Test: Pipeline API Validation
Tests that PipelineService and PipelineRequest follow unified API contract.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.pipeline_service import PipelineService, PipelineRequest
from src.config import load_config
from shapely.geometry import Point
import logging

def test_pipeline_service_init():
    """Test 1: PipelineService requires config."""
    print("\n[Test 1] PipelineService initialization with config...")
    
    config = load_config()
    logger = logging.getLogger('test')
    
    try:
        pipeline = PipelineService(config, logger)
        print("   ✓ PipelineService initialized successfully")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


def test_pipeline_request_no_center_coords():
    """Test 2: PipelineRequest should NOT accept center_lat/center_lon."""
    print("\n[Test 2] PipelineRequest rejects center_lat/center_lon...")
    
    try:
        # This should FAIL (no center_lat parameter exists)
        request = PipelineRequest(
            center_lat=31.95,
            center_lon=35.23,
            start_date='2025-01-01',
            end_date='2025-12-31'
        )
        print("   ✗ FAILED: PipelineRequest accepted center_lat/lon (should reject)")
        return False
    except TypeError as e:
        if 'center_lat' in str(e) or 'center_lon' in str(e):
            print(f"   ✓ Correctly rejected: {e}")
            return True
        else:
            print(f"   ? Unexpected error: {e}")
            return False


def test_pipeline_request_with_geometry():
    """Test 3: PipelineRequest accepts aoi_geometry."""
    print("\n[Test 3] PipelineRequest accepts aoi_geometry...")
    
    try:
        point = Point(35.23, 31.95)  # (lon, lat)
        request = PipelineRequest(
            aoi_geometry=point,
            start_date='2025-01-01',
            end_date='2025-12-31',
            mode='demo'
        )
        print("   ✓ PipelineRequest created successfully with aoi_geometry")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


def test_mode_real_converts_to_live():
    """Test 4: mode='real' should auto-convert to 'live'."""
    print("\n[Test 4] mode='real' converts to 'live'...")
    
    try:
        point = Point(35.23, 31.95)
        request = PipelineRequest(
            aoi_geometry=point,
            start_date='2025-01-01',
            end_date='2025-12-31',
            mode='real'  # Should convert to 'live'
        )
        
        if request.mode == 'live':
            print("   ✓ mode='real' correctly converted to 'live'")
            return True
        else:
            print(f"   ✗ mode did not convert: got '{request.mode}'")
            return False
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


def test_mode_invalid_rejected():
    """Test 5: Invalid mode should raise error."""
    print("\n[Test 5] Invalid mode rejected...")
    
    try:
        point = Point(35.23, 31.95)
        request = PipelineRequest(
            aoi_geometry=point,
            start_date='2025-01-01',
            end_date='2025-12-31',
            mode='production'  # Invalid
        )
        print(f"   ✗ Invalid mode accepted: {request.mode}")
        return False
    except ValueError as e:
        if 'Invalid mode' in str(e):
            print(f"   ✓ Correctly rejected: {e}")
            return True
        else:
            print(f"   ? Unexpected error: {e}")
            return False


def test_aoi_geometry_required():
    """Test 6: aoi_geometry cannot be None."""
    print("\n[Test 6] aoi_geometry=None rejected...")
    
    try:
        request = PipelineRequest(
            aoi_geometry=None,
            start_date='2025-01-01',
            end_date='2025-12-31'
        )
        print("   ✗ aoi_geometry=None was accepted (should reject)")
        return False
    except ValueError as e:
        if 'aoi_geometry' in str(e):
            print(f"   ✓ Correctly rejected: {e}")
            return True
        else:
            print(f"   ? Unexpected error: {e}")
            return False


if __name__ == "__main__":
    print("="*60)
    print("PROMPT 1: Pipeline API Validation Tests")
    print("="*60)
    
    tests = [
        test_pipeline_service_init,
        test_pipeline_request_no_center_coords,
        test_pipeline_request_with_geometry,
        test_mode_real_converts_to_live,
        test_mode_invalid_rejected,
        test_aoi_geometry_required
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n   ✗ Unexpected test error: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL TESTS PASSED - PROMPT 1 COMPLETE")
    else:
        print("✗ SOME TESTS FAILED - Review above")
    print("="*60)
    
    sys.exit(0 if passed == total else 1)
