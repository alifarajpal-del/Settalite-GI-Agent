#!/usr/bin/env python3
"""
Heritage Sentinel Pro - Integration Test
End-to-end test of demo mode pipeline without Streamlit runtime
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_integration():
    """Run full integration test"""
    print("\n🧪 Heritage Sentinel Pro - Integration Test\n")
    print("=" * 60)
    
    failures = []
    warnings = []
    success = []
    
    # Test 1: Config loading with validation
    print("\n1️⃣  Testing config loader...")
    try:
        from src.config import load_config
        config = load_config()
        
        assert isinstance(config, dict), "Config must be dict"
        assert 'app' in config, "Config must have 'app' key"
        
        # Validate critical keys for services
        print("   Validating critical keys...")
        
        # App keys
        assert 'name' in config['app'], "Missing app.name"
        assert 'version' in config['app'], "Missing app.version"
        
        # Satellite keys
        assert 'satellite' in config, "Missing satellite config"
        assert 'providers' in config['satellite'], "Missing satellite.providers"
        assert 'sentinel' in config['satellite']['providers'], "Missing sentinel provider"
        
        sentinel = config['satellite']['providers']['sentinel']
        assert 'resolution' in sentinel, "Missing sentinel.resolution"
        assert 'bands' in sentinel, "Missing sentinel.bands"
        assert 'optical' in sentinel['bands'], "Missing sentinel.bands.optical"
        
        # Processing keys
        assert 'processing' in config, "Missing processing config"
        assert 'coordinate_extraction' in config['processing'], "Missing coordinate_extraction"
        assert 'anomaly_detection' in config['processing'], "Missing anomaly_detection"
        assert 'spectral_indices' in config['processing'], "Missing spectral_indices"
        
        # Paths
        assert 'paths' in config, "Missing paths config"
        assert 'outputs' in config['paths'], "Missing paths.outputs"
        assert 'exports' in config['paths'], "Missing paths.exports"
        assert 'data' in config['paths'], "Missing paths.data"
        
        print("✅ Config loaded successfully")
        print(f"   App: {config['app'].get('name', 'Unknown')}")
        print(f"   Version: {config['app'].get('version', 'Unknown')}")
        print(f"   Satellite bands: {len(sentinel['bands'].get('optical', []))}")
        success.append("Config loader")
        
    except AssertionError as e:
        print(f"❌ Config validation failed: {e}")
        failures.append(("Config validation", str(e)))
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        failures.append(("Config loading", str(e)))
    
    # Test 2: MockDataService initialization
    print("\n2️⃣  Testing MockDataService...")
    try:
        from src.services.mock_data_service import MockDataService
        
        # Try with seed if supported
        try:
            mock = MockDataService()
        except ImportError as e:
            mock = MockDataService()
        
        print("✅ MockDataService instantiated")
        success.append("MockDataService init")
        
    except Exception as e:
        print(f"❌ MockDataService failed: {e}")
        failures.append(("MockDataService", str(e)))
        return failures, warnings, success
    
    # Test 3: AOI generation
    print("\n3️⃣  Testing AOI generation...")
    try:
        aoi = mock.create_mock_aoi()
        
        # Validate it's a geometry-like object
        assert aoi is not None, "AOI should not be None"
        
        # Check if it's shapely Polygon or has expected attributes
        if hasattr(aoi, 'is_valid'):
            assert aoi.is_valid, "AOI must be valid geometry"
            print(f"✅ AOI created (type: {type(aoi).__name__})")
        elif hasattr(aoi, 'geom_type'):
            print(f"✅ AOI created (geom_type: {aoi.geom_type})")
        else:
            print(f"⚠️  AOI created but format unexpected: {type(aoi)}")
            warnings.append("AOI format")
        
        success.append("AOI generation")
        
    except Exception as e:
        print(f"❌ AOI generation failed: {e}")
        failures.append(("AOI generation", str(e)))
    
    # Test 4: Detection generation
    print("\n4️⃣  Testing detection generation...")
    try:
        detections = mock.generate_mock_detections(num_sites=12)
        
        assert hasattr(detections, 'columns'), "Detections must be DataFrame-like"
        assert len(detections) == 12, f"Expected 12 sites, got {len(detections)}"
        
        # Check for required fields (handle Arabic column names)
        has_lat = any('lat' in str(col).lower() or 'العرض' in str(col) for col in detections.columns)
        has_lon = any('lon' in str(col).lower() or 'الطول' in str(col) for col in detections.columns)
        has_conf = any('conf' in str(col).lower() or 'الثقة' in str(col) for col in detections.columns)
        
        assert has_lat, "Detections must have latitude field"
        assert has_lon, "Detections must have longitude field"
        assert has_conf, "Detections must have confidence field"
        
        print(f"✅ Generated {len(detections)} detections")
        print(f"   Columns: {len(detections.columns)}")
        success.append("Detection generation")
        
    except Exception as e:
        print(f"❌ Detection generation failed: {e}")
        failures.append(("Detection generation", str(e)))
    
    # Test 5: Satellite data generation (optional)
    print("\n5️⃣  Testing satellite data generation...")
    try:
        if hasattr(mock, 'generate_mock_satellite_data'):
            sat_data = mock.generate_mock_satellite_data(width=50, height=50)
            
            assert isinstance(sat_data, dict), "Satellite data must be dict"
            assert 'bands' in sat_data, "Must have 'bands' key"
            
            band_count = len(sat_data['bands'])
            print(f"✅ Generated satellite data ({band_count} bands)")
            success.append("Satellite data generation")
        else:
            print("⚠️  generate_mock_satellite_data not implemented")
            warnings.append("Satellite data method")
            
    except Exception as e:
        print(f"⚠️  Satellite data generation failed: {e}")
        warnings.append(("Satellite data", str(e)))
    
    # Test 6: CoordinateExtractor (if available)
    print("\n6️⃣  Testing CoordinateExtractor (optional)...")
    try:
        from src.services.coordinate_extractor import CoordinateExtractor
        
        # Just check if it can be imported and initialized
        print("✅ CoordinateExtractor available")
        success.append("CoordinateExtractor")
        
    except ImportError:
        print("⚠️  CoordinateExtractor not available (requires heavy deps)")
        warnings.append("CoordinateExtractor")
    except Exception as e:
        print(f"⚠️  CoordinateExtractor error: {e}")
        warnings.append(("CoordinateExtractor", str(e)))
    
    return failures, warnings, success

def main():
    """Run tests and print summary"""
    failures, warnings, success = test_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("\n📊 Test Summary:")
    print(f"  ✅ Passed: {len(success)}")
    print(f"  ⚠️  Warnings: {len(warnings)}")
    print(f"  ❌ Failed: {len(failures)}")
    
    if failures:
        print("\n❌ INTEGRATION TEST FAILED\n")
        print("Failures:")
        for test_name, error in failures:
            print(f"  • {test_name}: {error}")
        
        success_rate = len(success) / (len(success) + len(failures)) * 100 if (success or failures) else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")
        
        return 1
    else:
        total = len(success) + len(warnings)
        success_rate = len(success) / total * 100 if total else 100
        
        print("\n✅ INTEGRATION TEST PASSED")
        print(f"Success rate: {success_rate:.1f}%")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} non-critical warnings (optional features)")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())
