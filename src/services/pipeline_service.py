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

# Import error types
from src.utils.dependency_errors import (
    DependencyMissingError,
    ServiceInitializationError
)


@dataclass
class PipelineRequest:
    """
    Encapsulates all inputs required for pipeline execution.
    
    Attributes:
        aoi_geometry: Area of interest (Shapely geometry)
        start_date: Start date for satellite data (YYYY-MM-DD)
        end_date: End date for satellite data (YYYY-MM-DD)
        mode: Execution mode ('demo' or 'live')
        max_cloud_cover: Maximum cloud coverage percentage
        anomaly_algorithm: Algorithm for anomaly detection
        contamination: Contamination parameter for anomaly detection
        export_formats: List of export formats (e.g., ['geojson', 'csv', 'kml'])
        output_dir: Directory for saving results
        output_basename: Base name for output files
        metadata: Additional metadata to include in results
    """
    aoi_geometry: Any
    start_date: str
    end_date: str
    mode: str = 'demo'
    max_cloud_cover: int = 30
    anomaly_algorithm: str = 'isolation_forest'
    contamination: float = 0.1
    export_formats: List[str] = field(default_factory=lambda: ['geojson', 'csv'])
    output_dir: str = 'outputs'
    output_basename: str = field(default_factory=lambda: f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """
    Standardized output from pipeline execution.
    
    Attributes:
        success: Whether pipeline completed successfully
        dataframe: GeoDataFrame with detected sites (None if failed)
        stats: Dictionary with statistics (num_sites, processing_time, etc.)
        export_paths: Dictionary mapping format to file path
        errors: List of error messages encountered
        warnings: List of warning messages
        metadata: Additional metadata about the execution
        step_completed: Last step successfully completed
    """
    success: bool
    dataframe: Optional[Any] = None  # GeoDataFrame (avoid import at module level)
    stats: Dict[str, Any] = field(default_factory=dict)
    export_paths: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    step_completed: Optional[str] = None


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
    
    def run(self, request: PipelineRequest) -> PipelineResult:
        """
        Execute the complete pipeline with the given request.
        
        This method orchestrates all services in a linear flow, handling errors
        gracefully at each step. If any critical step fails, it returns
        immediately with error details.
        
        Args:
            request: PipelineRequest object with all necessary parameters
        
        Returns:
            PipelineResult: Standardized result object with data, stats, and errors
        """
        start_time = datetime.now()
        result = PipelineResult(success=False)
        
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
                
            elif request.mode == 'live':
                # Live mode: use SatelliteService
                self.logger.info("Using SatelliteService for live mode")
                
                try:
                    satellite_service = self._get_satellite_service()
                    satellite_result = satellite_service.download_sentinel_data(
                        aoi_geometry=request.aoi_geometry,
                        start_date=request.start_date,
                        end_date=request.end_date,
                        max_cloud_cover=request.max_cloud_cover
                    )
                    bands_data = satellite_result['bands']
                    result.step_completed = 'fetch'
                    
                except DependencyMissingError as e:
                    # Heavy libraries missing - graceful degradation
                    error_msg = f"Missing dependencies for live mode: {', '.join(e.missing_libs)}"
                    self.logger.warning(error_msg)
                    result.errors.append(error_msg)
                    result.warnings.append(f"Install hint: {e.install_hint}")
                    result.warnings.append("Falling back to demo mode...")
                    
                    # Fall back to demo mode
                    mock_service = self._get_mock_service()
                    mock_data = mock_service.generate_mock_satellite_data(
                        width=100,
                        height=100
                    )
                    bands_data = mock_data['bands']
                    result.metadata['fallback_to_demo'] = True
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
