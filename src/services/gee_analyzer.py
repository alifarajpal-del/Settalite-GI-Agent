"""
Google Earth Engine Analyzer - Multi-temporal indicator analysis.
PROMPT 3B Implementation: Time-series anomaly detection with persistence scoring.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import os

try:
    import ee
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False


@dataclass
class IndicatorTimeSeries:
    """Time series data for a specific indicator."""
    name: str  # 'NDVI', 'NDWI', 'SAR_VV', etc.
    timestamps: List[datetime]
    values: List[float]
    anomaly_count: int
    persistence_score: float  # 0-1, ratio of anomalous observations
    seasonal_consistency: bool


@dataclass
class GEEResult:
    """Result from Google Earth Engine analysis."""
    status: str  # 'GEE_OK' or 'GEE_FAILED'
    indicators: List[IndicatorTimeSeries]
    overlay_tiles: Dict[str, str]  # indicator_name -> tile_url
    quality_flags: Dict[str, bool]  # coverage_ok, temporal_ok, etc.
    failure_reason: Optional[str] = None


class GoogleEarthEngineAnalyzer:
    """
    Multi-temporal analysis using Google Earth Engine.
    
    PROMPT 3B: Persistence-based anomaly detection
    - NDVI time-series + anomaly persistence
    - NDWI/moisture proxy
    - Optional: Sentinel-1 SAR
    - No single-image reliance
    """
    
    def __init__(self, config: Dict, logger: Optional[logging.Logger] = None):
        """
        Initialize GEE analyzer.
        
        Args:
            config: Must contain gee.project_id for Earth Engine
            logger: Optional logger
        """
        self.logger = logger or logging.getLogger(__name__)
        self.available = False
        self.config = config
        
        if not GEE_AVAILABLE:
            self.logger.warning("Earth Engine library not available - install with: pip install earthengine-api")
            return
        
        # Get project ID from config
        self.project_id = config.get('gee', {}).get('project_id')
        if not self.project_id:
            self.logger.warning("GEE project_id not configured")
            return
        
        # Try to initialize Earth Engine
        try:
            # Check if already initialized
            try:
                ee.Number(1).getInfo()
                self.available = True
                self.logger.info(f"✓ Earth Engine already authenticated (project: {self.project_id})")
                return
            except:
                pass
            
            # Try service account authentication (from secrets)
            service_account_json = config.get('gee', {}).get('service_account_json')
            if service_account_json:
                import json
                credentials_dict = json.loads(service_account_json)
                credentials = ee.ServiceAccountCredentials(
                    credentials_dict['client_email'],
                    key_data=service_account_json
                )
                ee.Initialize(credentials, project=self.project_id)
                self.available = True
                self.logger.info(f"✓ Earth Engine initialized with service account (project: {self.project_id})")
                return
            
            # Try service account key file
            service_account_key = config.get('gee', {}).get('service_account_key')
            if service_account_key and os.path.exists(service_account_key):
                credentials = ee.ServiceAccountCredentials(None, service_account_key)
                ee.Initialize(credentials, project=self.project_id)
                self.available = True
                self.logger.info(f"✓ Earth Engine initialized with service account file (project: {self.project_id})")
                return
                ee.Initialize(credentials)
                self.available = True
                self.logger.info("✓ Earth Engine initialized with service account")
                return
            
            # Try default authentication (works on local dev)
            try:
                ee.Initialize(project=self.project_id)
                self.available = True
                self.logger.info(f"✓ Earth Engine initialized with default credentials (project: {self.project_id})")
            except Exception as e:
                self.logger.warning(f"Earth Engine authentication failed: {e}")
                self.logger.warning("Run 'earthengine authenticate' locally or provide service_account_json in secrets")
                self.available = False
                
        except Exception as e:
            self.logger.error(f"Earth Engine initialization failed: {e}")
            self.available = False
    
    def analyze_multitemporal(
        self,
        bbox: Tuple[float, float, float, float],  # (minx, miny, maxx, maxy)
        start_date: datetime,
        end_date: datetime,
        min_images: int = 5
    ) -> GEEResult:
        """
        Multi-temporal analysis of vegetation and moisture anomalies.
        
        Args:
            bbox: Bounding box in WGS84
            start_date: Start date
            end_date: End date
            min_images: Minimum images required for temporal analysis
            
        Returns:
            GEEResult with indicators or failure reason
        """
        if not self.available:
            return GEEResult(
                status='GEE_FAILED',
                indicators=[],
                overlay_tiles={},
                quality_flags={'gee_available': False},
                failure_reason='GEE_UNAVAILABLE: Library not installed or not authenticated'
            )
        
        try:
            # Create AOI geometry
            minx, miny, maxx, maxy = bbox
            aoi = ee.Geometry.Rectangle([minx, miny, maxx, maxy])
            
            # Query Sentinel-2 collection
            s2_collection = (
                ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(aoi)
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            )
            
            # Check image count
            image_count = s2_collection.size().getInfo()
            self.logger.info(f"Found {image_count} Sentinel-2 images in GEE")
            
            if image_count < min_images:
                return GEEResult(
                    status='GEE_FAILED',
                    indicators=[],
                    overlay_tiles={},
                    quality_flags={'temporal_coverage': False},
                    failure_reason=f'INSUFFICIENT_COVERAGE: Only {image_count} images found (minimum {min_images})'
                )
            
            # TODO: Implement actual multi-temporal analysis
            # For now, return partial result
            return GEEResult(
                status='GEE_OK',
                indicators=[],
                overlay_tiles={},
                quality_flags={'temporal_coverage': True, 'analysis_pending': True},
                failure_reason=None
            )
            
        except Exception as e:
            self.logger.error(f"GEE analysis failed: {e}")
            return GEEResult(
                status='GEE_FAILED',
                indicators=[],
                overlay_tiles={},
                quality_flags={},
                failure_reason=f'ANALYSIS_ERROR: {str(e)}'
            )
    
    def compute_ndvi_persistence(self, collection, aoi, threshold: float = 0.15) -> IndicatorTimeSeries:
        """
        Compute NDVI anomaly persistence over time.
        
        Args:
            collection: Earth Engine ImageCollection
            aoi: Area of interest geometry
            threshold: Anomaly threshold (deviation from local mean)
            
        Returns:
            IndicatorTimeSeries with persistence metrics
        """
        # TODO: Implement NDVI time-series analysis
        # - Compute NDVI for each image
        # - Calculate local mean/std
        # - Detect anomalies (values > mean + threshold*std)
        # - Compute persistence (ratio of anomalous observations)
        pass
    
    def test_connection(self) -> bool:
        """Test if GEE connection works."""
        if not self.available:
            return False
        
        try:
            # Simple test: get image count from a known collection
            ee.Number(1).getInfo()
            return True
        except Exception as e:
            self.logger.error(f"GEE connection test failed: {e}")
            return False
