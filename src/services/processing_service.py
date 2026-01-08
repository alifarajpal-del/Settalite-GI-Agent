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
        
        # NDVI
        if 'B08' in bands and 'B04' in bands:
            nir = bands['B08'].astype(np.float32)
            red = bands['B04'].astype(np.float32)
            indices['NDVI'] = (nir - red) / (nir + red + 1e-10)
        
        # NDWI
        if 'B03' in bands and 'B08' in bands:
            green = bands['B03'].astype(np.float32)
            nir = bands['B08'].astype(np.float32)
            indices['NDWI'] = (green - nir) / (green + nir + 1e-10)
        
        # MSAVI
        if 'B08' in bands and 'B04' in bands:
            nir = bands['B08'].astype(np.float32)
            red = bands['B04'].astype(np.float32)
            indices['MSAVI'] = (2 * nir + 1 - np.sqrt((2 * nir + 1)**2 - 8 * (nir - red))) / 2
        
        # NBR
        if 'B08' in bands and 'B12' in bands:
            nir = bands['B08'].astype(np.float32)
            swir2 = bands['B12'].astype(np.float32)
            indices['NBR'] = (nir - swir2) / (nir + swir2 + 1e-10)
        
        self.logger.info(f"تم حساب {len(indices)} مؤشر طيفي")
        return indices
