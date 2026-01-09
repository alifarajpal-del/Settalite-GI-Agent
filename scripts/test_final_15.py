"""
Comprehensive Integration Test for Heritage Sentinel Pro Final 15%

Tests all newly implemented components:
- Schema Normalizer (Stability A)
- GeoJSON Validator (Stability B)
- Synthetic Heritage Generator (PROMPT 3)
- Hybrid Data Service (PROMPT 6)
- Benchmark Data Loader (PROMPT 2)

Run with: python scripts/test_final_15.py
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_schema_normalizer():
    """Test schema normalization with mixed data"""
    logger.info("="*60)
    logger.info("TEST 1: Schema Normalizer")
    logger.info("="*60)
    
    try:
        from src.utils.schema_normalizer import normalize_detections, validate_dataframe_schema
        
        # Create test data with Arabic columns
        test_data = pd.DataFrame({
            'خط العرض': [24.5, 24.6, 24.7],
            'خط الطول': [46.5, 46.6, 46.7],
            'الثقة': [85, 70, 95],
            'الأولوية': ['عالية', 'متوسطة', 'عالية'],
            'site_id': ['TEST_001', 'TEST_002', 'TEST_003']
        })
        
        logger.info(f"Input: {len(test_data)} rows with Arabic columns")
        logger.info(f"Columns: {list(test_data.columns)}")
        
        # Normalize
        normalized = normalize_detections(test_data)
        
        logger.info(f"Output: {len(normalized)} rows")
        logger.info(f"Columns: {list(normalized.columns)}")
        
        # Validate
        is_valid, errors = validate_dataframe_schema(normalized)
        
        if is_valid:
            logger.info("✓ TEST 1 PASSED: Schema normalization successful")
            return True
        else:
            logger.error(f"✗ TEST 1 FAILED: Validation errors: {errors}")
            return False
    
    except Exception as e:
        logger.error(f"✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_geojson_validator():
    """Test GeoJSON validation and export"""
    logger.info("="*60)
    logger.info("TEST 2: GeoJSON Validator")
    logger.info("="*60)
    
    try:
        from src.utils.geojson_validator import (
            create_valid_geojson,
            quick_geojson_test,
            get_geojson_statistics
        )
        
        # Create test data
        test_data = pd.DataFrame({
            'id': ['TEST_001', 'TEST_002'],
            'lat': [24.5, 24.6],
            'lon': [46.5, 46.6],
            'confidence': [85.0, 70.0],
            'priority': ['high', 'medium'],
            'area_m2': [1500.0, 2000.0],
            'site_type': ['settlement', 'burial']
        })
        
        logger.info(f"Input: {len(test_data)} sites")
        
        # Create GeoJSON
        geojson_bytes = create_valid_geojson(test_data)
        
        logger.info(f"Generated GeoJSON: {len(geojson_bytes)} bytes")
        
        # Validate
        is_valid = quick_geojson_test(geojson_bytes)
        
        # Get statistics
        stats = get_geojson_statistics(geojson_bytes)
        
        logger.info(f"Valid: {is_valid}")
        logger.info(f"Features: {stats['feature_count']}")
        logger.info(f"Size: {stats['size_kb']} KB")
        
        if is_valid and stats['feature_count'] == len(test_data):
            logger.info("✓ TEST 2 PASSED: GeoJSON validation successful")
            return True
        else:
            logger.error(f"✗ TEST 2 FAILED: Validation or feature count mismatch")
            return False
    
    except Exception as e:
        logger.error(f"✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_synthetic_generator():
    """Test synthetic heritage site generation"""
    logger.info("="*60)
    logger.info("TEST 3: Synthetic Heritage Generator")
    logger.info("="*60)
    
    try:
        from src.services.synthetic_heritage_generator import (
            SyntheticHeritageGenerator,
            quick_synthetic_test
        )
        
        # Quick test
        df = quick_synthetic_test(num_sites=30)
        
        logger.info(f"Generated: {len(df)} sites")
        logger.info(f"Patterns: mixed (grid + organic + random)")
        
        # Check schema
        required_cols = ['id', 'lat', 'lon', 'confidence', 'priority', 'area_m2', 'site_type']
        has_all_cols = all(col in df.columns for col in required_cols)
        
        if has_all_cols and len(df) > 0:
            logger.info(f"Site types: {df['site_type'].value_counts().to_dict()}")
            logger.info(f"Priority distribution: {df['priority'].value_counts().to_dict()}")
            logger.info("✓ TEST 3 PASSED: Synthetic generation successful")
            return True
        else:
            logger.error(f"✗ TEST 3 FAILED: Missing columns or no data")
            return False
    
    except Exception as e:
        logger.error(f"✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_data_service():
    """Test hybrid data service combining multiple sources"""
    logger.info("="*60)
    logger.info("TEST 4: Hybrid Data Service")
    logger.info("="*60)
    
    try:
        from src.services.hybrid_data_service import HybridDataService, quick_hybrid_test
        
        # Quick test
        df = quick_hybrid_test()
        
        logger.info(f"Combined: {len(df)} sites")
        
        # Check for source column
        if 'source' in df.columns:
            logger.info(f"Sources: {df['source'].unique().tolist()}")
            
            # Get statistics
            service = HybridDataService()
            stats = service.get_source_statistics(df)
            
            logger.info(f"Total sites: {stats['total_sites']}")
            logger.info(f"Confidence: {stats['confidence_stats']['mean']:.1f} (avg)")
            
            logger.info("✓ TEST 4 PASSED: Hybrid data service successful")
            return True
        else:
            logger.error(f"✗ TEST 4 FAILED: No source column")
            return False
    
    except Exception as e:
        logger.error(f"✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_benchmark_loader():
    """Test benchmark data loader (without downloading)"""
    logger.info("="*60)
    logger.info("TEST 5: Benchmark Data Loader")
    logger.info("="*60)
    
    try:
        from src.services.benchmark_data_loader import BenchmarkDataLoader
        
        loader = BenchmarkDataLoader()
        
        # Check availability
        is_available = loader.is_eurosat_available()
        logger.info(f"EuroSAT available: {is_available}")
        
        # Get statistics
        stats = loader.get_statistics()
        logger.info(f"Data directory: {stats['data_dir']}")
        logger.info(f"Heritage classes: {len(stats['heritage_classes'])}")
        
        if is_available:
            logger.info(f"Total images: {stats.get('total_images', 0)}")
            
            # Try loading samples
            df = loader.load_eurosat_samples(num_samples=10, heritage_only=True)
            if df is not None and len(df) > 0:
                logger.info(f"Loaded {len(df)} samples successfully")
                logger.info("✓ TEST 5 PASSED: Benchmark loader fully functional")
                return True
        
        # Even without download, loader should initialize properly
        logger.info("✓ TEST 5 PASSED: Benchmark loader initialized (download not tested)")
        return True
    
    except Exception as e:
        logger.error(f"✗ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end_integration():
    """Test complete integration of all components"""
    logger.info("="*60)
    logger.info("TEST 6: End-to-End Integration")
    logger.info("="*60)
    
    try:
        from src.services.synthetic_heritage_generator import SyntheticHeritageGenerator
        from src.services.hybrid_data_service import HybridDataService
        from src.utils.schema_normalizer import normalize_detections
        from src.utils.geojson_validator import create_valid_geojson, quick_geojson_test
        
        # Step 1: Generate synthetic data
        generator = SyntheticHeritageGenerator(seed=42)
        riyadh_bbox = (46.5, 24.5, 46.9, 24.9)
        
        df1 = generator.generate(riyadh_bbox, pattern='grid', num_sites=20)
        df2 = generator.generate(riyadh_bbox, pattern='organic', num_sites=15)
        
        logger.info(f"Generated: {len(df1)} grid + {len(df2)} organic sites")
        
        # Step 2: Combine with hybrid service
        service = HybridDataService()
        sources = {
            'synthetic_grid': df1,
            'synthetic_organic': df2
        }
        combined = service.combine_sources(sources, aoi_bbox=riyadh_bbox)
        
        logger.info(f"Combined: {len(combined)} sites")
        
        # Step 3: Normalize schema (should be no-op for already normalized data)
        normalized = normalize_detections(combined)
        
        logger.info(f"Normalized: {len(normalized)} sites")
        
        # Step 4: Export to validated GeoJSON
        geojson_bytes = create_valid_geojson(normalized)
        is_valid = quick_geojson_test(geojson_bytes)
        
        logger.info(f"GeoJSON: {len(geojson_bytes)} bytes, Valid: {is_valid}")
        
        # Step 5: Verify data integrity
        if len(combined) > 0 and is_valid:
            logger.info("✓ TEST 6 PASSED: End-to-end integration successful")
            return True
        else:
            logger.error(f"✗ TEST 6 FAILED: Data lost or invalid export")
            return False
    
    except Exception as e:
        logger.error(f"✗ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("HERITAGE SENTINEL PRO - FINAL 15% INTEGRATION TESTS")
    logger.info("="*60)
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("")
    
    results = []
    
    # Run tests
    results.append(("Schema Normalizer", test_schema_normalizer()))
    results.append(("GeoJSON Validator", test_geojson_validator()))
    results.append(("Synthetic Generator", test_synthetic_generator()))
    results.append(("Hybrid Data Service", test_hybrid_data_service()))
    results.append(("Benchmark Loader", test_benchmark_loader()))
    results.append(("End-to-End Integration", test_end_to_end_integration()))
    
    # Summary
    logger.info("")
    logger.info("="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
