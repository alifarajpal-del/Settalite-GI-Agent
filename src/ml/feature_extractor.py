"""
Feature Extractor for Heritage Site Detection
Converts spectral indices, texture, and shape into standardized ML features
"""
import numpy as np
import warnings
from typing import Dict, Any, Optional
import logging

# Optional dependencies
try:
    from skimage import feature as sk_feature
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Unified feature extraction for heritage site detection.
    Produces consistent feature dictionaries compatible with ML models.
    """
    
    @staticmethod
    def extract_features(
        site_row: Dict[str, Any],
        indices_data: Optional[Dict[str, np.ndarray]] = None,
        geometry: Optional[Any] = None
    ) -> Dict[str, float]:
        """
        Extract standardized features from a candidate site.
        
        Args:
            site_row: Dictionary or DataFrame row with site data
            indices_data: Optional spectral indices (NDVI, NDWI, BAI, etc.)
            geometry: Optional shapely geometry (Polygon or Point)
        
        Returns:
            Feature dictionary with keys: ndvi, ndwi, texture, shape
            All values normalized to [0, 1] range
        """
        features = {
            'ndvi': 0.5,      # Neutral default
            'ndwi': 0.5,      # Neutral default
            'texture': 0.0,   # Unknown texture
            'shape': 0.5      # Neutral shape
        }
        
        # Extract NDVI
        if indices_data and 'NDVI' in indices_data:
            ndvi_array = indices_data['NDVI']
            if isinstance(ndvi_array, np.ndarray) and ndvi_array.size > 0:
                # Use mean, clamp to [0, 1]
                ndvi_mean = float(np.nanmean(ndvi_array))
                features['ndvi'] = max(0.0, min(1.0, (ndvi_mean + 1) / 2))  # [-1,1] -> [0,1]
        elif isinstance(site_row, dict) and 'ndvi' in site_row:
            features['ndvi'] = float(site_row['ndvi'])
        
        # Extract NDWI
        if indices_data and 'NDWI' in indices_data:
            ndwi_array = indices_data['NDWI']
            if isinstance(ndwi_array, np.ndarray) and ndwi_array.size > 0:
                ndwi_mean = float(np.nanmean(ndwi_array))
                features['ndwi'] = max(0.0, min(1.0, (ndwi_mean + 1) / 2))  # [-1,1] -> [0,1]
        elif isinstance(site_row, dict) and 'ndwi' in site_row:
            features['ndwi'] = float(site_row['ndwi'])
        
        # Extract texture complexity
        features['texture'] = FeatureExtractor._compute_texture(
            indices_data, 
            site_row
        )
        
        # Extract shape regularity
        features['shape'] = FeatureExtractor._compute_shape_regularity(
            geometry,
            site_row
        )
        
        return features
    
    @staticmethod
    def _compute_texture(
        indices_data: Optional[Dict[str, np.ndarray]],
        site_row: Dict[str, Any]
    ) -> float:
        """
        Compute texture complexity.
        
        Returns:
            Texture score in [0, 1] (0=smooth, 1=complex)
        """
        # Check if provided directly in site_row
        if isinstance(site_row, dict) and 'texture' in site_row:
            return float(site_row['texture'])
        
        # Try to compute from indices if skimage available
        if SKIMAGE_AVAILABLE and indices_data:
            try:
                # Use NDVI for texture analysis (most informative)
                if 'NDVI' in indices_data:
                    ndvi = indices_data['NDVI']
                    
                    # Ensure 2D array
                    if ndvi.ndim != 2:
                        return 0.0
                    
                    # Convert to uint8 for GLCM
                    ndvi_norm = ((ndvi + 1) / 2 * 255).astype(np.uint8)
                    
                    # Compute GLCM (Gray Level Co-occurrence Matrix)
                    glcm = sk_feature.graycomatrix(
                        ndvi_norm,
                        distances=[1],
                        angles=[0],
                        levels=256,
                        symmetric=True,
                        normed=True
                    )
                    
                    # Extract contrast (measure of texture complexity)
                    contrast = sk_feature.graycoprops(glcm, 'contrast')[0, 0]
                    
                    # Normalize contrast to [0, 1]
                    # High contrast indicates complex texture (heritage sites)
                    texture_score = min(1.0, contrast / 100.0)
                    
                    return float(texture_score)
            
            except Exception as e:
                logger.debug(f"Texture computation failed: {e}")
        
        # Default: unknown texture
        return 0.0
    
    @staticmethod
    def _compute_shape_regularity(
        geometry: Optional[Any],
        site_row: Dict[str, Any]
    ) -> float:
        """
        Compute shape regularity/compactness.
        
        Heritage sites often have regular shapes (rectangular, circular).
        Compactness = 4π * Area / Perimeter²
        Circle = 1.0, irregular shapes < 1.0
        
        Returns:
            Shape score in [0, 1] (0=irregular, 1=perfect circle)
        """
        # Check if provided directly
        if isinstance(site_row, dict) and 'shape' in site_row:
            return float(site_row['shape'])
        
        # Try to compute from geometry
        if geometry is not None:
            try:
                # Check if it's a Polygon
                if hasattr(geometry, 'area') and hasattr(geometry, 'length'):
                    area = geometry.area
                    perimeter = geometry.length
                    
                    if perimeter > 0 and area > 0:
                        # Compactness formula
                        compactness = (4 * np.pi * area) / (perimeter ** 2)
                        
                        # Clamp to [0, 1]
                        compactness = max(0.0, min(1.0, compactness))
                        
                        return float(compactness)
                
                # If it's just a Point, use neutral shape
                elif hasattr(geometry, 'x') and hasattr(geometry, 'y'):
                    return 0.5
            
            except Exception as e:
                logger.debug(f"Shape computation failed: {e}")
        
        # Default: neutral shape (neither regular nor irregular)
        return 0.5
    
    @staticmethod
    def extract_batch_features(
        sites_data: list,
        indices_data: Optional[Dict[str, np.ndarray]] = None,
        geometries: Optional[list] = None
    ) -> list:
        """
        Extract features for multiple sites at once.
        
        Args:
            sites_data: List of site dictionaries
            indices_data: Shared spectral indices
            geometries: List of geometries (one per site)
        
        Returns:
            List of feature dictionaries
        """
        features_list = []
        
        for i, site_row in enumerate(sites_data):
            geometry = geometries[i] if geometries and i < len(geometries) else None
            
            features = FeatureExtractor.extract_features(
                site_row,
                indices_data,
                geometry
            )
            
            features_list.append(features)
        
        return features_list


# Convenience function for simple usage
def extract_features(
    site_row: Dict[str, Any],
    indices_data: Optional[Dict[str, np.ndarray]] = None,
    geometry: Optional[Any] = None
) -> Dict[str, float]:
    """
    Extract features from a site. Wrapper around FeatureExtractor.
    
    Args:
        site_row: Site data dictionary
        indices_data: Optional spectral indices
        geometry: Optional geometry object
    
    Returns:
        Feature dictionary with ndvi, ndwi, texture, shape
    """
    return FeatureExtractor.extract_features(site_row, indices_data, geometry)
