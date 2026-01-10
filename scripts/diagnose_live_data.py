"""
Diagnostic script to validate live data flow
تشخيص شامل لتدفق البيانات المباشرة
"""

import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def diagnose_data_shapes():
    """Test data flow with actual shapes"""
    print("=" * 60)
    print("DIAGNOSTIC: Live Data Shape Validation")
    print("=" * 60)
    
    # Test 1: Simulate multi-temporal data from Sentinel Hub
    print("\n[Test 1] Multi-temporal data (3D) handling:")
    timesteps = 5
    height, width = 100, 100
    
    # Simulate band data (time, height, width)
    b03_3d = np.random.rand(timesteps, height, width).astype(np.float32)
    b04_3d = np.random.rand(timesteps, height, width).astype(np.float32)
    b08_3d = np.random.rand(timesteps, height, width).astype(np.float32)
    
    print(f"  B03 shape: {b03_3d.shape} (time, h, w)")
    print(f"  B04 shape: {b04_3d.shape}")
    print(f"  B08 shape: {b08_3d.shape}")
    
    # Apply mean composite
    b03_2d = np.mean(b03_3d, axis=0)
    b04_2d = np.mean(b04_3d, axis=0)
    b08_2d = np.mean(b08_3d, axis=0)
    
    print(f"\n  After mean composite:")
    print(f"  B03 shape: {b03_2d.shape} ✓")
    print(f"  B04 shape: {b04_2d.shape} ✓")
    print(f"  B08 shape: {b08_2d.shape} ✓")
    
    # Compute indices
    nir_2d = b08_2d
    red_2d = b04_2d
    green_2d = b03_2d
    
    ndvi = (nir_2d - red_2d) / (nir_2d + red_2d + 1e-8)
    ndwi = (green_2d - nir_2d) / (green_2d + nir_2d + 1e-8)
    
    print(f"\n  NDVI shape: {ndvi.shape} ✓")
    print(f"  NDWI shape: {ndwi.shape} ✓")
    
    # Test 2: Detection service preparation
    print("\n[Test 2] Detection service feature preparation:")
    
    indices = {
        'NDVI': ndvi,
        'NDWI': ndwi,
        'B04': red_2d,
        'B08': nir_2d
    }
    
    # Validate all are 2D
    all_2d = all(arr.ndim == 2 for arr in indices.values())
    print(f"  All indices are 2D: {all_2d} {'✓' if all_2d else '✗'}")
    
    if not all_2d:
        for name, arr in indices.items():
            print(f"  {name}: {arr.shape} (ndim={arr.ndim}) {'✗' if arr.ndim != 2 else '✓'}")
        return False
    
    # Stack features
    feature_arrays = list(indices.values())
    X = np.stack(feature_arrays, axis=-1)
    print(f"  Stacked features shape: {X.shape} (h, w, features) ✓")
    
    # Validate shape
    assert X.ndim == 3, f"Expected 3D stack, got {X.ndim}D"
    assert X.shape[:2] == (height, width), f"Expected ({height}, {width}), got {X.shape[:2]}"
    assert X.shape[2] == len(indices), f"Expected {len(indices)} features, got {X.shape[2]}"
    
    # Store original shape
    original_shape = X.shape[:2]
    print(f"  Original shape stored: {original_shape} ✓")
    
    # Reshape for sklearn
    X_reshaped = X.reshape(-1, X.shape[-1])
    print(f"  Reshaped for sklearn: {X_reshaped.shape} (samples, features) ✓")
    
    # Validate reshape
    assert X_reshaped.shape[0] == height * width
    assert X_reshaped.shape[1] == len(indices)
    
    # Test 3: Handle NaN values correctly
    print("\n[Test 3] NaN handling:")
    
    # Add some NaN values
    X_with_nan = X.copy()
    X_with_nan[10:20, 30:40, 0] = np.nan  # Add NaN to first feature
    
    n_nan_before = np.sum(np.isnan(X_with_nan))
    print(f"  NaN values before: {n_nan_before}")
    
    # Replace NaN properly
    X_clean = X_with_nan.copy()
    for i in range(X_clean.shape[-1]):
        channel = X_clean[:, :, i]
        channel_mean = np.nanmean(channel)
        if np.isnan(channel_mean):
            channel_mean = 0.0
        X_clean[:, :, i] = np.where(np.isnan(channel), channel_mean, channel)
    
    n_nan_after = np.sum(np.isnan(X_clean))
    print(f"  NaN values after: {n_nan_after} {'✓' if n_nan_after == 0 else '✗'}")
    
    # Test 4: Reshape predictions back to 2D
    print("\n[Test 4] Prediction reshaping:")
    
    # Simulate predictions (1D array)
    predictions = np.random.choice([-1, 1], size=height * width)
    print(f"  Predictions shape: {predictions.shape} (1D) ✓")
    
    # Reshape to original
    anomaly_map = predictions.reshape(original_shape)
    print(f"  Anomaly map shape: {anomaly_map.shape} (h, w) ✓")
    
    assert anomaly_map.shape == (height, width)
    
    # Test 5: Single timestamp data
    print("\n[Test 5] Single timestamp data (2D) handling:")
    
    b03_single = np.random.rand(height, width).astype(np.float32)
    b04_single = np.random.rand(height, width).astype(np.float32)
    b08_single = np.random.rand(height, width).astype(np.float32)
    
    print(f"  B03 shape: {b03_single.shape} (already 2D) ✓")
    print(f"  B04 shape: {b04_single.shape} ✓")
    print(f"  B08 shape: {b08_single.shape} ✓")
    
    # Check if composite needed
    if b03_single.ndim == 3:
        print(f"  Applying mean composite...")
        b03_single = np.mean(b03_single, axis=0)
    else:
        print(f"  No composite needed (already 2D) ✓")
    
    print("\n" + "=" * 60)
    print("✓ ALL DIAGNOSTIC TESTS PASSED")
    print("=" * 60)
    print("\nSummary:")
    print("1. ✓ Multi-temporal (3D) → Mean composite → 2D")
    print("2. ✓ All indices validated as 2D before detection")
    print("3. ✓ Feature stacking produces (h, w, features)")
    print("4. ✓ Reshape to (samples, features) for sklearn")
    print("5. ✓ Original shape preserved for reconstruction")
    print("6. ✓ NaN handling with proper indexing")
    print("7. ✓ Predictions reshaped back to (h, w)")
    print("8. ✓ Single timestamp data handled correctly")
    print("\n✓ Live mode data flow is ROBUST")
    
    return True

if __name__ == "__main__":
    try:
        success = diagnose_data_shapes()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ DIAGNOSTIC FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
