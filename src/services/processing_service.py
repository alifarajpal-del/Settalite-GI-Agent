"""
خدمة المعالجة المتقدمة
"""
import numpy as np
from typing import Dict
import warnings
warnings.filterwarnings('ignore')

class AdvancedProcessingService:
    """
    خدمة معالجة متقدمة للبيانات الفضائية
    """
    
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger
        
    def calculate_spectral_indices(self, bands: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        حساب المؤشرات الطيفية المتقدمة
        """
        self.logger.info("حساب المؤشرات الطيفية...")
        
        indices = {}
        
        # Ensure all bands are numpy arrays (convert memoryview if needed)
        bands_array = {}
        for band_name, band_data in bands.items():
            if isinstance(band_data, (memoryview, bytes)):
                bands_array[band_name] = np.frombuffer(band_data, dtype=np.float64).reshape(-1, int(np.sqrt(len(band_data))))
            elif hasattr(band_data, '__array__'):
                bands_array[band_name] = np.asarray(band_data)
            else:
                bands_array[band_name] = band_data
        
        # NDVI
        if 'B08' in bands_array and 'B04' in bands_array:
            nir = np.asarray(bands_array['B08'], dtype=np.float32)
            red = np.asarray(bands_array['B04'], dtype=np.float32)
            indices['NDVI'] = (nir - red) / (nir + red + 1e-10)
        
        # NDWI
        if 'B03' in bands_array and 'B08' in bands_array:
            green = np.asarray(bands_array['B03'], dtype=np.float32)
            nir = np.asarray(bands_array['B08'], dtype=np.float32)
            indices['NDWI'] = (green - nir) / (green + nir + 1e-10)
        
        # MSAVI
        if 'B08' in bands_array and 'B04' in bands_array:
            nir = np.asarray(bands_array['B08'], dtype=np.float32)
            red = np.asarray(bands_array['B04'], dtype=np.float32)
            indices['MSAVI'] = (2 * nir + 1 - np.sqrt((2 * nir + 1)**2 - 8 * (nir - red))) / 2
        
        # NBR
        if 'B08' in bands_array and 'B12' in bands_array:
            nir = np.asarray(bands_array['B08'], dtype=np.float32)
            swir2 = np.asarray(bands_array['B12'], dtype=np.float32)
            indices['NBR'] = (nir - swir2) / (nir + swir2 + 1e-10)
        
        self.logger.info(f"تم حساب {len(indices)} مؤشر طيفي")
        return indices
