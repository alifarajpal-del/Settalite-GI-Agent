"""
Synthetic Heritage Generator for Heritage Sentinel Pro
Generates realistic archaeological site patterns for testing and demo purposes.

Supports multiple pattern types:
- Grid: Planned settlements with regular spacing
- Organic: Natural growth patterns (villages, clusters)
- Axial: Linear alignments (roads, canals, walls)
- Random: Scattered individual sites

All output follows canonical schema for seamless integration.
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, box
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SyntheticHeritageGenerator:
    """
    Generate synthetic archaeological site patterns with realistic characteristics.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize generator with optional random seed.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
        
        # Site type probabilities
        self.site_types = {
            'settlement': 0.30,
            'burial': 0.25,
            'temple': 0.15,
            'fortress': 0.10,
            'workshop': 0.10,
            'agricultural': 0.10
        }
        
        logger.info(f"SyntheticHeritageGenerator initialized (seed={seed})")
    
    @staticmethod
    def _get_priority_level(confidence: float) -> str:
        """Get priority level based on confidence"""
        if confidence >= 80:
            return 'high'
        elif confidence >= 65:
            return 'medium'
        else:
            return 'low'
    
    def generate(
        self,
        aoi_bbox: Tuple[float, float, float, float],
        pattern: str = 'mixed',
        num_sites: int = 50,
        confidence_range: Tuple[float, float] = (60, 95),
        area_range: Tuple[float, float] = (500, 5000)
    ) -> pd.DataFrame:
        """
        Generate synthetic archaeological sites within AOI.
        
        Args:
            aoi_bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            pattern: Pattern type ('grid', 'organic', 'axial', 'random', 'mixed')
            num_sites: Number of sites to generate
            confidence_range: (min, max) confidence score [0-100]
            area_range: (min, max) site area in m²
        
        Returns:
            DataFrame with canonical schema (id, lat, lon, confidence, priority, area_m2, site_type, geometry)
        """
        logger.info(f"Generating {num_sites} sites with pattern: {pattern}")
        
        _, _, _, _ = aoi_bbox
        
        if pattern == 'grid':
            sites = self._generate_grid_pattern(aoi_bbox, num_sites)
        elif pattern == 'organic':
            sites = self._generate_organic_pattern(aoi_bbox, num_sites)
        elif pattern == 'axial':
            sites = self._generate_axial_pattern(aoi_bbox, num_sites)
        elif pattern == 'random':
            sites = self._generate_random_pattern(aoi_bbox, num_sites)
        elif pattern == 'mixed':
            # Combine multiple patterns
            grid_sites = self._generate_grid_pattern(aoi_bbox, num_sites // 3)
            organic_sites = self._generate_organic_pattern(aoi_bbox, num_sites // 3)
            random_sites = self._generate_random_pattern(aoi_bbox, num_sites - len(grid_sites) - len(organic_sites))
            sites = grid_sites + organic_sites + random_sites
        else:
            logger.warning(f"Unknown pattern: {pattern}, using random")
            sites = self._generate_random_pattern(aoi_bbox, num_sites)
        
        # Create DataFrame
        df = pd.DataFrame(sites)
        
        # Add confidence scores
        rng = np.random.default_rng(42)
        df['confidence'] = rng.uniform(
            confidence_range[0],
            confidence_range[1],
            size=len(df)
        )
        
        # Add priority based on confidence
        df['priority'] = df['confidence'].apply(
            lambda c: self._get_priority_level(c)
        )
        
        # Add site areas
        df['area_m2'] = np.random.uniform(
            area_range[0],
            area_range[1],
            size=len(df)
        )
        
        # Add site types
        df['site_type'] = self._assign_site_types(len(df))
        
        # Add IDs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df['id'] = [f"SYN_{timestamp}_{i:04d}" for i in range(len(df))]
        
        # Reorder columns to canonical schema
        df = df[['id', 'lat', 'lon', 'confidence', 'priority', 'area_m2', 'site_type']]
        
        logger.info(f"✓ Generated {len(df)} synthetic sites")
        return df
    
    def _generate_grid_pattern(
        self,
        aoi_bbox: Tuple[float, float, float, float],
        num_sites: int
    ) -> List[Dict]:
        """
        Generate grid pattern (planned settlement).
        
        Args:
            aoi_bbox: Bounding box
            num_sites: Approximate number of sites
        
        Returns:
            List of site dictionaries
        """
        min_lon, min_lat, max_lon, max_lat = aoi_bbox
        
        # Calculate grid dimensions
        grid_size = int(np.ceil(np.sqrt(num_sites)))
        
        # Generate grid points
        lons = np.linspace(min_lon, max_lon, grid_size + 2)[1:-1]
        lats = np.linspace(min_lat, max_lat, grid_size + 2)[1:-1]
        
        sites = []
        for lon in lons:
            for lat in lats:
                # Add small random offset (±5% of spacing)
                lon_offset = np.random.uniform(-0.05, 0.05) * (max_lon - min_lon) / grid_size
                lat_offset = np.random.uniform(-0.05, 0.05) * (max_lat - min_lat) / grid_size
                
                sites.append({
                    'lat': lat + lat_offset,
                    'lon': lon + lon_offset
                })
                
                if len(sites) >= num_sites:
                    break
            if len(sites) >= num_sites:
                break
        
        return sites[:num_sites]
    
    def _generate_organic_pattern(
        self,
        aoi_bbox: Tuple[float, float, float, float],
        num_sites: int
    ) -> List[Dict]:
        """
        Generate organic pattern (natural growth with clusters).
        
        Args:
            aoi_bbox: Bounding box
            num_sites: Number of sites
        
        Returns:
            List of site dictionaries
        """
        min_lon, min_lat, max_lon, max_lat = aoi_bbox
        
        # Generate 3-5 cluster centers
        num_clusters = np.random.randint(3, 6)
        cluster_centers = [
            (
                np.random.uniform(min_lon, max_lon),
                np.random.uniform(min_lat, max_lat)
            )
            for _ in range(num_clusters)
        ]
        
        sites = []
        sites_per_cluster = num_sites // num_clusters
        
        for center_lon, center_lat in cluster_centers:
            # Generate sites around cluster center
            for _ in range(sites_per_cluster):
                # Use normal distribution for clustering effect
                radius_deg = np.random.exponential(0.01)  # Exponential decay
                angle = np.random.uniform(0, 2 * np.pi)
                
                lon = center_lon + radius_deg * np.cos(angle)
                lat = center_lat + radius_deg * np.sin(angle)
                
                # Ensure within bounds
                lon = np.clip(lon, min_lon, max_lon)
                lat = np.clip(lat, min_lat, max_lat)
                
                sites.append({
                    'lat': lat,
                    'lon': lon
                })
        
        # Add remaining sites randomly
        while len(sites) < num_sites:
            sites.append({
                'lat': np.random.uniform(min_lat, max_lat),
                'lon': np.random.uniform(min_lon, max_lon)
            })
        
        return sites[:num_sites]
    
    def _generate_axial_pattern(
        self,
        aoi_bbox: Tuple[float, float, float, float],
        num_sites: int
    ) -> List[Dict]:
        """
        Generate axial pattern (linear features like roads/canals).
        
        Args:
            aoi_bbox: Bounding box
            num_sites: Number of sites
        
        Returns:
            List of site dictionaries
        """
        min_lon, min_lat, max_lon, max_lat = aoi_bbox
        
        # Generate 2-3 axes
        num_axes = np.random.randint(2, 4)
        sites = []
        sites_per_axis = num_sites // num_axes
        
        for _ in range(num_axes):
            # Random start and end points
            start_lon = np.random.uniform(min_lon, max_lon)
            start_lat = np.random.uniform(min_lat, max_lat)
            end_lon = np.random.uniform(min_lon, max_lon)
            end_lat = np.random.uniform(min_lat, max_lat)
            
            # Generate sites along axis
            for i in range(sites_per_axis):
                t = i / sites_per_axis  # Parameter along line
                
                lon = start_lon + t * (end_lon - start_lon)
                lat = start_lat + t * (end_lat - start_lat)
                
                # Add perpendicular offset (within ±0.002 degrees)
                perp_offset = np.random.uniform(-0.002, 0.002)
                lon += perp_offset * (end_lat - start_lat)  # Perpendicular direction
                lat -= perp_offset * (end_lon - start_lon)
                
                # Ensure within bounds
                lon = np.clip(lon, min_lon, max_lon)
                lat = np.clip(lat, min_lat, max_lat)
                
                sites.append({
                    'lat': lat,
                    'lon': lon
                })
        
        # Add remaining sites
        while len(sites) < num_sites:
            sites.append({
                'lat': np.random.uniform(min_lat, max_lat),
                'lon': np.random.uniform(min_lon, max_lon)
            })
        
        return sites[:num_sites]
    
    def _generate_random_pattern(
        self,
        aoi_bbox: Tuple[float, float, float, float],
        num_sites: int
    ) -> List[Dict]:
        """
        Generate random pattern (scattered sites).
        
        Args:
            aoi_bbox: Bounding box
            num_sites: Number of sites
        
        Returns:
            List of site dictionaries
        """
        min_lon, min_lat, max_lon, max_lat = aoi_bbox
        
        sites = []
        for _ in range(num_sites):
            sites.append({
                'lat': np.random.uniform(min_lat, max_lat),
                'lon': np.random.uniform(min_lon, max_lon)
            })
        
        return sites
    
    def _assign_site_types(self, num_sites: int) -> List[str]:
        """
        Assign site types based on probabilities.
        
        Args:
            num_sites: Number of sites
        
        Returns:
            List of site type strings
        """
        site_types_list = list(self.site_types.keys())
        probabilities = list(self.site_types.values())
        
        assigned = np.random.choice(
            site_types_list,
            size=num_sites,
            p=probabilities
        )
        
        return assigned.tolist()
    
    def generate_with_metadata(
        self,
        aoi_bbox: Tuple[float, float, float, float],
        pattern: str = 'mixed',
        num_sites: int = 50,
        confidence_range: Tuple[float, float] = (60, 95),
        area_range: Tuple[float, float] = (500, 5000)
    ) -> Dict:
        """
        Generate synthetic sites with metadata about generation.
        
        Args:
            aoi_bbox: Bounding box
            pattern: Pattern type
            num_sites: Number of sites
            confidence_range: Confidence range
            area_range: Area range
        
        Returns:
            Dictionary with 'data' (DataFrame) and 'metadata' (dict)
        """
        df = self.generate(
            aoi_bbox=aoi_bbox,
            pattern=pattern,
            num_sites=num_sites,
            confidence_range=confidence_range,
            area_range=area_range
        )
        
        metadata = {
            'pattern': pattern,
            'num_sites_requested': num_sites,
            'num_sites_generated': len(df),
            'aoi_bbox': aoi_bbox,
            'confidence_range': confidence_range,
            'area_range': area_range,
            'seed': self.seed,
            'generated_at': datetime.now().isoformat(),
            'site_type_distribution': df['site_type'].value_counts().to_dict(),
            'priority_distribution': df['priority'].value_counts().to_dict()
        }
        
        return {
            'data': df,
            'metadata': metadata
        }


def quick_synthetic_test(num_sites: int = 20) -> pd.DataFrame:
    """
    Quick test function to generate synthetic sites.
    
    Args:
        num_sites: Number of sites to generate
    
    Returns:
        DataFrame with synthetic sites
    """
    # Use Riyadh area as default AOI
    riyadh_bbox = (46.5, 24.5, 46.9, 24.9)
    
    generator = SyntheticHeritageGenerator(seed=42)
    df = generator.generate(
        aoi_bbox=riyadh_bbox,
        pattern='mixed',
        num_sites=num_sites
    )
    
    logger.info(f"Quick test generated {len(df)} sites")
    logger.info(f"Confidence range: {df['confidence'].min():.1f} - {df['confidence'].max():.1f}")
    logger.info(f"Area range: {df['area_m2'].min():.0f} - {df['area_m2'].max():.0f} m²")
    logger.info(f"Site types: {df['site_type'].value_counts().to_dict()}")
    
    return df
