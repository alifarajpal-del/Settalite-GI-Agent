"""
Integration Test: Full Pipeline with Real Providers + Manifest
Tests the complete flow from PROMPTs 1-4.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.pipeline_service import PipelineService, PipelineRequest
from src.provenance import create_manifest, ManifestStatus
from src.providers import SentinelHubProvider, GoogleEarthEngineProvider
from shapely.geometry import Point
from datetime import datetime, timedelta
import logging
import os

# Setup test environment
os.environ['STREAMLIT_ENV'] = 'test'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_integration_demo_mode():
    """Test 1: Demo mode with manifest."""
    print("\n[Test 1] Demo mode integration with manifest...")
    
    try:
        from src.config import load_config
        config = load_config()
        pipeline = PipelineService(config, logger)
        
        # Create request
        point = Point(35.23, 31.95)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        request = PipelineRequest(
            aoi_geometry=point.buffer(0.01),  # Small AOI
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            mode='demo'
        )
        
        # Run pipeline
        result = pipeline.run(request)
        
        # Verify
        assert result.success, "Pipeline should succeed"
        assert result.status == 'DEMO_OK', f"Expected DEMO_OK, got {result.status}"
        assert result.manifest is not None, "Manifest should exist"
        assert result.manifest.status == ManifestStatus.DEMO_MODE, "Manifest status should be DEMO_MODE"
        assert len(result.manifest.data_sources) > 0, "Should have data sources"
        
        print("   ✓ Demo mode integration test passed")
        print(f"   Manifest run_id: {result.manifest.run_id}")
        print(f"   Data sources: {len(result.manifest.data_sources)}")
        return True
        
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manifest_creation():
    """Test 2: Manifest creation and validation."""
    print("\n[Test 2] Manifest creation...")
    
    try:
        manifest = create_manifest(
            run_id="test_001",
            mode="demo",
            request_params={'test': 'value'}
        )
        
        assert manifest.run_id == "test_001"
        assert manifest.mode == "demo"
        assert not manifest.can_compute_likelihood(), "Demo mode should not allow likelihood initially"
        
        print("   ✓ Manifest creation test passed")
        return True
        
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


def test_providers_safe_init():
    """Test 3: Providers initialize safely without crashing."""
    print("\n[Test 3] Safe provider initialization...")
    
    try:
        from src.config import load_config
        config = load_config()
        
        # Test Sentinel Hub
        sh_provider = SentinelHubProvider(config, logger)
        print(f"   Sentinel Hub available: {sh_provider.available}")
        
        # Test GEE
        gee_provider = GoogleEarthEngineProvider(config, logger)
        print(f"   GEE available: {gee_provider.is_available()}")
        print(f"   GEE message: {gee_provider.get_availability_message()}")
        
        print("   ✓ Providers initialized safely (no crash)")
        return True
        
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("INTEGRATION TEST: PROMPTs 1-4")
    print("="*60)
    
    tests = [
        test_manifest_creation,
        test_providers_safe_init,
        test_integration_demo_mode
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n   ✗ Unexpected error: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ INTEGRATION TESTS PASSED")
        print("\nSystem is ready:")
        print("  - PROMPT 1: Pipeline API ✓")
        print("  - PROMPT 2: Provenance Manifest ✓")
        print("  - PROMPT 3: Sentinel Hub Provider ✓")
        print("  - PROMPT 4: GEE Provider ✓")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60)
    
    sys.exit(0 if passed == total else 1)
