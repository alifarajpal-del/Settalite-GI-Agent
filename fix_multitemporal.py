"""Comprehensive fix for live mode data shape and structure issues"""
import re

file_path = r'c:\Users\PH-User\Desktop\Settalite-GI-Agent\src\services\pipeline_service.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the section where we compute NDVI/NDWI and replace it entirely
old_section = """            # PROMPT 3: Use real NDVI/NDWI for live mode
            if request.mode == 'live' and 'B04' in bands_data and 'B08' in bands_data:
                # Compute real NDVI/NDWI from downloaded bands (PROMPT 3)
                from src.providers import SentinelHubProvider
                sh_provider = SentinelHubProvider(self.config, self.logger)
                
                # Compute NDVI and NDWI
                ndvi = sh_provider.compute_ndvi(bands_data['B04'], bands_data['B08'])
                ndwi = sh_provider.compute_ndwi(bands_data['B03'], bands_data['B08'])
                
                # Create indices dict with real computed values
                indices = {
                    'NDVI': ndvi,
                    'NDWI': ndwi,
                    'B04': bands_data['B04'],  # Red
                    'B08': bands_data['B08']   # NIR
                }
                
                # Add indicators to manifest (PROMPT 2)
                from src.provenance.run_manifest import ComputedIndicator
                manifest.add_indicator(ComputedIndicator(
                    name='NDVI',
                    formula='(NIR - RED) / (NIR + RED)',
                    bands_used=['B08', 'B04'],
                    temporal_coverage={'computed_scenes': len(band_timestamps)},
                    computed_from_real_data=True
                ))
                manifest.add_indicator(ComputedIndicator(
                    name='NDWI',
                    formula='(GREEN - NIR) / (GREEN + NIR)',
                    bands_used=['B03', 'B08'],
                    temporal_coverage={'computed_scenes': len(band_timestamps)},
                    computed_from_real_data=True
                ))
                
                self.logger.info("✓ Computed real NDVI/NDWI from live imagery")"""

new_section = """            # PROMPT 3: Use real NDVI/NDWI for live mode
            if request.mode == 'live' and 'B04' in bands_data and 'B08' in bands_data:
                # Compute real NDVI/NDWI from downloaded bands (PROMPT 3)
                from src.providers import SentinelHubProvider
                sh_provider = SentinelHubProvider(self.config, self.logger)
                
                # Compute NDVI and NDWI (returns IndexTimeseries objects)
                ndvi_ts = sh_provider.compute_ndvi(bands_data['B04'], bands_data['B08'])
                ndwi_ts = sh_provider.compute_ndwi(bands_data['B03'], bands_data['B08'])
                
                # Extract data arrays: shape is (time, height, width) or (height, width)
                # For multi-temporal: use mean composite across time
                ndvi_data = ndvi_ts.data
                ndwi_data = ndwi_ts.data
                
                # If multi-temporal (3D), compute mean composite
                if ndvi_data.ndim == 3:
                    self.logger.info(f"Multi-temporal data: {ndvi_data.shape[0]} timesteps, computing mean composite...")
                    ndvi_data = np.mean(ndvi_data, axis=0)  # (height, width)
                    ndwi_data = np.mean(ndwi_data, axis=0)  # (height, width)
                
                # Also need 2D versions of bands for compatibility
                b04_data = bands_data['B04'].data
                b08_data = bands_data['B08'].data
                if b04_data.ndim == 3:
                    b04_data = np.mean(b04_data, axis=0)
                    b08_data = np.mean(b08_data, axis=0)
                
                # Create indices dict with 2D arrays for detection service
                indices = {
                    'NDVI': ndvi_data,      # 2D array (height, width)
                    'NDWI': ndwi_data,      # 2D array (height, width)
                    'B04': b04_data,        # 2D array (height, width)
                    'B08': b08_data         # 2D array (height, width)
                }
                
                # Add indicators to manifest (PROMPT 2)
                from src.provenance.run_manifest import ComputedIndicator
                manifest.add_indicator(ComputedIndicator(
                    name='NDVI',
                    formula='(NIR - RED) / (NIR + RED)',
                    bands_used=['B08', 'B04'],
                    temporal_coverage={
                        'computed_scenes': len(band_timestamps),
                        'composite_method': 'mean' if ndvi_ts.data.ndim == 3 else 'single'
                    },
                    computed_from_real_data=True
                ))
                manifest.add_indicator(ComputedIndicator(
                    name='NDWI',
                    formula='(GREEN - NIR) / (GREEN + NIR)',
                    bands_used=['B03', 'B08'],
                    temporal_coverage={
                        'computed_scenes': len(band_timestamps),
                        'composite_method': 'mean' if ndwi_ts.data.ndim == 3 else 'single'
                    },
                    computed_from_real_data=True
                ))
                
                self.logger.info(f"✓ Computed real NDVI/NDWI from live imagery (shape: {ndvi_data.shape})")"""

content = content.replace(old_section, new_section)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed multi-temporal data handling:")
print("  - Extract .data from IndexTimeseries")
print("  - Compute mean composite for 3D arrays (time, h, w) → (h, w)")
print("  - All arrays now 2D for detection service")
print("  - Added composite_method to manifest")
