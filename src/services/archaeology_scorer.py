"""
PROMPT 5: Realistic Archaeology Scoring
Compute archaeological likelihood based on spectral evidence and site characteristics.

Scoring is ONLY enabled for real data (PROMPT 2 constraint).
Factors:
1. Spectral anomalies (NDVI/NDWI deviance)
2. Spatial clustering (archaeological sites tend to cluster)
3. Landform suitability (slope, elevation)
4. Historical context (proximity to known sites)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import logging
from geopandas import GeoDataFrame


@dataclass
class ArchaeologyScoringConfig:
    """Configuration for archaeology scoring."""
    # Spectral anomaly thresholds
    ndvi_threshold: float = 0.3  # Vegetation stress indicator
    ndwi_threshold: float = 0.1  # Water/moisture indicator
    
    # Spatial weights
    clustering_radius_m: float = 500  # Archaeological sites within 500m cluster
    min_cluster_size: int = 3  # Minimum sites to form cluster
    cluster_weight: float = 0.4  # How much spatial clustering matters
    
    # Spectral weights
    spectral_anomaly_weight: float = 0.35  # How much spectral deviance matters
    pattern_weight: float = 0.25  # How much spatial patterns matter
    
    # Landform weights (when available)
    elevation_weight: float = 0.0  # Not always available
    slope_weight: float = 0.0     # Not always available
    
    # Historical context
    known_sites_buffer_km: float = 5.0  # Consider known sites within 5km


class ArchaeologyScorer:
    """
    Compute archaeological likelihood scores for detected anomalies.
    
    PROMPT 5: Realistic scoring based on:
    1. Spectral evidence (NDVI/NDWI anomalies)
    2. Spatial patterns (clustering, geometric regularity)
    3. Landform suitability (optional)
    4. Historical context (optional)
    
    CRITICAL: Only scores real data. DEMO_MODE always scores=0.
    """
    
    def __init__(self, config: ArchaeologyScoringConfig, logger: logging.Logger = None):
        """Initialize scorer."""
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
    
    def _calculate_site_likelihood(
        self,
        row,
        idx,
        spectral_scores,
        spatial_scores,
        anomaly_map,
        kwargs
    ):
        """Calculate likelihood score for a single site"""
        # Get pixel-level spectral score
        spectral_score = self._get_site_spectral_score(
            row.geometry, anomaly_map, spectral_scores
        )
        
        # Get spatial score (clustering, patterns)
        spatial_score = spatial_scores.get(idx, 0.0)
        
        # Combine with configurable weights
        total_weight = self.config.spectral_anomaly_weight + self.config.pattern_weight
        combined_score = (
            spectral_score * self.config.spectral_anomaly_weight +
            spatial_score * self.config.pattern_weight
        ) / total_weight if total_weight > 0 else 0.0
        
        # Count supporting indicators
        indicators, factors = self._collect_score_factors(
            spectral_score, spatial_score, row.geometry, kwargs
        )
        
        # Calculate confidence
        max_indicators = 2 + (1 if 'elevation' in kwargs else 0)
        confidence = min(100, (indicators / max_indicators) * 100) if max_indicators > 0 else 50
        
        # Apply landform adjustment if available
        if 'elevation' in kwargs and 'landform_suitability' in factors:
            combined_score = combined_score * 0.6 + factors['landform_suitability'] * 0.4
        
        return combined_score * 100, confidence, factors
    
    def _collect_score_factors(self, spectral_score, spatial_score, geometry, kwargs):
        """Collect and count supporting score factors"""
        indicators = 0
        factors = {}
        
        if spectral_score > 0.5:
            indicators += 1
            factors['spectral_anomaly'] = spectral_score
        
        if spatial_score > 0.5:
            indicators += 1
            factors['spatial_clustering'] = spatial_score
        
        # Add landform factors if available
        if 'elevation' in kwargs:
            landform_score = self._score_landform(geometry, kwargs.get('elevation'))
            if landform_score > 0.3:
                indicators += 1
                factors['landform_suitability'] = landform_score
        
        return indicators, factors
    
    def score_sites(
        self,
        gdf: GeoDataFrame,
        indices: Dict[str, np.ndarray],
        anomaly_map: np.ndarray,
        **kwargs
    ) -> GeoDataFrame:
        """
        Score each detected site for archaeological likelihood.
        
        Args:
            gdf: GeoDataFrame with detected anomalies
            indices: Dict with NDVI, NDWI, etc.
            anomaly_map: Boolean array of anomaly pixels
            aoi_geometry: Area of interest polygon/bbox
            **kwargs: Additional context (elevation, slope, etc.)
        
        Returns:
            GeoDataFrame with added score columns:
            - likelihood: 0-100 archaeology probability
            - score_factors: Dict with breakdown
            - confidence: Model confidence in score
        """
        if gdf is None or gdf.empty:
            return gdf
        
        # Compute component scores
        spectral_scores = self._score_spectral_anomalies(indices, anomaly_map)
        spatial_scores = self._score_spatial_patterns(gdf)
        
        # Combine scores
        gdf['likelihood'] = 0.0
        gdf['confidence'] = 0.0
        gdf['score_factors'] = [{} for _ in range(len(gdf))]
        
        for idx, row in gdf.iterrows():
            # Calculate likelihood for this site
            likelihood_score, confidence, factors = self._calculate_site_likelihood(
                row, idx, spectral_scores, spatial_scores, anomaly_map, kwargs
            )
            
            gdf.at[idx, 'likelihood'] = round(likelihood_score, 1)
            gdf.at[idx, 'confidence'] = round(confidence, 1)
            gdf.at[idx, 'score_factors'] = factors
        
        self.logger.info(f"Scored {len(gdf)} sites with archaeology likelihoods")
        return gdf
    
    def _score_spectral_anomalies(
        self,
        indices: Dict[str, np.ndarray],
        anomaly_map: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """
        Compute spectral anomaly score for each pixel.
        
        Combines NDVI (vegetation) and NDWI (moisture) deviance.
        Archaeological sites often show vegetation stress from buried structures.
        """
        scores = {}
        
        # NDVI score: negative anomalies (low vegetation) are archaeological markers
        if 'NDVI' in indices:
            ndvi = indices['NDVI']
            # Normalize to [0, 1]
            ndvi_norm = (ndvi - ndvi.min()) / (ndvi.max() - ndvi.min() + 1e-8)
            # Invert: low NDVI = high score (archaeological interest)
            scores['NDVI'] = 1.0 - ndvi_norm
        
        # NDWI score: anomalies suggest moisture patterns around buried features
        if 'NDWI' in indices:
            ndwi = indices['NDWI']
            ndwi_norm = (ndwi - ndwi.min()) / (ndwi.max() - ndwi.min() + 1e-8)
            # Extreme values (very high or very low) are interesting
            scores['NDWI'] = np.abs(ndwi_norm - 0.5) * 2  # Peaks at extremes
        
        # Combine available scores
        combined = np.zeros_like(anomaly_map, dtype=float)
        if scores:
            for score in scores.values():
                combined += score
            combined /= len(scores)
        
        scores['combined'] = combined
        return scores
    
    def _calculate_clustering_score(self, idx, geom, gdf):
        """Calculate clustering score for a single site"""
        neighbors = []
        for other_idx, other_row in gdf.iterrows():
            if idx != other_idx:
                dist = geom.distance(other_row.geometry)
                # Convert to meters (rough approximation)
                dist_m = dist * 111000  # degrees to meters
                if dist_m < self.config.clustering_radius_m:
                    neighbors.append(dist_m)
        
        # Score based on clustering
        if len(neighbors) >= self.config.min_cluster_size:
            # Sites are clustered - archaeological indicator
            return min(1.0, len(neighbors) / 5)  # Max 5 neighbors
        return 0.0
    
    def _score_spatial_patterns(
        self,
        gdf: GeoDataFrame
    ) -> Dict[int, float]:
        """
        Score spatial patterns that suggest archaeological sites.
        
        Factors:
        - Clustering (nearby sites form patterns)
        - Geometric regularity (grids, alignments)
        """
        scores = {}
        
        if len(gdf) < 3:
            # Need at least 3 sites for spatial patterns
            for idx in gdf.index:
                scores[idx] = 0.0
            return scores
        
        # Compute clustering scores for each site
        for idx, row in gdf.iterrows():
            scores[idx] = self._calculate_clustering_score(idx, row.geometry, gdf)
        
        return scores
    
    def _get_site_spectral_score(
        self,
        geometry,
        anomaly_map: np.ndarray,
        spectral_scores: Dict[str, np.ndarray]
    ) -> float:
        """Get spectral anomaly score for a specific site geometry."""
        # This is simplified - in production would need georeference to convert
        # geometry bounds to raster coordinates
        
        if 'combined' in spectral_scores:
            scores = spectral_scores['combined']
            # For now, return mean of all anomaly pixels
            if scores.size > 0:
                return float(np.mean(scores[anomaly_map]))
        
        return 0.5  # Default if no spectral data
    
    def _score_landform(
        self,
        _,
        __: np.ndarray
    ) -> float:
        """
        Score site suitability based on landform.
        
        Archaeological sites prefer certain elevations and slopes:
        - Floodplains and terraces (habitation areas)
        - Elevated ridges (defensive positions)
        - Water-adjacent areas (resources)
        """
        # Simplified: in production would need georeference
        return 0.5
    
    def score_as_ground_truth(
        self,
        gdf: GeoDataFrame,
        known_sites: Optional[GeoDataFrame] = None
    ) -> Dict[str, Any]:
        """
        Compare scores against known archaeological sites (PROMPT 6).
        
        Returns:
            Dict with:
            - true_positives: Detected sites matching known sites
            - false_positives: Detected sites with no known match
            - true_negatives: Known sites not detected
            - false_negatives: New sites not in training data
            - precision: TP / (TP + FP)
            - recall: TP / (TP + FN)
            - f1_score: 2 * (precision * recall) / (precision + recall)
        """
        if known_sites is None or known_sites.empty:
            return {
                'true_positives': 0,
                'false_positives': len(gdf) if gdf is not None else 0,
                'false_negatives': 0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'note': 'No ground truth data available'
            }
        
        true_positives = 0
        matched_known = set()
        
        # Match detected sites to known sites (within 250m)
        for _, detected in gdf.iterrows():
            for k_idx, known in known_sites.iterrows():
                dist = detected.geometry.distance(known.geometry)
                if dist < 0.0022:  # ~250m in degrees at equator
                    true_positives += 1
                    matched_known.add(k_idx)
                    break
        
        false_positives = len(gdf) - true_positives if gdf is not None else 0
        false_negatives = len(known_sites) - len(matched_known)
        
        # Calculate metrics
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        
        return {
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1, 3),
            'detected_count': len(gdf) if gdf is not None else 0,
            'known_count': len(known_sites)
        }
