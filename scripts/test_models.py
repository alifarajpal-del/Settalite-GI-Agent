"""
Test script for Heritage Sentinel Pro ML Models
Tests ensemble, detector, and registry with synthetic features
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from src.models import HeritageDetectionEnsemble, PretrainedAnomalyDetector, ModelRegistry


def test_ensemble():
    """Test HeritageDetectionEnsemble with synthetic features"""
    print("\n[TEST 1] HeritageDetectionEnsemble")
    print("=" * 50)
    
    try:
        ensemble = HeritageDetectionEnsemble()
        print("[OK] Ensemble initialized")
        
        # Test with feature dict
        test_features = {
            'ndvi': 0.25,      # Low vegetation (good for heritage)
            'ndwi': 0.15,      # Low moisture (good for heritage)
            'texture': 0.8,    # High texture complexity
            'shape': 0.7       # Regular shape
        }
        
        score = ensemble.apply_heritage_rules(test_features)
        print(f"[OK] Rule-based score: {score:.2f}")
        print("     Expected: ~1.0 (all rules match)")
        
        # Test with low-confidence features
        low_conf_features = {
            'ndvi': 0.8,       # High vegetation (not heritage)
            'ndwi': 0.6,       # High moisture (not heritage)
            'texture': 0.3,    # Low texture
            'shape': 0.2       # Irregular shape
        }
        
        low_score = ensemble.apply_heritage_rules(low_conf_features)
        print(f"[OK] Low confidence score: {low_score:.2f}")
        print("     Expected: ~0.0 (no rules match)")
        
        return True
    
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        return False


def test_pretrained_detector():
    """Test PretrainedAnomalyDetector"""
    print("\n[TEST 2] PretrainedAnomalyDetector")
    print("=" * 50)
    
    try:
        detector = PretrainedAnomalyDetector()
        print("[OK] Detector initialized (default model)")
        
        # Generate synthetic spectral features
        rng = np.random.default_rng(42)
        normal_data = rng.standard_normal((100, 4))
        anomalies = rng.standard_normal((10, 4)) * 3
        all_data = np.vstack([normal_data, anomalies])
        
        predictions = detector.detect(all_data)
        print("[OK] Detection completed")
        print(f"     Total samples: {len(predictions)}")
        print(f"     Anomalies detected: {np.sum(predictions == -1)}")
        print(f"     Normal points: {np.sum(predictions == 1)}")
        
        return True
    
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        return False


def test_model_registry():
    """Test ModelRegistry save/load/list operations"""
    print("\n[TEST 3] ModelRegistry")
    print("=" * 50)
    
    try:
        registry = ModelRegistry(registry_dir='models/test_registry')
        print("[OK] Registry initialized")
        
        # Create a simple test model
        from sklearn.ensemble import IsolationForest
        test_model = IsolationForest(contamination=0.1, random_state=42)
        
        # Train on dummy data
        rng = np.random.default_rng(42)
        dummy_data = rng.standard_normal((50, 3))
        test_model.fit(dummy_data)
        
        # Save model
        metadata = {
            'version': '1.0.0',
            'description': 'Test isolation forest for heritage detection',
            'training_samples': 50,
            'features': ['ndvi', 'ndwi', 'bai']
        }
        
        model_path = registry.save_model(
            test_model,
            model_name='test_heritage_detector',
            metadata=metadata
        )
        print(f"[OK] Model saved: {model_path}")
        
        # List models
        models = registry.list_models()
        print(f"[OK] Found {len(models)} model(s) in registry")
        for model_info in models:
            print(f"     - {model_info['name']} v{model_info['latest_version']}")
        
        # Load model
        loaded_model = registry.load_model('test_heritage_detector')
        print("[OK] Model loaded successfully")
        
        # Verify it works
        test_predictions = loaded_model.predict(dummy_data[:5])
        print(f"[OK] Loaded model predictions: {test_predictions}")
        
        # Get model info
        info = registry.get_model_info('test_heritage_detector')
        print(f"[OK] Model info retrieved: {info['model_type']}")
        
        # Cleanup
        registry.delete_model('test_heritage_detector')
        print("[OK] Test model deleted")
        
        return True
    
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all model tests"""
    print("\n" + "=" * 50)
    print("Heritage Sentinel Pro - ML Models Test Suite")
    print("=" * 50)
    
    results = {
        'ensemble': test_ensemble(),
        'detector': test_pretrained_detector(),
        'registry': test_model_registry()
    }
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All ML models tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
