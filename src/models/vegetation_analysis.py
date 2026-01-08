"""
تحليل الغطاء النباتي
"""
import numpy as np

class VegetationAnalysis:
    """
    تحليل الغطاء النباتي
    """
    
    @staticmethod
    def calculate_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
        """
        حساب NDVI
        """
        return (nir - red) / (nir + red + 1e-10)
    
    @staticmethod
    def calculate_evi(nir: np.ndarray, red: np.ndarray, blue: np.ndarray) -> np.ndarray:
        """
        حساب EVI (Enhanced Vegetation Index)
        """
        return 2.5 * ((nir - red) / (nir + 6 * red - 7.5 * blue + 1))
    
    @staticmethod
    def classify_vegetation(ndvi: np.ndarray) -> np.ndarray:
        """
        تصنيف الغطاء النباتي
        """
        classification = np.zeros_like(ndvi, dtype=int)
        classification[ndvi < 0.2] = 0  # بلا غطاء نباتي
        classification[(ndvi >= 0.2) & (ndvi < 0.4)] = 1  # غطاء خفيف
        classification[(ndvi >= 0.4) & (ndvi < 0.6)] = 2  # غطاء متوسط
        classification[ndvi >= 0.6] = 3  # غطاء كثيف
        return classification
