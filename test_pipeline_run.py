#!/usr/bin/env python
"""
Simple script to test the pipeline with demo mode to verify the IndexError fix.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.pipeline_service import PipelineService, PipelineRequest
from src.config import load_config
from shapely.geometry import box

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_demo_pipeline():
    """Test the demo mode pipeline end-to-end"""
    print("\n" + "="*70)
    print("Testing Pipeline with Demo Mode")
    print("="*70 + "\n")
    
    try:
        # Load config
        config = load_config()
        print("✓ Config loaded")
        
        # Create pipeline service
        pipeline = PipelineService(config)
        print("✓ Pipeline service created")
        
        # Create a test AOI (small area in Saudi Arabia)
        aoi_geom = box(35.2, 31.9, 35.3, 32.0)
        
        # Create request for demo mode
        request = PipelineRequest(
            mode='demo',  # Use demo mode
            aoi_geometry=aoi_geom,
            start_date='2024-01-01',
            end_date='2024-06-30',
            anomaly_algorithm='isolation_forest',
            contamination=0.1
        )
        
        print(f"✓ Request created (mode={request.mode})")
        print(f"  AOI: {aoi_geom.bounds}")
        
        # Run pipeline
        print("\nRunning pipeline...")
        result = pipeline.run(request)
        
        # Check result
        print(f"\n✓ Pipeline completed!")
        print(f"  Status: {result.status}")
        print(f"  Success: {result.success}")
        print(f"  Step completed: {result.step_completed}")
        
        if result.errors:
            print(f"\n✗ Errors ({len(result.errors)}):")
            for error in result.errors:
                print(f"  - {error}")
            return False
        
        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        # Verify stats
        if result.stats:
            print(f"\n📊 Statistics:")
            for key, value in result.stats.items():
                print(f"  - {key}: {value}")
        
        print("\n" + "="*70)
        print("✓ Pipeline test PASSED!")
        print("="*70 + "\n")
        return True
        
    except Exception as e:
        print(f"\n✗ Pipeline test FAILED!")
        print(f"  Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_demo_pipeline()
    sys.exit(0 if success else 1)
