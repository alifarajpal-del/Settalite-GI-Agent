"""
PROMPT 3: Real Sentinel Hub Provider - Band Download + Multi-Temporal Indices
Implements actual imagery download and NDVI/NDWI computation.
"""

import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import numpy as np
from pathlib import Path

try:
    from sentinelhub import (
        SHConfig, 
        BBox, 
        CRS, 
        DataCollection,
        SentinelHubRequest,
        SentinelHubCatalog,
        MimeType,
        bbox_to_dimensions
    )
    SENTINELHUB_AVAILABLE = True
except ImportError:
    SENTINELHUB_AVAILABLE = False


@dataclass
class BandData:
    """Container for downloaded band data."""
    band_name: str
    data: np.ndarray  # Shape: (height, width) or (time, height, width)
    timestamps: List[datetime]
    resolution: Tuple[int, int]
    bbox: Tuple[float, float, float, float]


@dataclass
class IndexTimeseries:
    """Multi-temporal index (NDVI/NDWI) with statistics."""
    index_name: str
    formula: str
    data: np.ndarray  # Shape: (time, height, width)
    timestamps: List[datetime]
    stats: Dict[str, Any]  # mean, std, min, max, percentiles per timestamp
    computed_from_real_data: bool = True


@dataclass
class ImageryResult:
    """Result from imagery download and processing."""
    status: str  # 'SUCCESS' or 'FAILED'
    bands: Dict[str, BandData]  # band_name -> BandData
    indices: Dict[str, IndexTimeseries]  # index_name -> IndexTimeseries
    scenes_processed: int
    resolution: Tuple[int, int]
    bbox: Tuple[float, float, float, float]
    failure_reason: Optional[str] = None


class SentinelHubProvider:
    """
    PROMPT 3: Production-grade Sentinel Hub provider.
    Downloads actual bands and computes multi-temporal indices.
    """
    
    def __init__(self, config: Dict, logger: Optional[logging.Logger] = None):
        """Initialize provider with Sentinel Hub credentials."""
        self.logger = logger or logging.getLogger(__name__)
        self.config_dict = config
        self.available = False
        self._unavailable_reason = None
        
        if not SENTINELHUB_AVAILABLE:
            self._unavailable_reason = "sentinelhub library not installed. Install with: pip install sentinelhub>=3.9.0"
            self.logger.error(f"❌ {self._unavailable_reason}")
            return
        
        # Load credentials
        import os
        client_id = config.get('sentinelhub', {}).get('client_id') or os.getenv('SENTINELHUB_CLIENT_ID')
        client_secret = config.get('sentinelhub', {}).get('client_secret') or os.getenv('SENTINELHUB_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            self._unavailable_reason = (
                "Sentinel Hub credentials not found.\n\n"
                "Required environment variables:\n"
                "- SENTINELHUB_CLIENT_ID\n"
                "- SENTINELHUB_CLIENT_SECRET\n\n"
                "Get free credentials at: https://www.sentinel-hub.com/\n"
                "Then add to Streamlit secrets or .env file"
            )
            self.logger.error(f"❌ {self._unavailable_reason}")
            return
        
        # Configure SentinelHub
        try:
            self.sh_config = SHConfig()
            self.sh_config.sh_client_id = client_id
            self.sh_config.sh_client_secret = client_secret
            
            self.available = True
            self.logger.info("✓ Sentinel Hub provider initialized successfully")
            self.logger.info(f"  Client ID: {client_id[:10]}...")
            self.logger.info(f"  Ready to search and download Sentinel-2 imagery")
        except Exception as e:
            self._unavailable_reason = f"Failed to configure Sentinel Hub: {type(e).__name__}: {e}"
            self.logger.error(f"❌ {self._unavailable_reason}")
            self.available = False
    
    def search_scenes(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 20.0
    ) -> List[Dict[str, Any]]:
        """
        Search for available scenes.
        
        Returns:
            List of scene metadata dicts
        """
        if not self.available:
            self.logger.warning("SentinelHub provider not available - cannot search scenes")
            return []
        
        try:
            sh_bbox = BBox(bbox=bbox, crs=CRS.WGS84)
            catalog = SentinelHubCatalog(config=self.sh_config)
            
            time_interval = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
            # Calculate bbox size
            bbox_width = bbox[2] - bbox[0]
            bbox_height = bbox[3] - bbox[1]
            bbox_area_km2 = bbox_width * bbox_height * 111 * 111  # rough approximation
            
            # Log search parameters
            self.logger.info(f"🔍 Searching Sentinel-2 scenes:")
            self.logger.info(f"  📍 AOI Bounds: ({bbox[0]:.4f}, {bbox[1]:.4f}) to ({bbox[2]:.4f}, {bbox[3]:.4f})")
            self.logger.info(f"  📐 AOI Size: {bbox_width:.4f}° x {bbox_height:.4f}° (~{bbox_area_km2:.0f} km²)")
            self.logger.info(f"  📅 Time Range: {time_interval[0]} to {time_interval[1]}")
            self.logger.info(f"  ☁️ Max Cloud Cover: {max_cloud_cover}%")
            self.logger.info(f"  📡 Collection: SENTINEL2_L2A")
            
            # Warn if bbox is too small or too large
            if bbox_area_km2 < 1:
                self.logger.warning(f"⚠️ AOI is very small ({bbox_area_km2:.2f} km²) - may not cover a full Sentinel-2 tile")
            elif bbox_area_km2 > 50000:
                self.logger.warning(f"⚠️ AOI is very large ({bbox_area_km2:.0f} km²) - search may be slow")
            
            search_iterator = catalog.search(
                DataCollection.SENTINEL2_L2A,
                bbox=sh_bbox,
                time=time_interval,
                filter=f"eo:cloud_cover < {max_cloud_cover}"
            )
            
            scenes = []
            scene_count = 0
            for item in search_iterator:
                scene_count += 1
                cloud_cover = item['properties'].get('eo:cloud_cover', 0)
                scenes.append({
                    'id': item['id'],
                    'datetime': datetime.fromisoformat(item['properties']['datetime'].replace('Z', '+00:00')),
                    'cloud_cover': cloud_cover,
                    'data_coverage': item['properties'].get('s2:data_coverage', 100)
                })
            
            if len(scenes) == 0:
                self.logger.warning(f"⚠️ NO SCENES FOUND with cloud cover < {max_cloud_cover}%")
                self.logger.info(f"Troubleshooting tips:")
                self.logger.info(f"  1. Check if AOI is over land: {bbox}")
                self.logger.info(f"  2. Try longer time range (current: {(end_date - start_date).days} days)")
                self.logger.info(f"  3. Try higher cloud cover (50-80%)")
                self.logger.info(f"  4. Verify location is covered by Sentinel-2")
            else:
                self.logger.info(f"✓ Found {len(scenes)} scenes matching criteria")
                if scenes:
                    avg_cloud = sum(s['cloud_cover'] for s in scenes) / len(scenes)
                    self.logger.info(f"  Average cloud cover: {avg_cloud:.1f}%")
            
            return scenes
            
        except Exception as e:
            self.logger.error(f"Scene search failed: {type(e).__name__}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    @retry(

    
        stop=stop_after_attempt(3),

    
        wait=wait_exponential(multiplier=1, min=4, max=10),

    
        retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),

    
        reraise=True

    
    )

    
    def fetch_band_stack(
        self,
        bbox: Tuple[float, float, float, float],
        time_range: Tuple[datetime, datetime],
        bands: List[str] = ['B04', 'B08'],  # Red, NIR for NDVI
        resolution: int = 10,
        max_cloud_cover: float = 20.0
    ) -> ImageryResult:
        """
        PROMPT 3: Download band stack for multiple dates.
        
        Args:
            bbox: Bounding box (minx, miny, maxx, maxy)
            time_range: (start_date, end_date)
            bands: List of band names to download
            resolution: Resolution in meters
            max_cloud_cover: Maximum cloud cover
            
        Returns:
            ImageryResult with actual band data
        """
        if not self.available:
            return ImageryResult(
                status='FAILED',
                bands={},
                indices={},
                scenes_processed=0,
                resolution=(0, 0),
                bbox=bbox,
                failure_reason='Provider not available'
            )
        
        try:
            # Create bbox and calculate dimensions
            sh_bbox = BBox(bbox=bbox, crs=CRS.WGS84)
            size = bbox_to_dimensions(sh_bbox, resolution=resolution)
            
            # Search scenes first
            scenes = self.search_scenes(bbox, time_range[0], time_range[1], max_cloud_cover)
            
            if len(scenes) == 0:
                return ImageryResult(
                    status='FAILED',
                    bands={},
                    indices={},
                    scenes_processed=0,
                    resolution=(resolution, resolution),
                    bbox=bbox,
                    failure_reason='No scenes found'
                )
            
            # Limit to reasonable number for processing
            scenes = scenes[:10]  # Process up to 10 scenes
            timestamps = [s['datetime'] for s in scenes]
            
            self.logger.info(f"Downloading {len(bands)} bands for {len(scenes)} scenes...")
            
            # Build evalscript for all requested bands
            evalscript = self._build_evalscript(bands)
            
            # Create request
            request = SentinelHubRequest(
                evalscript=evalscript,
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=DataCollection.SENTINEL2_L2A,
                        time_interval=(time_range[0], time_range[1]),
                        maxcc=max_cloud_cover / 100.0
                    )
                ],
                responses=[
                    SentinelHubRequest.output_response('default', MimeType.TIFF)
                ],
                bbox=sh_bbox,
                size=size,
                config=self.sh_config
            )
            
            # Execute request
            self.logger.info("Executing Sentinel Hub request...")
            data = request.get_data()
            
            if not data or len(data) == 0:
                return ImageryResult(
                    status='FAILED',
                    bands={},
                    indices={},
                    scenes_processed=0,
                    resolution=(resolution, resolution),
                    bbox=bbox,
                    failure_reason='No data returned from API'
                )
            
            # Parse response into BandData
            band_dict = {}
            for i, band_name in enumerate(bands):
                # data is list of arrays, extract band
                band_arrays = []
                for img in data:
                    if img.shape[-1] > i:
                        band_arrays.append(img[:, :, i])
                
                if band_arrays:
                    band_stack = np.stack(band_arrays, axis=0)  # (time, height, width)
                    band_dict[band_name] = BandData(
                        band_name=band_name,
                        data=band_stack,
                        timestamps=timestamps[:len(band_arrays)],
                        resolution=(resolution, resolution),
                        bbox=bbox
                    )
            
            self.logger.info(f"✓ Downloaded {len(band_dict)} bands, {len(data)} timesteps")
            
            return ImageryResult(
                status='SUCCESS',
                bands=band_dict,
                indices={},  # Will be computed separately
                scenes_processed=len(data),
                resolution=(resolution, resolution),
                bbox=bbox
            )
            
        except Exception as e:
            self.logger.error(f"Band download failed: {e}")
            return ImageryResult(
                status='FAILED',
                bands={},
                indices={},
                scenes_processed=0,
                resolution=(resolution, resolution),
                bbox=bbox,
                failure_reason=str(e)
            )
    
    def compute_ndvi(self, red_band: BandData, nir_band: BandData) -> IndexTimeseries:
        """
        Compute NDVI from Red and NIR bands.
        
        NDVI = (NIR - Red) / (NIR + Red)
        """
        self.logger.info("Computing NDVI...")
        
        nir = nir_band.data.astype(np.float32)
        red = red_band.data.astype(np.float32)
        
        # Avoid division by zero
        denominator = nir + red
        ndvi = np.where(
            denominator != 0,
            (nir - red) / denominator,
            0
        )
        
        # Compute statistics per timestamp
        stats = self._compute_timeseries_stats(ndvi)
        
        return IndexTimeseries(
            index_name='NDVI',
            formula='(NIR - Red) / (NIR + Red)',
            data=ndvi,
            timestamps=nir_band.timestamps,
            stats=stats,
            computed_from_real_data=True
        )
    
    def compute_ndwi(self, green_band: BandData, nir_band: BandData) -> IndexTimeseries:
        """
        Compute NDWI (McFeeters) from Green and NIR bands.
        
        NDWI = (Green - NIR) / (Green + NIR)
        """
        self.logger.info("Computing NDWI...")
        
        green = green_band.data.astype(np.float32)
        nir = nir_band.data.astype(np.float32)
        
        denominator = green + nir
        ndwi = np.where(
            denominator != 0,
            (green - nir) / denominator,
            0
        )
        
        stats = self._compute_timeseries_stats(ndwi)
        
        return IndexTimeseries(
            index_name='NDWI',
            formula='(Green - NIR) / (Green + NIR)',
            data=ndwi,
            timestamps=green_band.timestamps,
            stats=stats,
            computed_from_real_data=True
        )
    
    def _compute_timeseries_stats(self, data: np.ndarray) -> Dict[str, Any]:
        """Compute statistics for each timestamp in timeseries."""
        stats = {
            'per_timestamp': [],
            'overall': {}
        }
        
        # Stats per timestamp
        for t in range(data.shape[0]):
            frame = data[t]
            valid_data = frame[~np.isnan(frame)]
            
            if len(valid_data) > 0:
                stats['per_timestamp'].append({
                    'mean': float(np.mean(valid_data)),
                    'std': float(np.std(valid_data)),
                    'min': float(np.min(valid_data)),
                    'max': float(np.max(valid_data)),
                    'p25': float(np.percentile(valid_data, 25)),
                    'p50': float(np.percentile(valid_data, 50)),
                    'p75': float(np.percentile(valid_data, 75))
                })
            else:
                stats['per_timestamp'].append({})
        
        # Overall stats
        valid_data = data[~np.isnan(data)]
        if len(valid_data) > 0:
            stats['overall'] = {
                'mean': float(np.mean(valid_data)),
                'std': float(np.std(valid_data)),
                'min': float(np.min(valid_data)),
                'max': float(np.max(valid_data)),
                'variance': float(np.var(valid_data))
            }
        
        return stats
    
    def _build_evalscript(self, bands: List[str]) -> str:
        """Build evalscript for Sentinel Hub request."""
        # Map band names to outputs
        band_outputs = ','.join([f'sample.{b}' for b in bands])
        
        evalscript = f"""
        //VERSION=3
        function setup() {{
            return {{
                input: [{{"bands": {bands}}}],
                output: {{
                    bands: {len(bands)},
                    sampleType: "FLOAT32"
                }}
            }};
        }}
        
        function evaluatePixel(sample) {{
            return [{band_outputs}];
        }}
        """
        
        return evalscript
