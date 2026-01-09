"""
Heritage Sentinel Pro - Core Pipeline Orchestration Service

This service unifies all scattered services into a robust, linear pipeline.
It handles the complete workflow from data acquisition to export, with proper
error handling and graceful degradation.

Author: Senior Backend Architect
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime
import logging
import numpy as np

# Type checking imports (not evaluated at runtime)
if TYPE_CHECKING:
    import pandas as pd
    import geopandas as gpd

# Import services
from src.services.satellite_service import SatelliteService
from src.services.mock_data_service import MockDataService
from src.services.processing_service import AdvancedProcessingService
from src.services.detection_service import AnomalyDetectionService
from src.services.coordinate_extractor import CoordinateExtractor
from src.services.export_service import ExportService

# Import provenance system (PROMPT 2)
from src.provenance import RunManifest, ManifestStatus

# Import ML models and features (optional)
try:
    from src.models import HeritageDetectionEnsemble
    from src.ml import extract_features
    ML_MODELS_AVAILABLE = True
except ImportError:
    ML_MODELS_AVAILABLE = False

# Import normalization utilities
from src.utils.schema_normalizer import normalize_detections

# Import error types
from src.utils.dependency_errors import (
    DependencyMissingError,
    ServiceInitializationError
)


@dataclass
class PipelineRequest:
    """
    Encapsulates all inputs required for pipeline execution.
    
    PROMPT 1: Unified API - AOI geometry only (no center_lat/lon)
    
    Attributes:
        aoi_geometry: Area of interest (Shapely geometry: Point, Polygon, etc.)
        start_date: Start date for satellite data (YYYY-MM-DD)
        end_date: End date for satellite data (YYYY-MM-DD)
        mode: Execution mode ('demo' or 'live' - 'real' auto-converted to 'live')
        max_cloud_cover: Maximum cloud coverage percentage
        anomaly_algorithm: Algorithm for anomaly detection
        contamination: Contamination parameter for anomaly detection
        export_formats: List of export formats (e.g., ['geojson', 'csv', 'kml'])
        output_dir: Directory for saving results
        output_basename: Base name for output files
        metadata: Additional metadata to include in results
    """
    aoi_geometry: Any  # Shapely geometry (Point/Polygon/MultiPolygon)
    start_date: str
    end_date: str
    mode: str = 'demo'
    max_cloud_cover: int = 30
    anomaly_algorithm: str = 'isolation_forest'
    contamination: float = 0.1
    model_mode: str = 'classic'  # 'classic', 'ensemble', or 'hybrid'
    export_formats: List[str] = field(default_factory=lambda: ['geojson', 'csv'])
    output_dir: str = 'outputs'
    output_basename: str = field(default_factory=lambda: f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize inputs."""
        # Normalize mode: 'real' -> 'live' for backward compatibility
        if self.mode == 'real':
            self.mode = 'live'
        
        # Validate mode
        if self.mode not in ['demo', 'live']:
            raise ValueError(
                f"Invalid mode: '{self.mode}'. Must be 'demo' or 'live' (or 'real' which converts to 'live')."
            )
        
        # Validate AOI geometry exists
        if self.aoi_geometry is None:
            raise ValueError("aoi_geometry is required and cannot be None")


@dataclass
class PipelineResult:
    """
    Standardized output from pipeline execution.
    
    PROMPT 2: No-Fake-Live Contract with Provenance Manifest
    - status: 'DEMO_OK' | 'LIVE_OK' | 'LIVE_FAILED'
    - manifest: Complete provenance tracking (REQUIRED)
    - data_quality: Quality metrics
    - If LIVE_FAILED: no likelihood, no heatmap, only failure_reason
    - If LIVE_OK: must have real data in manifest
    
    Attributes:
        success: Whether pipeline completed successfully
        status: Execution status following No-Fake-Live contract
        manifest: RunManifest with complete provenance (PROMPT 2)
        dataframe: GeoDataFrame with detected sites (None if LIVE_FAILED)
        stats: Dictionary with statistics (num_sites, processing_time, etc.)
        export_paths: Dictionary mapping format to file path
        errors: List of error messages encountered
        warnings: List of warning messages
        metadata: Additional metadata about the execution
        step_completed: Last step successfully completed
        data_quality: Quality metrics (scene count, cloud cover, etc.)
        provenance: Simplified provenance for UI (legacy, use manifest instead)
        failure_reason: Reason for LIVE_FAILED (if applicable)
    """
    success: bool
    status: str  # 'DEMO_OK' | 'LIVE_OK' | 'LIVE_FAILED'
    manifest: RunManifest  # PROMPT 2: Complete provenance tracking
    dataframe: Optional[Any] = None  # GeoDataFrame (avoid import at module level)
    stats: Dict[str, Any] = field(default_factory=dict)
    export_paths: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    step_completed: Optional[str] = None
    data_quality: Dict[str, Any] = field(default_factory=dict)  # PROMPT 2
    provenance: Optional[Dict[str, Any]] = None  # Legacy (use manifest)
    failure_reason: Optional[str] = None  # For LIVE_FAILED
    
    def can_show_likelihood(self) -> bool:
        """
        PROMPT 2: Check if archaeological likelihood can be shown.
        Only true if manifest indicates real data processing was successful.
        """
        return self.manifest.can_compute_likelihood()


class PipelineService:
    """
    Core orchestration service that unifies all Heritage Sentinel Pro services
    into a single, robust pipeline.
    
    The pipeline follows a linear 5-step execution flow:
        1. Fetch: Acquire satellite data (SatelliteService or MockDataService)
        2. Process: Calculate spectral indices (AdvancedProcessingService)
        3. Detect: Identify anomalies (AnomalyDetectionService)
        4. Extract: Convert anomaly map to coordinates (CoordinateExtractor)
        5. Export: Save results to disk (ExportService)
    
    Each step is wrapped in error handling for resilience. If a critical step
    fails, the pipeline returns immediately with error details.
    """
    
    def __init__(self, config: Dict, logger: Optional[logging.Logger] = None):
        """
        Initialize pipeline with configuration and logger.
        
        Args:
            config: Application configuration dictionary
            logger: Logger instance (creates default if None)
        """
        self.config = config
        self.logger = logger or self._create_default_logger()
        
        # Initialize services lazily (only when needed)
        self._satellite_service = None
        self._mock_service = None
        self._processing_service = None
        self._detection_service = None
        self._coordinate_extractor = None
        self._export_service = None
        
        self.logger.info("PipelineService initialized")
    
    def _create_default_logger(self) -> logging.Logger:
        """Create a default logger if none provided."""
        logger = logging.getLogger('PipelineService')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _get_satellite_service(self) -> SatelliteService:
        """Lazy initialization of SatelliteService."""
        if self._satellite_service is None:
            self._satellite_service = SatelliteService(self.config, self.logger)
        return self._satellite_service
    
    def _get_mock_service(self) -> MockDataService:
        """Lazy initialization of MockDataService."""
        if self._mock_service is None:
            self._mock_service = MockDataService()
        return self._mock_service
    
    def _get_processing_service(self) -> AdvancedProcessingService:
        """Lazy initialization of AdvancedProcessingService."""
        if self._processing_service is None:
            self._processing_service = AdvancedProcessingService(self.config, self.logger)
        return self._processing_service
    
    def _get_detection_service(self) -> AnomalyDetectionService:
        """Lazy initialization of AnomalyDetectionService."""
        if self._detection_service is None:
            self._detection_service = AnomalyDetectionService(self.config, self.logger)
        return self._detection_service
    
    def _get_coordinate_extractor(self) -> CoordinateExtractor:
        """Lazy initialization of CoordinateExtractor."""
        if self._coordinate_extractor is None:
            self._coordinate_extractor = CoordinateExtractor(self.config, self.logger)
        return self._coordinate_extractor
    
    def _get_export_service(self) -> ExportService:
        """Lazy initialization of ExportService."""
        if self._export_service is None:
            self._export_service = ExportService(self.config, self.logger)
        return self._export_service
    
    def _get_ensemble(self):
        """Lazy initialization of HeritageDetectionEnsemble."""
        if self._ensemble is None and ML_MODELS_AVAILABLE:
            self._ensemble = HeritageDetectionEnsemble()
        return self._ensemble
    
    def run(self, request: PipelineRequest) -> PipelineResult:
        """
        Execute the complete pipeline with the given request.
        
        PROMPT 5: No-Fake-Live Contract enforced:
        - DEMO_OK: Mock data with clear labeling
        - LIVE_OK: Real data with provenance
        - LIVE_FAILED: No results, only failure reason
        
        Args:
            request: PipelineRequest object with all necessary parameters
        
        Returns:
            PipelineResult: Standardized result object with data, stats, and errors
        """
        start_time = datetime.now()
        run_id = f"run_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Create manifest (PROMPT 2)
        from src.provenance import create_manifest
        manifest = create_manifest(
            run_id=run_id,
            mode=request.mode,
            request_params={
                'start_date': request.start_date,
                'end_date': request.end_date,
                'aoi_bounds': str(request.aoi_geometry.bounds)
            }
        )
        
        result = PipelineResult(success=False, status='UNKNOWN', manifest=manifest)
        
        self.logger.info("="*60)
        self.logger.info("Starting Heritage Sentinel Pro Pipeline")
        self.logger.info(f"Mode: {request.mode}")
        self.logger.info(f"Date Range: {request.start_date} to {request.end_date}")
        self.logger.info("="*60)
        
        # Store request metadata
        result.metadata['request'] = {
            'mode': request.mode,
            'start_date': request.start_date,
            'end_date': request.end_date,
            'start_time': start_time.isoformat()
        }
        
        # ============================================================
        # STEP 1: FETCH DATA (SatelliteService or MockDataService)
        # ============================================================
        bands_data = None
        try:
            self.logger.info("STEP 1/5: Fetching satellite data...")
            
            if request.mode == 'demo':
                # Demo mode: use MockDataService
                self.logger.info("Using MockDataService for demo mode")
                mock_service = self._get_mock_service()
                
                # Generate mock satellite data
                mock_data = mock_service.generate_mock_satellite_data(
                    width=100,
                    height=100
                )
                bands_data = mock_data['bands']
                result.step_completed = 'fetch'
                result.status = 'DEMO_OK'  # Clear demo labeling
                
                # Add mock data source to manifest (PROMPT 2)
                from src.provenance.run_manifest import DataSource
                manifest.add_data_source(DataSource(
                    provider='mock',
                    collection='MOCK_DATA',
                    scene_ids=['demo_scene_001'],
                    timestamps=[datetime.now().isoformat()],
                    api_endpoints=[],
                    total_scenes=1,
                    processed_scenes=1
                ))
                
            elif request.mode == 'live':
                # PROMPT 3: Live mode with real Sentinel Hub download
                self.logger.info("Using Live satellite providers (Sentinel Hub + GEE)")
                
                # Initialize Sentinel Hub Provider (PROMPT 3)
                from src.providers import SentinelHubProvider
                from src.provenance.run_manifest import DataSource, ProcessingStep
                
                sh_provider = SentinelHubProvider(self.config, self.logger)
                
                if not sh_provider.available:
                    # Sentinel Hub not available - LIVE_FAILED
                    result.status = 'LIVE_FAILED'
                    result.failure_reason = 'SENTINELHUB_UNAVAILABLE: Check credentials or install sentinelhub library'
                    self.logger.error(result.failure_reason)
                    result.errors.append(result.failure_reason)
                    manifest.set_failure(result.failure_reason)
                    return result
                
                # Convert AOI to bbox
                bbox = request.aoi_geometry.bounds  # (minx, miny, maxx, maxy)
                start_dt = datetime.strptime(request.start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(request.end_date, '%Y-%m-%d')
                
                # Search for scenes
                scenes = sh_provider.search_scenes(bbox, start_dt, end_dt, max_cloud_cover=20.0)
                
                if not scenes:
                    result.status = 'LIVE_FAILED'
                    result.failure_reason = 'NO_SCENES_FOUND: No satellite imagery available for the specified AOI and time range'
                    self.logger.error(result.failure_reason)
                    result.errors.append(result.failure_reason)
                    manifest.set_failure(result.failure_reason)
                    return result
                
                self.logger.info(f"Found {len(scenes)} scenes")
                
                # Download real bands (PROMPT 3)
                band_result = sh_provider.fetch_band_stack(
                    bbox=bbox,
                    time_range=(start_dt, end_dt),
                    resolution=10  # 10m resolution
                )
                
                if band_result.status != 'SUCCESS':
                    result.status = 'LIVE_FAILED'
                    # Prefer failure_reason from provider when available
                    failure_msg = getattr(band_result, 'failure_reason', None) or getattr(band_result, 'error', None) or 'Unknown error'
                    result.failure_reason = f'BAND_DOWNLOAD_FAILED: {failure_msg}'
                    self.logger.error(result.failure_reason)
                    result.errors.append(result.failure_reason)
                    manifest.set_failure(result.failure_reason)
                    return result
                
                # Extract bands
                bands_data = band_result.bands
                self.logger.info(f"✓ Downloaded real imagery: {bands_data.keys()}")
                
                # Add data source to manifest (PROMPT 2)
                manifest.add_data_source(DataSource(
                    provider='sentinelhub',
                    collection='SENTINEL2_L2A',
                    scene_ids=[s['id'] for s in scenes[:5]],
                    timestamps=[s['datetime'].isoformat() for s in scenes[:5]],
                    api_endpoints=['https://services.sentinel-hub.com/api/v1/process'],
                    total_scenes=len(scenes),
                    processed_scenes=len(band_result.timestamps)
                ))
                
                result.status = 'LIVE_OK'
                result.step_completed = 'fetch'
            
            else:
                error_msg = f"Invalid mode: {request.mode}. Must be 'demo' or 'live'"
                self.logger.error(error_msg)
                result.errors.append(error_msg)
                return result
            
            if bands_data is None or not bands_data:
                error_msg = "Failed to fetch satellite data - no bands returned"
                self.logger.error(error_msg)
                result.errors.append(error_msg)
                return result
            
            self.logger.info(f"✓ Successfully fetched {len(bands_data)} bands")
            
        except Exception as e:
            error_msg = f"STEP 1 FAILED: {type(e).__name__}: {str(e)}"
            self.logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # ============================================================
        # STEP 2: PROCESS (Calculate Spectral Indices)
        # ============================================================
        indices = None
        try:
            self.logger.info("STEP 2/5: Calculating spectral indices...")
            
            # PROMPT 3: Use real NDVI/NDWI for live mode
            if request.mode == 'live' and 'B04' in bands_data and 'B08' in bands_data:
                # Compute real NDVI/NDWI from downloaded bands (PROMPT 3)
                from src.providers import SentinelHubProvider
                sh_provider = SentinelHubProvider(self.config, self.logger)
                
                # Compute NDVI and NDWI
                ndvi = sh_provider.compute_ndvi(bands_data['B04'], bands_data['B08'])
                ndwi = sh_provider.compute_ndwi(bands_data['B03'], bands_data['B08'])
                
                # Create indices dict with real computed values
                indices = {
                    'NDVI': ndvi,
                    'NDWI': ndwi,
                    'B04': bands_data['B04'],  # Red
                    'B08': bands_data['B08']   # NIR
                }
                
                # Add indicators to manifest (PROMPT 2)
                from src.provenance.run_manifest import ComputedIndicator
                manifest.add_indicator(ComputedIndicator(
                    name='NDVI',
                    formula='(NIR - RED) / (NIR + RED)',
                    bands_used=['B08', 'B04'],
                    temporal_coverage={'computed_scenes': len(band_result.timestamps)},
                    computed_from_real_data=True
                ))
                manifest.add_indicator(ComputedIndicator(
                    name='NDWI',
                    formula='(GREEN - NIR) / (GREEN + NIR)',
                    bands_used=['B03', 'B08'],
                    temporal_coverage={'computed_scenes': len(band_result.timestamps)},
                    computed_from_real_data=True
                ))
                
                self.logger.info("✓ Computed real NDVI/NDWI from live imagery")
            else:
                # Demo mode or missing bands: use processing service
                processing_service = self._get_processing_service()
                indices = processing_service.calculate_spectral_indices(bands_data)
            
            if indices is None or not indices:
                error_msg = "Failed to calculate spectral indices - no indices returned"
                self.logger.error(error_msg)
                result.errors.append(error_msg)
                return result
            
            result.step_completed = 'process'
            self.logger.info(f"✓ Successfully calculated {len(indices)} spectral indices")
            
        except Exception as e:
            error_msg = f"STEP 2 FAILED: {type(e).__name__}: {str(e)}"
            self.logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # ============================================================
        # STEP 3: DETECT (Anomaly Detection)
        # ============================================================
        anomaly_map = None
        anomaly_surface = None
        try:
            self.logger.info("STEP 3/5: Detecting anomalies...")
            
            detection_service = self._get_detection_service()
            detection_result = detection_service.detect_anomalies(
                indices=indices,
                algorithm=request.anomaly_algorithm,
                contamination=request.contamination
            )
            
            anomaly_map = detection_result.get('anomaly_map')
            anomaly_surface = detection_result.get('anomaly_surface', anomaly_map)
            
            if anomaly_map is None:
                error_msg = "Failed to detect anomalies - no anomaly map returned"
                self.logger.error(error_msg)
                result.errors.append(error_msg)
                return result
            
            # Calculate detection statistics
            num_anomalies = int(np.sum(anomaly_map))
            total_pixels = anomaly_map.size
            anomaly_percentage = (num_anomalies / total_pixels) * 100
            
            result.stats['num_anomaly_pixels'] = num_anomalies
            result.stats['total_pixels'] = total_pixels
            result.stats['anomaly_percentage'] = round(anomaly_percentage, 2)
            
            result.step_completed = 'detect'
            self.logger.info(f"✓ Detected {num_anomalies} anomaly pixels ({anomaly_percentage:.2f}%)")
            
        except Exception as e:
            error_msg = f"STEP 3 FAILED: {type(e).__name__}: {str(e)}"
            self.logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # ============================================================
        # STEP 4: EXTRACT (Coordinate Extraction)
        # ============================================================
        gdf = None
        try:
            self.logger.info("STEP 4/5: Extracting coordinates...")
            
            try:
                coordinate_extractor = self._get_coordinate_extractor()
                gdf = coordinate_extractor.extract_coordinates_from_anomaly_map(
                    anomaly_map=anomaly_map,
                    anomaly_surface=anomaly_surface,
                    aoi_geometry=request.aoi_geometry
                )
                
                if gdf is None or gdf.empty:
                    # No sites detected - not necessarily an error
                    warning_msg = "No archaeological sites detected in the area"
                    self.logger.warning(warning_msg)
                    result.warnings.append(warning_msg)
                    
                    # Create empty GeoDataFrame with proper schema
                    import geopandas as gpd
                    gdf = gpd.GeoDataFrame({
                        'site_id': [],
                        'confidence': [],
                        'area_m2': [],
                        'geometry': []
                    }, crs='EPSG:4326')
                
                result.dataframe = gdf
                result.stats['num_sites'] = len(gdf)
                result.step_completed = 'extract'
                
                self.logger.info(f"✓ Extracted {len(gdf)} archaeological sites")
                
            except DependencyMissingError as e:
                # CoordinateExtractor requires heavy libraries
                error_msg = f"Cannot extract coordinates - missing: {', '.join(e.missing_libs)}"
                self.logger.error(error_msg)
                result.errors.append(error_msg)
                result.warnings.append(f"Install hint: {e.install_hint}")
                
                # Cannot continue without coordinates
                return result
            
        except Exception as e:
            error_msg = f"STEP 4 FAILED: {type(e).__name__}: {str(e)}"
            self.logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # ============================================================
        # STEP 4.5: APPLY ML MODELS (if requested)
        # ============================================================
        if request.model_mode in ['ensemble', 'hybrid'] and gdf is not None and not gdf.empty:
            try:
                self.logger.info("STEP 4.5: Applying ML ensemble scoring...")
                
                # Check if ML models available
                if not ML_MODELS_AVAILABLE:
                    warning_msg = "ML models requested but not available (sklearn not installed)"
                    self.logger.warning(warning_msg)
                    result.warnings.append(warning_msg)
                    result.stats['ensemble_available'] = False
                else:
                    ensemble = self._get_ensemble()
                    if ensemble is None:
                        result.warnings.append("Could not initialize ensemble model")
                        result.stats['ensemble_available'] = False
                    else:
                        result.stats['ensemble_available'] = True
                        feature_defaults_count = 0
                        
                        # Process each site
                        for idx in gdf.index:
                            site_row = gdf.loc[idx]
                            
                            # Extract features
                            features = extract_features(
                                site_row=site_row.to_dict() if hasattr(site_row, 'to_dict') else {},
                                indices_data=indices if indices else None,
                                geometry=site_row.get('geometry') if hasattr(site_row, 'get') else None
                            )
                            
                            # Count default features
                            if features.get('texture', 0) == 0:
                                feature_defaults_count += 1
                            
                            # Get ensemble score
                            ensemble_score = ensemble.apply_heritage_rules(features)
                            
                            # Clamp to [0, 1]
                            ensemble_score = max(0.0, min(1.0, ensemble_score))
                            
                            # Get classic confidence (if exists)
                            classic_conf = site_row.get('confidence', 0.75) if hasattr(site_row, 'get') else 0.75
                            
                            # Apply confidence logic based on mode
                            if request.model_mode == 'ensemble':
                                # Pure ensemble mode
                                new_confidence = ensemble_score * 100
                            else:  # hybrid
                                # Combine classic + ensemble
                                new_confidence = 0.6 * classic_conf + 0.4 * (ensemble_score * 100)
                            
                            # Update confidence
                            gdf.at[idx, 'confidence'] = new_confidence
                            
                            # Update priority based on new confidence
                            if new_confidence >= 85:
                                priority = 'high'
                            elif new_confidence >= 70:
                                priority = 'medium'
                            else:
                                priority = 'low'
                            
                            # Add/update priority column
                            if 'priority' in gdf.columns:
                                gdf.at[idx, 'priority'] = priority
                        
                        result.stats['feature_defaults_used_count'] = feature_defaults_count
                        result.stats['model_mode'] = request.model_mode
                        
                        self.logger.info(f"✓ Applied {request.model_mode} mode to {len(gdf)} sites")
                        self.logger.info(f"  Feature defaults used: {feature_defaults_count}")
            
            except Exception as e:
                error_msg = f"ML model application failed: {type(e).__name__}: {str(e)}"
                self.logger.warning(error_msg)
                result.warnings.append(error_msg)
        else:
            # Classic mode or no data
            result.stats['model_mode'] = request.model_mode
            # Classic mode or no data
            result.stats['model_mode'] = request.model_mode
            result.stats['ensemble_available'] = ML_MODELS_AVAILABLE
        
        # ============================================================
        # STEP 4.8: ARCHAEOLOGY SCORING (PROMPT 5)
        # ============================================================
        if gdf is not None and not gdf.empty and manifest.can_compute_likelihood():
            try:
                self.logger.info("STEP 4.8: Computing archaeology scores (PROMPT 5)...")
                
                from src.services.archaeology_scorer import ArchaeologyScorer, ArchaeologyScoringConfig
                
                scoring_config = ArchaeologyScoringConfig()
                scorer = ArchaeologyScorer(scoring_config, self.logger)
                
                # Score sites
                gdf = scorer.score_sites(
                    gdf=gdf,
                    indices=indices,
                    anomaly_map=anomaly_map,
                    aoi_geometry=request.aoi_geometry
                )
                
                result.dataframe = gdf
                result.stats['archaeology_scored'] = True
                self.logger.info("✓ Archaeology scores computed (real data only)")
                
            except Exception as e:
                error_msg = f"Archaeology scoring failed (non-critical): {str(e)}"
                self.logger.warning(error_msg)
                result.warnings.append(error_msg)
                result.stats['archaeology_scored'] = False
        else:
            # Demo mode: scores not computed (PROMPT 2 compliance)
            result.stats['archaeology_scored'] = False
            if manifest.status.value == 'DEMO_MODE':
                self.logger.info("Demo mode: archaeology scores not computed (PROMPT 2)")
        
        # ============================================================
        # STEP 4.9: NORMALIZE SCHEMA (before export)
        # ============================================================
        if gdf is not None and not gdf.empty:
            try:
                self.logger.info("STEP 4.9: Normalizing schema...")
                
                # Normalize to canonical schema
                gdf_normalized = normalize_detections(gdf)
                
                # Update result with normalized data
                gdf = gdf_normalized
                result.dataframe = gdf_normalized
                result.stats['schema_normalized'] = True
                
                self.logger.info(f"✓ Normalized {len(gdf)} detections to canonical schema")
                
            except Exception as e:
                # Non-critical - continue with unnormalized data
                error_msg = f"Schema normalization failed (non-critical): {type(e).__name__}: {str(e)}"
                self.logger.warning(error_msg)
                result.warnings.append(error_msg)
                result.stats['schema_normalized'] = False
        else:
            result.stats['schema_normalized'] = False
        
        # ============================================================
        # STEP 4.95: GROUND TRUTH EVALUATION (PROMPT 6)
        # ============================================================
        if gdf is not None and not gdf.empty:
            try:
                # Try to load and evaluate against ground truth (optional)
                from src.services.ground_truth_evaluator import GroundTruthEvaluator
                
                evaluator = GroundTruthEvaluator(self.logger)
                # Look for ground truth in config or workspace
                ground_truth_path = self.config.get('ground_truth_path')
                
                if ground_truth_path:
                    if evaluator.load_ground_truth(ground_truth_path):
                        eval_result = evaluator.evaluate(gdf)
                        result.metadata['ground_truth_evaluation'] = eval_result
                        result.stats['evaluation_status'] = eval_result.get('status', 'FAILED')
                        self.logger.info(f"Ground truth evaluation: {eval_result.get('metrics', {})}")
                
            except Exception as e:
                # Non-critical - ground truth evaluation is optional
                self.logger.debug(f"Ground truth evaluation not available: {e}")
        
        # ============================================================
        # STEP 5: EXPORT (Save Results)
        # ============================================================
        try:
            self.logger.info("STEP 5/5: Exporting results...")
            
            if gdf is not None and not gdf.empty and request.export_formats:
                export_service = self._get_export_service()
                export_paths = export_service.export_all(
                    gdf=gdf,
                    formats=request.export_formats,
                    output_dir=request.output_dir,
                    base_name=request.output_basename
                )
                
                result.export_paths = export_paths
                self.logger.info(f"✓ Exported to {len(export_paths)} format(s)")
                
                for fmt, path in export_paths.items():
                    self.logger.info(f"  - {fmt}: {path}")
            else:
                warning_msg = "Skipping export (no data or no formats specified)"
                self.logger.warning(warning_msg)
                result.warnings.append(warning_msg)
            
            result.step_completed = 'export'
            
        except Exception as e:
            # Export failure is not critical - we still have the data
            error_msg = f"STEP 5 FAILED (non-critical): {type(e).__name__}: {str(e)}"
            self.logger.warning(error_msg)
            result.warnings.append(error_msg)
        
        # ============================================================
        # FINALIZE RESULT
        # ============================================================
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        result.success = True
        result.stats['processing_time_seconds'] = round(processing_time, 2)
        result.metadata['end_time'] = end_time.isoformat()
        
        self.logger.info("="*60)
        self.logger.info("Pipeline completed successfully!")
        self.logger.info(f"Processing time: {processing_time:.2f} seconds")
        self.logger.info(f"Sites detected: {result.stats.get('num_sites', 0)}")
        self.logger.info("="*60)
        
        return result
    
    def validate_request(self, request: PipelineRequest) -> tuple[bool, List[str]]:
        """
        Validate a PipelineRequest before execution.
        
        Args:
            request: PipelineRequest to validate
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate mode
        if request.mode not in ['demo', 'live']:
            errors.append(f"Invalid mode: {request.mode}. Must be 'demo' or 'live'")
        
        # Validate dates
        try:
            start = datetime.strptime(request.start_date, '%Y-%m-%d')
            end = datetime.strptime(request.end_date, '%Y-%m-%d')
            if start > end:
                errors.append("start_date must be before end_date")
        except ValueError as e:
            errors.append(f"Invalid date format: {e}")
        
        # Validate parameters
        if not 0 < request.contamination < 1:
            errors.append("contamination must be between 0 and 1")
        
        if not 0 <= request.max_cloud_cover <= 100:
            errors.append("max_cloud_cover must be between 0 and 100")
        
        # Validate AOI
        if request.aoi_geometry is None:
            errors.append("aoi_geometry is required")
        
        # Validate export formats
        valid_formats = ['geojson', 'csv', 'kml', 'shapefile']
        for fmt in request.export_formats:
            if fmt not in valid_formats:
                errors.append(f"Invalid export format: {fmt}. Valid: {valid_formats}")
        
        return len(errors) == 0, errors
