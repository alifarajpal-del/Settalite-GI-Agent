"""
PROMPT 4: Google Earth Engine Provider (Safe Mode - No Crash)
Provides GEE integration when authenticated, fails gracefully otherwise.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import os

# Try to import Earth Engine
try:
    import ee
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False
    ee = None


@dataclass
class GEEResult:
    """Result from GEE operation."""
    status: str  # 'GEE_OK', 'GEE_FAILED', 'GEE_UNAVAILABLE'
    data: Optional[Any] = None
    tile_url: Optional[str] = None
    stats: Dict[str, Any] = None
    failure_reason: Optional[str] = None


class GoogleEarthEngineProvider:
    """
    PROMPT 4: Safe GEE provider that doesn't crash app if unavailable.
    
    Key features:
    - is_available() checks authentication without crashing
    - All methods return GEEResult with clear status
    - UI can show GEE status and guide user if needed
    """
    
    def __init__(self, config: Dict, logger: Optional[logging.Logger] = None):
        """Initialize GEE provider (safe - no crash if unavailable)."""
        self.logger = logger or logging.getLogger(__name__)
        self.config = config
        self.available = False
        self.failure_reason = None
        
        if not GEE_AVAILABLE:
            self.failure_reason = "earthengine-api not installed (pip install earthengine-api)"
            self.logger.info(f"GEE unavailable: {self.failure_reason}")
            return
        
        # Try to initialize
        try:
            # Check if already initialized
            try:
                ee.Number(1).getInfo()  # Test call
                self.available = True
                self.logger.info("✓ GEE already initialized")
                return
            except Exception:
                pass  # Not initialized yet
            
            # Try to initialize with credentials
            project_id = config.get('gee', {}).get('project_id') or os.getenv('GEE_PROJECT_ID')
            
            if project_id:
                # Try service account or high volume endpoint
                try:
                    ee.Initialize(project=project_id)
                    self.available = True
                    self.logger.info(f"✓ GEE initialized with project: {project_id}")
                    return
                except Exception as e:
                    self.logger.debug(f"GEE project init failed: {e}")
            
            # Try default initialization (for local authenticated users)
            try:
                ee.Initialize()
                self.available = True
                self.logger.info("✓ GEE initialized (default auth)")
                return
            except Exception as e:
                self.failure_reason = "Authentication required: run 'earthengine authenticate' locally"
                self.logger.info(f"GEE unavailable: {self.failure_reason}")
                
        except Exception as e:
            self.failure_reason = f"Initialization error: {str(e)}"
            self.logger.warning(f"GEE unavailable: {self.failure_reason}")
    
    def is_available(self) -> bool:
        """Check if GEE is available for use."""
        return self.available
    
    def get_availability_message(self) -> str:
        """Get user-friendly availability message."""
        if self.available:
            return "✓ Google Earth Engine is available"
        else:
            return f"✗ GEE unavailable: {self.failure_reason}"
    
    def get_s2_ndvi_composite(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 20.0
    ) -> GEEResult:
        """
        Get Sentinel-2 NDVI composite as tile URL for visualization.
        
        Args:
            bbox: (minx, miny, maxx, maxy)
            start_date: Start of time range
            end_date: End of time range
            max_cloud_cover: Maximum cloud cover
            
        Returns:
            GEEResult with tile_url for display
        """
        if not self.available:
            return GEEResult(
                status='GEE_UNAVAILABLE',
                failure_reason=self.failure_reason
            )
        
        try:
            # Create geometry
            geometry = ee.Geometry.Rectangle([bbox[0], bbox[1], bbox[2], bbox[3]])
            
            # Load Sentinel-2 collection
            s2 = (ee.ImageCollection(self.S2_COLLECTION)
                .filterBounds(geometry)
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', max_cloud_cover)))
            
            # Compute NDVI
            def add_ndvi(image):
                ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                return image.addBands(ndvi)
            
            s2_ndvi = s2.map(add_ndvi)
            
            # Get median composite
            ndvi_composite = s2_ndvi.select('NDVI').median().clip(geometry)
            
            # Get tile URL
            vis_params = {
                'min': -0.2,
                'max': 0.8,
                'palette': ['red', 'yellow', 'green']
            }
            
            tile_url = ndvi_composite.getMapId(vis_params)['tile_fetcher'].url_format
            
            self.logger.info("✓ GEE NDVI composite generated")
            
            return GEEResult(
                status='GEE_OK',
                tile_url=tile_url,
                data={'collection_size': s2.size().getInfo()}
            )
            
        except Exception as e:
            self.logger.error(f"GEE composite failed: {e}")
            return GEEResult(
                status='GEE_FAILED',
                failure_reason=str(e)
            )
    
    def get_ndvi_timeseries(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 20.0
    ) -> GEEResult:
        """
        Get NDVI statistics over time (mean per image date).
        
        Returns:
            GEEResult with stats dict containing timeseries data
        """
        if not self.available:
            return GEEResult(
                status='GEE_UNAVAILABLE',
                failure_reason=self.failure_reason
            )
        
        try:
            # Create geometry
            geometry = ee.Geometry.Rectangle([bbox[0], bbox[1], bbox[2], bbox[3]])
            
            # Load Sentinel-2
            s2 = (ee.ImageCollection(self.S2_COLLECTION)
                .filterBounds(geometry)
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', max_cloud_cover)))
            
            # Compute NDVI per image
            def add_ndvi_stats(image):
                ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                stats = ndvi.reduceRegion(
                    reducer=ee.Reducer.mean().combine(
                        ee.Reducer.stdDev(), '', True
                    ).combine(
                        ee.Reducer.minMax(), '', True
                    ),
                    geometry=geometry,
                    scale=10,
                    maxPixels=1e9
                )
                
                return ee.Feature(None, {
                    'date': image.date().format('YYYY-MM-dd'),
                    'mean': stats.get('NDVI_mean'),
                    'std': stats.get('NDVI_stdDev'),
                    'min': stats.get('NDVI_min'),
                    'max': stats.get('NDVI_max')
                })
            
            # Get timeseries
            timeseries = s2.map(add_ndvi_stats).getInfo()
            
            # Extract features
            stats_list = []
            for feature in timeseries['features']:
                props = feature['properties']
                if props.get('mean') is not None:
                    stats_list.append({
                        'date': props['date'],
                        'mean': float(props['mean']),
                        'std': float(props.get('std', 0)),
                        'min': float(props.get('min', 0)),
                        'max': float(props.get('max', 0))
                    })
            
            self.logger.info(f"✓ GEE timeseries computed ({len(stats_list)} dates)")
            
            return GEEResult(
                status='GEE_OK',
                stats={
                    'timeseries': stats_list,
                    'count': len(stats_list)
                }
            )
            
        except Exception as e:
            self.logger.error(f"GEE timeseries failed: {e}")
            return GEEResult(
                status='GEE_FAILED',
                failure_reason=str(e)
            )
    
    def get_multi_temporal_variance(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: datetime,
        end_date: datetime,
        index_name: str = 'NDVI'
    ) -> GEEResult:
        """
        Compute multi-temporal variance of an index.
        High variance may indicate changes (including archaeological features).
        
        Returns:
            GEEResult with variance statistics
        """
        if not self.available:
            return GEEResult(
                status='GEE_UNAVAILABLE',
                failure_reason=self.failure_reason
            )
        
        try:
            geometry = ee.Geometry.Rectangle([bbox[0], bbox[1], bbox[2], bbox[3]])
            
            # Load collection
            s2 = (ee.ImageCollection(self.S2_COLLECTION)
                .filterBounds(geometry)
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))
            
            # Compute index
            if index_name == 'NDVI':
                def add_index(img):
                    return img.normalizedDifference(['B8', 'B4']).rename('INDEX')
            elif index_name == 'NDWI':
                def add_index(img):
                    return img.normalizedDifference(['B3', 'B8']).rename('INDEX')
            else:
                raise ValueError(f"Unknown index: {index_name}")
            
            indices = s2.map(add_index)
            
            # Compute variance
            variance = indices.select('INDEX').reduce(ee.Reducer.variance())
            
            # Get stats
            stats = variance.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), '', True
                ).combine(
                    ee.Reducer.percentile([25, 50, 75]), '', True
                ),
                geometry=geometry,
                scale=10,
                maxPixels=1e9
            ).getInfo()
            
            self.logger.info(f"✓ GEE variance computed for {index_name}")
            
            return GEEResult(
                status='GEE_OK',
                stats={
                    'index': index_name,
                    'variance_mean': stats.get('INDEX_variance_mean'),
                    'variance_std': stats.get('INDEX_variance_stdDev'),
                    'variance_p50': stats.get('INDEX_variance_p50')
                }
            )
            
        except Exception as e:
            self.logger.error(f"GEE variance failed: {e}")
            return GEEResult(
                status='GEE_FAILED',
                failure_reason=str(e)
            )
