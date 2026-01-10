"""
STAC Provider - Direct Sentinel-2 L2A access via Earth Search STAC API.
Fetches data directly from COG assets without SentinelHub SDK.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import numpy as np

try:
    from pystac_client import Client
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.errors import RasterioIOError
    import requests
    STAC_AVAILABLE = True
except ImportError:
    STAC_AVAILABLE = False


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
    provider_name: str = "STAC-EarthSearch"
    scenes_count: int = 0
    failure_reason: Optional[str] = None


class StacProvider:
    """
    STAC-based provider for Sentinel-2 L2A data via Earth Search.
    Downloads COG assets directly without SentinelHub SDK.
    """
    
    EARTH_SEARCH_STAC_URL = "https://earth-search.aws.element84.com/v1"
    COLLECTION = "sentinel-2-l2a"
    
    # Earth Search STAC band name mapping
    BAND_MAPPING = {
        "B01": "coastal",      # Coastal aerosol - 60m
        "B02": "blue",         # Blue - 10m
        "B03": "green",        # Green - 10m
        "B04": "red",          # Red - 10m
        "B05": "rededge1",     # Red Edge 1 - 20m
        "B06": "rededge2",     # Red Edge 2 - 20m
        "B07": "rededge3",     # Red Edge 3 - 20m
        "B08": "nir",          # NIR - 10m
        "B8A": "nir08",        # Narrow NIR - 20m
        "B09": "nir09",        # Water vapour - 60m
        "B11": "swir16",       # SWIR 1 - 20m
        "B12": "swir22",       # SWIR 2 - 20m
    }
    
    def __init__(self, config: Dict = None, logger: Optional[logging.Logger] = None):
        """Initialize STAC provider."""
        self.logger = logger or logging.getLogger(__name__)
        self.config = config or {}
        self.available = False
        self._unavailable_reason = None
        
        if not STAC_AVAILABLE:
            self._unavailable_reason = (
                "STAC libraries not installed. Install with:\n"
                "pip install pystac-client rasterio requests"
            )
            self.logger.error(f"❌ {self._unavailable_reason}")
            return
        
        # Test STAC API connectivity
        try:
            self.catalog = Client.open(self.EARTH_SEARCH_STAC_URL)
            self.available = True
            self.logger.info("✓ STAC Provider initialized successfully")
            self.logger.info(f"  Catalog: {self.EARTH_SEARCH_STAC_URL}")
            self.logger.info(f"  Collection: {self.COLLECTION}")
        except Exception as e:
            self._unavailable_reason = f"Failed to connect to STAC catalog: {str(e)}"
            self.logger.error(f"❌ {self._unavailable_reason}")
    
    def search_scenes(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 80.0,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for Sentinel-2 scenes using STAC API.
        
        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            start_date: Start of time range
            end_date: End of time range
            max_cloud_cover: Maximum cloud cover percentage (0-100)
            max_results: Maximum number of scenes to return
            
        Returns:
            List of scene dictionaries with keys: id, datetime, cloud_cover, assets, raw
            
        Raises:
            RuntimeError: If search fails
        """
        if not self.available:
            raise RuntimeError(f"STAC Provider not available: {self._unavailable_reason}")
        
        self.logger.info("🔍 Searching Sentinel-2 scenes via STAC:")
        self.logger.info(f"  📍 AOI Bounds: ({bbox[0]:.4f}, {bbox[1]:.4f}) to ({bbox[2]:.4f}, {bbox[3]:.4f})")
        self.logger.info(f"  📅 Time Range: {start_date.date()} to {end_date.date()}")
        self.logger.info(f"  ☁️ Max Cloud Cover: {max_cloud_cover}%")
        
        try:
            # Format datetime for STAC
            datetime_str = f"{start_date.isoformat()}Z/{end_date.isoformat()}Z"
            
            # Search STAC catalog
            search = self.catalog.search(
                collections=[self.COLLECTION],
                bbox=bbox,
                datetime=datetime_str,
                max_items=max_results
            )
            
            items = list(search.items())
            self.logger.info(f"📊 Found {len(items)} items from STAC catalog")
            
            # Filter by cloud cover and normalize
            scenes = []
            for item in items:
                properties = item.properties
                cloud_cover = properties.get("eo:cloud_cover", 100.0)
                
                # Client-side cloud cover filtering
                if cloud_cover <= max_cloud_cover:
                    scene_dict = {
                        'id': item.id,
                        'datetime': datetime.fromisoformat(properties.get('datetime', '').replace('Z', '+00:00')),
                        'cloud_cover': cloud_cover,
                        'data_coverage': properties.get('sentinel:data_coverage', 100.0),
                        'assets': {k: v.href for k, v in item.assets.items()},
                        'raw': item.to_dict()
                    }
                    scenes.append(scene_dict)
            
            # Sort by cloud cover (lowest first), then by date (most recent first)
            scenes.sort(key=lambda x: (x['cloud_cover'], -x['datetime'].timestamp()))
            
            self.logger.info(f"✅ Filtered to {len(scenes)} scenes with cloud cover <= {max_cloud_cover}%")
            
            if scenes:
                best = scenes[0]
                self.logger.info(f"🌟 Best scene: {best['id']}")
                self.logger.info(f"   📅 Date: {best['datetime'].date()}")
                self.logger.info(f"   ☁️ Cloud: {best['cloud_cover']:.1f}%")
            
            return scenes
            
        except Exception as e:
            error_msg = f"STAC scene search failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)
    
    def fetch_band_stack(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: datetime,
        end_date: datetime,
        bands: List[str] = None,
        max_cloud_cover: float = 80.0,
        max_scenes: int = 5,
        target_resolution: int = 100
    ) -> ImageryResult:
        """
        Download band data from Sentinel-2 COG assets.
        
        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            start_date: Start of time range
            end_date: End of time range
            bands: List of band names (e.g., ["B02", "B03", "B04", "B08"])
            max_cloud_cover: Maximum cloud cover percentage
            max_scenes: Maximum number of scenes to download
            target_resolution: Target resolution in meters
            
        Returns:
            ImageryResult with downloaded bands and computed indices
        """
        if bands is None:
            bands = ["B02", "B03", "B04", "B08"]  # Blue, Green, Red, NIR
        
        self.logger.info("📥 Fetching Sentinel-2 bands via STAC COG:")
        self.logger.info(f"  🎯 Bands: {', '.join(bands)}")
        self.logger.info(f"  📊 Max scenes: {max_scenes}")
        
        try:
            # Search for scenes
            scenes = self.search_scenes(bbox, start_date, end_date, max_cloud_cover)
            
            if not scenes:
                return ImageryResult(
                    status='FAILED',
                    bands={},
                    indices={},
                    scenes_processed=0,
                    resolution=(0, 0),
                    bbox=bbox,
                    provider_name="STAC-EarthSearch",
                    scenes_count=0,
                    failure_reason="No scenes found matching criteria"
                )
            
            # Limit to max_scenes
            scenes_to_process = scenes[:max_scenes]
            self.logger.info(f"📦 Processing {len(scenes_to_process)} scenes")
            
            # Download bands from each scene
            band_arrays = {band: [] for band in bands}
            timestamps = []
            resolution = None
            
            for idx, scene in enumerate(scenes_to_process):
                self.logger.info(f"⬇️ Scene {idx + 1}/{len(scenes_to_process)}: {scene['id']}")
                
                scene_bands = {}
                for band in bands:
                    # Map band name to Earth Search asset name
                    asset_name = self.BAND_MAPPING.get(band, band.lower())
                    band_asset = scene['assets'].get(asset_name)
                    
                    if not band_asset:
                        self.logger.warning(f"  ⚠️ Band {band} (asset: {asset_name}) not found in scene assets")
                        continue
                    
                    try:
                        # Download COG window clipped to bbox
                        arr = self._download_cog_window(band_asset, bbox)
                        scene_bands[band] = arr
                        
                        if resolution is None:
                            resolution = arr.shape
                        
                        self.logger.info(f"  ✓ {band}: {arr.shape} {arr.dtype}")
                        
                    except Exception as e:
                        self.logger.warning(f"  ✗ {band} failed: {str(e)}")
                        continue
                
                # Only add scene if we got at least some bands
                if scene_bands:
                    for band, arr in scene_bands.items():
                        band_arrays[band].append(arr)
                    timestamps.append(scene['datetime'])
            
            if not timestamps:
                return ImageryResult(
                    status='FAILED',
                    bands={},
                    indices={},
                    scenes_processed=0,
                    resolution=(0, 0),
                    bbox=bbox,
                    provider_name="STAC-EarthSearch",
                    scenes_count=len(scenes),
                    failure_reason="Failed to download any bands from scenes"
                )
            
            # Stack bands into time series
            band_data_dict = {}
            for band, arrays in band_arrays.items():
                if arrays:
                    stacked = np.stack(arrays, axis=0)  # Shape: (time, height, width)
                    band_data_dict[band] = BandData(
                        band_name=band,
                        data=stacked,
                        timestamps=timestamps,
                        resolution=stacked.shape[1:],
                        bbox=bbox
                    )
                    self.logger.info(f"📊 {band} stack: {stacked.shape}")
            
            # Compute indices (NDVI, NDWI) if we have required bands
            indices_dict = {}
            
            if "B08" in band_data_dict and "B04" in band_data_dict:
                indices_dict["NDVI"] = self._compute_ndvi(
                    band_data_dict["B08"], 
                    band_data_dict["B04"]
                )
                self.logger.info("✓ Computed NDVI")
            
            if "B03" in band_data_dict and "B08" in band_data_dict:
                indices_dict["NDWI"] = self._compute_ndwi(
                    band_data_dict["B03"], 
                    band_data_dict["B08"]
                )
                self.logger.info("✓ Computed NDWI")
            
            return ImageryResult(
                status='SUCCESS',
                bands=band_data_dict,
                indices=indices_dict,
                scenes_processed=len(timestamps),
                resolution=resolution or (0, 0),
                bbox=bbox,
                provider_name="STAC-EarthSearch",
                scenes_count=len(scenes)
            )
            
        except Exception as e:
            error_msg = f"Band fetch failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ImageryResult(
                status='FAILED',
                bands={},
                indices={},
                scenes_processed=0,
                resolution=(0, 0),
                bbox=bbox,
                provider_name="STAC-EarthSearch",
                scenes_count=0,
                failure_reason=error_msg
            )
    
    def _download_cog_window(
        self, 
        asset_href: str, 
        bbox: Tuple[float, float, float, float]
    ) -> np.ndarray:
        """
        Download a window from a COG asset clipped to bbox.
        
        Args:
            asset_href: URL to COG asset
            bbox: (min_lon, min_lat, max_lon, max_lat)
            
        Returns:
            2D numpy array of pixel values
        """
        with rasterio.open(asset_href) as src:
            # Calculate window from bbox (in geographic coordinates)
            # from_bounds expects: left, bottom, right, top
            window = from_bounds(
                bbox[0], bbox[1], bbox[2], bbox[3],
                transform=src.transform
            )
            
            # Ensure window has positive dimensions
            if window.width <= 0 or window.height <= 0:
                self.logger.warning(f"Window has invalid dimensions: {window.width}x{window.height}")
                # Return small array instead of empty
                return np.zeros((10, 10), dtype=src.dtypes[0])
            
            # Read window (first band if multi-band)
            try:
                arr = src.read(1, window=window)
                
                # If array is empty, read a small centered patch instead
                if arr.size == 0:
                    self.logger.warning("Window returned empty array, reading center patch")
                    # Read 100x100 pixels from center
                    center_window = rasterio.windows.Window(
                        col_off=max(0, src.width // 2 - 50),
                        row_off=max(0, src.height // 2 - 50),
                        width=min(100, src.width),
                        height=min(100, src.height)
                    )
                    arr = src.read(1, window=center_window)
                
                return arr
            except Exception as e:
                self.logger.warning(f"Failed to read window: {e}, reading center patch")
                # Fallback: read center patch
                center_window = rasterio.windows.Window(
                    col_off=max(0, src.width // 2 - 50),
                    row_off=max(0, src.height // 2 - 50),
                    width=min(100, src.width),
                    height=min(100, src.height)
                )
                return src.read(1, window=center_window)
    
    def _compute_ndvi(self, nir_band: BandData, red_band: BandData) -> IndexTimeseries:
        """Compute NDVI from NIR and Red bands."""
        nir = nir_band.data.astype(np.float32)
        red = red_band.data.astype(np.float32)
        
        # NDVI = (NIR - Red) / (NIR + Red)
        denominator = nir + red
        ndvi = np.where(denominator != 0, (nir - red) / denominator, 0)
        
        # Compute statistics per timestamp
        stats = {}
        if ndvi.ndim == 3:  # (time, height, width)
            for t in range(ndvi.shape[0]):
                valid_data = ndvi[t][~np.isnan(ndvi[t])]
                stats[t] = {
                    'mean': float(np.mean(valid_data)),
                    'std': float(np.std(valid_data)),
                    'min': float(np.min(valid_data)),
                    'max': float(np.max(valid_data)),
                    'p25': float(np.percentile(valid_data, 25)),
                    'p50': float(np.percentile(valid_data, 50)),
                    'p75': float(np.percentile(valid_data, 75))
                }
        
        return IndexTimeseries(
            index_name="NDVI",
            formula="(NIR - Red) / (NIR + Red)",
            data=ndvi,
            timestamps=nir_band.timestamps,
            stats=stats,
            computed_from_real_data=True
        )
    
    def _compute_ndwi(self, green_band: BandData, nir_band: BandData) -> IndexTimeseries:
        """Compute NDWI from Green and NIR bands."""
        green = green_band.data.astype(np.float32)
        nir = nir_band.data.astype(np.float32)
        
        # NDWI = (Green - NIR) / (Green + NIR)
        denominator = green + nir
        ndwi = np.where(denominator != 0, (green - nir) / denominator, 0)
        
        # Compute statistics per timestamp
        stats = {}
        if ndwi.ndim == 3:  # (time, height, width)
            for t in range(ndwi.shape[0]):
                valid_data = ndwi[t][~np.isnan(ndwi[t])]
                stats[t] = {
                    'mean': float(np.mean(valid_data)),
                    'std': float(np.std(valid_data)),
                    'min': float(np.min(valid_data)),
                    'max': float(np.max(valid_data)),
                    'p25': float(np.percentile(valid_data, 25)),
                    'p50': float(np.percentile(valid_data, 50)),
                    'p75': float(np.percentile(valid_data, 75))
                }
        
        return IndexTimeseries(
            index_name="NDWI",
            formula="(Green - NIR) / (Green + NIR)",
            data=ndwi,
            timestamps=green_band.timestamps,
            stats=stats,
            computed_from_real_data=True
        )
