"""
PROACTIVE FIX: Anticipate and resolve future issues
توقع وحل المشاكل المستقبلية بشكل استباقي

Based on the 7 errors encountered during live deployment, this script identifies
and fixes potential future issues BEFORE they occur.
"""

import re
from pathlib import Path

def _apply_pipeline_validation_fix(pipeline_path, fixes_applied):
    """Apply defensive checks fix to pipeline_service.py"""
    if not pipeline_path.exists():
        return
    
    content = pipeline_path.read_text(encoding='utf-8')
    
    # Add validation for empty results before STEP 3
    if 'if not indices or len(indices) == 0:' not in content:
        # Find STEP 3 section
        step3_pattern = r'(# STEP 3: Detect anomalies\s+logger\.info\("STEP 3/5: Detecting anomalies\.\.\."\))'
        
        validation_code = r'''\1
        
        # Validate indices exist and have correct shape
        if not indices or len(indices) == 0:
            logger.error("No spectral indices calculated - cannot proceed with detection")
            return {
                'status': 'error',
                'error': 'No spectral indices calculated',
                'step_failed': 'indices',
                'run_id': run_id
            }
        
        # Validate all indices are 2D arrays
        for idx_name, idx_data in indices.items():
            if not hasattr(idx_data, 'shape'):
                logger.error(f"Index {idx_name} is not a numpy array: {type(idx_data)}")
                return {
                    'status': 'error',
                    'error': f'Index {idx_name} is not a numpy array',
                    'step_failed': 'indices',
                    'run_id': run_id
                }
            if idx_data.ndim != 2:
                logger.error(f"Index {idx_name} has wrong shape: {idx_data.shape} (expected 2D)")
                return {
                    'status': 'error',
                    'error': f'Index {idx_name} has shape {idx_data.shape}, expected 2D',
                    'step_failed': 'indices',
                    'run_id': run_id
                }
        '''
        
        content = re.sub(step3_pattern, validation_code, content)
        fixes_applied.append("Added validation for indices before STEP 3")
    
    pipeline_path.write_text(content, encoding='utf-8')

def _apply_cloud_coverage_fix(sh_provider_path, fixes_applied):
    """Apply cloud coverage validation to sentinelhub_provider.py"""
    if not sh_provider_path.exists():
        return
    
    content = sh_provider_path.read_text(encoding='utf-8')
    
    # Add validation to ensure scenes meet cloud coverage threshold
    if 'scenes = [s for s in scenes if' not in content:
        # Find search_scenes method
        search_pattern = r'(scenes = \[\{[^\]]+\] for item in results\.get_items\(\)\])'
        
        validation_code = r'''\1
        
        # Filter scenes by cloud coverage if specified
        if max_cloud_cover is not None:
            original_count = len(scenes)
            scenes = [s for s in scenes if s.get('cloud_coverage', 100) <= max_cloud_cover]
            logger.info(f"Filtered {original_count} scenes to {len(scenes)} with cloud coverage <= {max_cloud_cover}%")
        '''
        
        if re.search(search_pattern, content):
            content = re.sub(search_pattern, validation_code, content)
            fixes_applied.append("Added cloud coverage filtering in search_scenes")
    
    sh_provider_path.write_text(content, encoding='utf-8')

def _apply_retry_logic_fix(sh_provider_path, fixes_applied):
    """Apply retry logic for Sentinel Hub API calls"""
    if not sh_provider_path.exists():
        return
    
    content = sh_provider_path.read_text(encoding='utf-8')
    
    # Add retry decorator import
    if 'from tenacity import retry, stop_after_attempt, wait_exponential' not in content:
        # Add import at top
        import_pattern = r'(import logging\n)'
        import_code = r'\1from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type\nfrom sentinelhub import SHRuntimeError\n'
        content = re.sub(import_pattern, import_code, content)
        fixes_applied.append("Added retry logic imports")
    
    # Add retry decorator to fetch_band_stack
    if '@retry' not in content.split('def fetch_band_stack')[0].split('\n')[-2]:
        fetch_pattern = r'(\s+)(def fetch_band_stack\()'
        retry_code = r'\1@retry(\n\1    stop=stop_after_attempt(3),\n\1    wait=wait_exponential(multiplier=1, min=4, max=10),\n\1    retry=retry_if_exception_type((SHRuntimeError, ConnectionError, TimeoutError)),\n\1    reraise=True\n\1)\n\1\2'
        content = re.sub(fetch_pattern, retry_code, content)
        fixes_applied.append("Added retry logic to fetch_band_stack")
    
    sh_provider_path.write_text(content, encoding='utf-8')

def _apply_memory_optimization_fix(pipeline_path, fixes_applied):
    """Apply memory optimization for large imagery"""
    if not pipeline_path.exists():
        return
    
    content = pipeline_path.read_text(encoding='utf-8')
    
    # Add garbage collection after heavy processing
    if 'import gc' not in content:
        import_pattern = r'(import numpy as np\n)'
        import_code = r'\1import gc\n'
        content = re.sub(import_pattern, import_code, content)
        fixes_applied.append("Added garbage collection import")
    
    # Add gc.collect() after STEP 2
    if 'gc.collect()' not in content:
        step2_end_pattern = r'(logger\.info\(f"✓ Successfully calculated \{len\(indices\)\} spectral indices"\)\n)'
        gc_code = r'\1            gc.collect()  # Free memory from band processing\n'
        content = re.sub(step2_end_pattern, gc_code, content)
        fixes_applied.append("Added garbage collection after STEP 2")
    
    pipeline_path.write_text(content, encoding='utf-8')

def _apply_logging_fix(pipeline_path, fixes_applied):
    """Apply logging for data shapes throughout pipeline"""
    if not pipeline_path.exists():
        return
    
    content = pipeline_path.read_text(encoding='utf-8')
    
    # Add shape logging after band fetching
    if 'logger.debug(f"Band {band_name} shape:' not in content:
        band_pattern = r'(for band_name, band_data in band_result\.bands\.items\(\):)'
        shape_log = r'\1\n                logger.debug(f"Band {band_name} shape: {band_data.data.shape if hasattr(band_data, \'data\') else \'N/A\'}")'
        content = re.sub(band_pattern, shape_log, content)
        fixes_applied.append("Added shape logging for bands")
    
    pipeline_path.write_text(content, encoding='utf-8')

def apply_fixes():
    """Apply proactive fixes to prevent future issues"""
    
    fixes_applied = []
    
    # Define file paths
    pipeline_path = Path("src/services/pipeline_service.py")
    sh_provider_path = Path("src/providers/sentinelhub_provider.py")
    
    # Apply fixes using helper functions
    _apply_pipeline_validation_fix(pipeline_path, fixes_applied)
    _apply_cloud_coverage_fix(sh_provider_path, fixes_applied)
    _apply_retry_logic_fix(sh_provider_path, fixes_applied)
    _apply_memory_optimization_fix(pipeline_path, fixes_applied)
    _apply_logging_fix(pipeline_path, fixes_applied)
    
    # ============================================================
    # FIX 6: Add validation for coordinate systems
    # ============================================================
    detector_path = Path("src/services/detection_service.py")
    if detector_path.exists():
        content = detector_path.read_text(encoding='utf-8')
        
        # Add CRS validation in extract_coordinates
        if 'if bbox_crs != 4326:' not in content:
            extract_pattern = r'(def extract_coordinates\([^)]+\):)'
            crs_validation = r'''\1
        """Extract geographic coordinates from anomaly pixels with CRS validation"""
        
        # Validate CRS
        if bbox_crs != 4326:
            logger.warning(f"Input CRS is {bbox_crs}, expected WGS84 (4326). Reprojection may be needed.")
        '''
            content = re.sub(extract_pattern, crs_validation, content)
            fixes_applied.append("Added CRS validation in extract_coordinates")
        
        detector_path.write_text(content, encoding='utf-8')
    
    # ============================================================
    # FIX 7: Add timeout configuration for API calls
    # ============================================================
    if sh_provider_path.exists():
        content = sh_provider_path.read_text(encoding='utf-8')
        
        # Add timeout to SHConfig
        if 'config.sh_timeout' not in content:
            config_pattern = r'(self\.config = SHConfig\(\))'
            timeout_code = r'''\1
        self.config.sh_timeout = 120  # 2 minutes timeout for API calls
        '''
            content = re.sub(config_pattern, timeout_code, content)
            fixes_applied.append("Added timeout configuration to SHConfig")
        
        sh_provider_path.write_text(content, encoding='utf-8')
    
    return fixes_applied

if __name__ == "__main__":
    print("=" * 60)
    print("PROACTIVE FIX: Anticipating Future Issues")
    print("=" * 60)
    
    fixes = apply_fixes()
    
    if fixes:
        print(f"\n✓ Applied {len(fixes)} proactive fixes:\n")
        for i, fix in enumerate(fixes, 1):
            print(f"  {i}. {fix}")
        print("\n" + "=" * 60)
        print("System hardened against future issues!")
        print("=" * 60)
    else:
        print("\n✓ All proactive fixes already applied")
