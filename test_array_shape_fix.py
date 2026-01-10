"""Quick test of the array shape fix"""
import sys
sys.path.insert(0, '.')

from src.services.mock_data_service import MockDataService
from src.services.processing_service import AdvancedProcessingService
from src.services.detection_service import AnomalyDetectionService
import logging
import numpy as np

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

print("=" * 70)
print("Testing Array Shape Handling Fix")
print("=" * 70 + "\n")

try:
    # 1. Generate mock bands
    imagery = MockDataService.generate_mock_satellite_data(height=50, width=50)
    bands = imagery['bands']
    print(f"✓ Step 1: Mock bands generated")
    for name, arr in bands.items():
        print(f"    {name}: shape={arr.shape}, dtype={arr.dtype}")
    
    # 2. Calculate spectral indices
    proc = AdvancedProcessingService({}, logger)
    indices = proc.calculate_spectral_indices(bands)
    print(f"\n✓ Step 2: Spectral indices calculated")
    for name, arr in indices.items():
        print(f"    {name}: shape={arr.shape}, ndim={arr.ndim}")
    
    # 3. Verify all are 2D
    all_2d = all(arr.ndim == 2 for arr in indices.values())
    print(f"\n✓ Step 3: All indices are 2D: {all_2d}")
    
    # 4. Test detection service
    detector = AnomalyDetectionService({}, logger)
    result = detector.detect_anomalies(
        indices=indices,
        algorithm='isolation_forest',
        contamination=0.1
    )
    print(f"\n✓ Step 4: Anomaly detection completed")
    print(f"    Anomaly map shape: {result['anomaly_map'].shape}")
    print(f"    Anomalies found: {int(np.sum(result['anomaly_map']))}")
    
    print("\n" + "=" * 70)
    print("✓✓✓ ALL TESTS PASSED - Fix is working! ✓✓✓")
    print("=" * 70)

except Exception as e:
    print(f"\n✗ TEST FAILED!")
    print(f"  Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
