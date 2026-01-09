"""
Hybrid Data Service for Heritage Sentinel Pro
Manages multiple data sources and combines them intelligently:
- Real satellite detections (live mode)
- Mock data (demo mode)
- Synthetic heritage sites (testing/demo)
- Benchmark datasets (optional)

All sources are normalized to canonical schema before merging.
"""
import pandas as pd
import geopandas as gpd
from typing import Dict, List, Optional, Tuple
from shapely.geometry import Point, box
import logging
from datetime import datetime

# Import internal services
from src.services.synthetic_heritage_generator import SyntheticHeritageGenerator
from src.utils.schema_normalizer import normalize_detections

logger = logging.getLogger(__name__)


class HybridDataService:
    """
    Service for managing and combining multiple heritage detection data sources.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize hybrid data service.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.synthetic_generator = SyntheticHeritageGenerator(seed=42)
        
        # Source weights for confidence adjustment
        self.source_weights = {
            'real': 1.0,      # Real detections are trusted most
            'mock': 0.8,      # Mock data is for demo only
            'synthetic': 0.9, # Synthetic is realistic but not real
            'benchmark': 0.95 # Benchmark is validated
        }
        
        logger.info("HybridDataService initialized")
    
    def combine_sources(
        self,
        sources: Dict[str, pd.DataFrame],
        aoi_bbox: Optional[Tuple[float, float, float, float]] = None,
        deduplicate: bool = True,
        dedupe_threshold_m: float = 100.0
    ) -> pd.DataFrame:
        """
        Combine multiple data sources into single normalized dataset.
        
        Args:
            sources: Dictionary of {source_name: dataframe}
            aoi_bbox: Optional AOI for filtering (min_lon, min_lat, max_lon, max_lat)
            deduplicate: Whether to remove duplicate sites
            dedupe_threshold_m: Distance threshold for considering sites duplicates
        
        Returns:
            Combined and normalized DataFrame
        """
        logger.info(f"Combining {len(sources)} data sources...")
        
        combined_dfs = []
        
        for source_name, df in sources.items():
            if df is None or df.empty:
                logger.warning(f"Source '{source_name}' is empty, skipping")
                continue
            
            logger.info(f"Processing source: {source_name} ({len(df)} sites)")
            
            # Normalize to canonical schema
            try:
                df_normalized = normalize_detections(df)
            except Exception as e:
                logger.error(f"Failed to normalize {source_name}: {e}")
                continue
            
            # Add source metadata
            df_normalized['source'] = source_name
            
            # Adjust confidence based on source weight
            if source_name in self.source_weights:
                weight = self.source_weights[source_name]
                df_normalized['confidence'] = df_normalized['confidence'] * weight
                # Clamp to [0, 100]
                df_normalized['confidence'] = df_normalized['confidence'].clip(0, 100)
            
            # Filter by AOI if provided
            if aoi_bbox is not None:
                min_lon, min_lat, max_lon, max_lat = aoi_bbox
                df_normalized = df_normalized[
                    (df_normalized['lon'] >= min_lon) &
                    (df_normalized['lon'] <= max_lon) &
                    (df_normalized['lat'] >= min_lat) &
                    (df_normalized['lat'] <= max_lat)
                ]
                logger.info(f"  After AOI filter: {len(df_normalized)} sites")
            
            combined_dfs.append(df_normalized)
        
        if not combined_dfs:
            logger.warning("No valid data sources to combine")
            return pd.DataFrame()
        
        # Concatenate all sources
        combined = pd.concat(combined_dfs, ignore_index=True)
        logger.info(f"Combined dataset: {len(combined)} total sites")
        
        # Deduplicate if requested
        if deduplicate:
            combined = self._deduplicate_sites(combined, threshold_m=dedupe_threshold_m)
            logger.info(f"After deduplication: {len(combined)} unique sites")
        
        # Re-normalize priority based on adjusted confidence
        combined['priority'] = combined['confidence'].apply(lambda c: 
            'high' if c >= 80 else 'medium' if c >= 65 else 'low'
        )
        
        # Sort by confidence (descending)
        combined = combined.sort_values('confidence', ascending=False).reset_index(drop=True)
        
        logger.info("✓ Data sources combined successfully")
        return combined
    
    def _deduplicate_sites(
        self,
        df: pd.DataFrame,
        threshold_m: float = 100.0
    ) -> pd.DataFrame:
        """
        Remove duplicate sites based on distance threshold.
        
        Args:
            df: DataFrame with lat/lon columns
            threshold_m: Distance threshold in meters
        
        Returns:
            DataFrame with duplicates removed
        """
        if len(df) == 0:
            return df
        
        logger.info(f"Deduplicating sites (threshold={threshold_m}m)...")
        
        # Convert to GeoDataFrame if not already
        if not isinstance(df, gpd.GeoDataFrame):
            if 'geometry' not in df.columns:
                df['geometry'] = df.apply(
                    lambda row: Point(row['lon'], row['lat']),
                    axis=1
                )
            df = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
        
        # Reproject to metric CRS for distance calculation (UTM zone 38N for Saudi Arabia)
        df_utm = df.to_crs('EPSG:32638')
        
        # Track which sites to keep
        keep_indices = []
        removed_count = 0
        
        for i in range(len(df_utm)):
            if i in keep_indices:
                continue
            
            # Keep this site
            keep_indices.append(i)
            
            # Find sites within threshold
            current_geom = df_utm.iloc[i].geometry
            
            for j in range(i + 1, len(df_utm)):
                if j in keep_indices:
                    continue
                
                other_geom = df_utm.iloc[j].geometry
                distance = current_geom.distance(other_geom)
                
                if distance < threshold_m:
                    # Sites are duplicates - keep the one with higher confidence
                    if df.iloc[j]['confidence'] > df.iloc[i]['confidence']:
                        # Replace with higher confidence site
                        keep_indices.remove(i)
                        keep_indices.append(j)
                        removed_count += 1
                        break
                    else:
                        # Remove the lower confidence site
                        removed_count += 1
        
        # Filter to kept sites
        df_deduped = df.iloc[keep_indices].reset_index(drop=True)
        
        logger.info(f"Removed {removed_count} duplicate sites")
        
        return df_deduped
    
    def add_synthetic_sites(
        self,
        existing_df: Optional[pd.DataFrame],
        aoi_bbox: Tuple[float, float, float, float],
        num_sites: int = 30,
        pattern: str = 'mixed',
        confidence_range: Tuple[float, float] = (60, 90)
    ) -> pd.DataFrame:
        """
        Add synthetic sites to existing dataset (or create new).
        
        Args:
            existing_df: Existing DataFrame (can be None)
            aoi_bbox: Bounding box for synthetic sites
            num_sites: Number of synthetic sites
            pattern: Pattern type ('grid', 'organic', 'axial', 'random', 'mixed')
            confidence_range: Confidence range for synthetic sites
        
        Returns:
            Combined DataFrame with synthetic sites added
        """
        logger.info(f"Generating {num_sites} synthetic sites with pattern: {pattern}")
        
        # Generate synthetic sites
        synthetic_df = self.synthetic_generator.generate(
            aoi_bbox=aoi_bbox,
            pattern=pattern,
            num_sites=num_sites,
            confidence_range=confidence_range
        )
        
        # Add source tag
        synthetic_df['source'] = 'synthetic'
        
        # Combine with existing data if provided
        if existing_df is not None and not existing_df.empty:
            sources = {
                'existing': existing_df,
                'synthetic': synthetic_df
            }
            combined = self.combine_sources(sources, aoi_bbox=aoi_bbox)
        else:
            combined = synthetic_df
        
        logger.info(f"✓ Added synthetic sites (total: {len(combined)})")
        return combined
    
    def get_source_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Get statistics about data sources in combined dataset.
        
        Args:
            df: Combined DataFrame with 'source' column
        
        Returns:
            Dictionary with source statistics
        """
        if 'source' not in df.columns:
            return {'error': 'No source column in DataFrame'}
        
        stats = {
            'total_sites': len(df),
            'sources': {},
            'priority_distribution': df['priority'].value_counts().to_dict(),
            'site_type_distribution': df['site_type'].value_counts().to_dict() if 'site_type' in df.columns else {},
            'confidence_stats': {
                'mean': float(df['confidence'].mean()),
                'min': float(df['confidence'].min()),
                'max': float(df['confidence'].max()),
                'std': float(df['confidence'].std())
            }
        }
        
        # Per-source statistics
        for source in df['source'].unique():
            source_df = df[df['source'] == source]
            stats['sources'][source] = {
                'count': len(source_df),
                'percentage': round(len(source_df) / len(df) * 100, 1),
                'avg_confidence': round(float(source_df['confidence'].mean()), 1),
                'priority_high': int((source_df['priority'] == 'high').sum()),
                'priority_medium': int((source_df['priority'] == 'medium').sum()),
                'priority_low': int((source_df['priority'] == 'low').sum())
            }
        
        return stats
    
    def create_demo_dataset(
        self,
        aoi_bbox: Tuple[float, float, float, float],
        total_sites: int = 100
    ) -> Dict:
        """
        Create a complete demo dataset with mixed sources.
        
        Args:
            aoi_bbox: Bounding box
            total_sites: Target number of total sites
        
        Returns:
            Dictionary with 'data' (DataFrame) and 'metadata' (dict)
        """
        logger.info(f"Creating demo dataset with ~{total_sites} sites...")
        
        # Split sites between patterns
        grid_sites = int(total_sites * 0.3)
        organic_sites = int(total_sites * 0.4)
        random_sites = total_sites - grid_sites - organic_sites
        
        # Generate each pattern
        grid_df = self.synthetic_generator.generate(
            aoi_bbox=aoi_bbox,
            pattern='grid',
            num_sites=grid_sites,
            confidence_range=(70, 95)
        )
        grid_df['source'] = 'synthetic_grid'
        
        organic_df = self.synthetic_generator.generate(
            aoi_bbox=aoi_bbox,
            pattern='organic',
            num_sites=organic_sites,
            confidence_range=(60, 90)
        )
        organic_df['source'] = 'synthetic_organic'
        
        random_df = self.synthetic_generator.generate(
            aoi_bbox=aoi_bbox,
            pattern='random',
            num_sites=random_sites,
            confidence_range=(55, 85)
        )
        random_df['source'] = 'synthetic_random'
        
        # Combine all
        sources = {
            'synthetic_grid': grid_df,
            'synthetic_organic': organic_df,
            'synthetic_random': random_df
        }
        
        combined = self.combine_sources(sources, aoi_bbox=aoi_bbox)
        
        # Get statistics
        stats = self.get_source_statistics(combined)
        
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'aoi_bbox': aoi_bbox,
            'target_sites': total_sites,
            'actual_sites': len(combined),
            'statistics': stats
        }
        
        logger.info(f"✓ Demo dataset created: {len(combined)} sites from {len(sources)} sources")
        
        return {
            'data': combined,
            'metadata': metadata
        }


def quick_hybrid_test() -> pd.DataFrame:
    """
    Quick test function for hybrid data service.
    
    Returns:
        Combined DataFrame
    """
    # Riyadh AOI
    riyadh_bbox = (46.5, 24.5, 46.9, 24.9)
    
    service = HybridDataService()
    result = service.create_demo_dataset(
        aoi_bbox=riyadh_bbox,
        total_sites=50
    )
    
    df = result['data']
    metadata = result['metadata']
    
    logger.info(f"Quick test created {len(df)} sites")
    logger.info(f"Sources: {list(metadata['statistics']['sources'].keys())}")
    logger.info(f"Priority distribution: {metadata['statistics']['priority_distribution']}")
    
    return df
