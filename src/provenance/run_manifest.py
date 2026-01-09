"""
PROMPT 2: Provenance Manifest System
Strict tracking of data sources and processing steps with NO FAKE RESULTS policy.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import hashlib


class ManifestStatus(Enum):
    """Status of pipeline execution."""
    SUCCESS = "SUCCESS"  # All steps completed with real data
    PARTIAL = "PARTIAL"  # Some steps completed, degraded functionality
    LIVE_FAILED = "LIVE_FAILED"  # Live data fetch failed
    NO_DATA = "NO_DATA"  # No data available for processing
    DEMO_MODE = "DEMO_MODE"  # Running in demonstration mode


@dataclass
class DataSource:
    """Information about a data source used."""
    provider: str  # 'sentinelhub', 'gee', 'mock'
    collection: str  # e.g., 'SENTINEL2_L2A'
    scene_ids: List[str]  # List of scene identifiers
    timestamps: List[str]  # ISO format timestamps
    api_endpoints: List[str]  # Request endpoints (no secrets)
    total_scenes: int
    processed_scenes: int  # Actually processed (not just queried)


@dataclass
class ProcessingStep:
    """Record of a processing step."""
    step_name: str
    started_at: str
    completed_at: str
    status: str  # 'SUCCESS', 'FAILED', 'SKIPPED'
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class ComputedIndicator:
    """Record of a spectral/derived indicator."""
    name: str  # 'NDVI', 'NDWI', 'SAVI', etc.
    formula: str
    bands_used: List[str]
    temporal_coverage: Dict[str, Any]  # stats over time
    computed_from_real_data: bool  # CRITICAL FLAG


@dataclass
class OutputArtifact:
    """Record of generated output."""
    file_path: str
    file_type: str
    file_size_bytes: int
    checksum_sha256: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RunManifest:
    """
    Complete provenance manifest for a pipeline run.
    
    PROMPT 2: No-Fake-Results Policy
    - If status != SUCCESS, no archaeological likelihood is computed
    - All data sources must be traceable
    - Indicators must flag if computed from real vs mock data
    """
    run_id: str
    started_at: str
    completed_at: str
    status: ManifestStatus
    mode: str  # 'demo' or 'live'
    
    # Data sources
    data_sources: List[DataSource] = field(default_factory=list)
    
    # Processing pipeline
    processing_steps: List[ProcessingStep] = field(default_factory=list)
    
    # Computed indicators
    indicators: List[ComputedIndicator] = field(default_factory=list)
    
    # Outputs
    outputs: List[OutputArtifact] = field(default_factory=list)
    
    # Quality metrics
    data_quality: Dict[str, Any] = field(default_factory=dict)
    
    # Failure tracking
    failure_reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    # Request metadata
    request_params: Dict[str, Any] = field(default_factory=dict)
    
    def add_data_source(self, source: DataSource):
        """Add a data source to the manifest."""
        self.data_sources.append(source)
    
    def add_processing_step(self, step: ProcessingStep):
        """Add a processing step to the manifest."""
        self.processing_steps.append(step)
    
    def add_indicator(self, indicator: ComputedIndicator):
        """Add a computed indicator to the manifest."""
        self.indicators.append(indicator)
    
    def add_output(self, artifact: OutputArtifact):
        """Add an output artifact to the manifest."""
        self.outputs.append(artifact)
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def set_failure(self, reason: str, status: ManifestStatus = ManifestStatus.LIVE_FAILED):
        """Mark the run as failed."""
        self.status = status
        self.failure_reason = reason
    
    def can_compute_likelihood(self) -> bool:
        """
        Check if archaeological likelihood can be computed.
        
        PROMPT 2: Strict policy - only if:
        1. Status is SUCCESS
        2. At least one indicator was computed from real data
        3. Data quality is acceptable
        """
        if self.status != ManifestStatus.SUCCESS:
            return False
        
        # Check if any indicators were computed from real data
        has_real_indicators = any(
            ind.computed_from_real_data for ind in self.indicators
        )
        
        if not has_real_indicators and self.mode == 'live':
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        return {
            'run_id': self.run_id,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'status': self.status.value,
            'mode': self.mode,
            'data_sources': [asdict(ds) for ds in self.data_sources],
            'processing_steps': [asdict(ps) for ps in self.processing_steps],
            'indicators': [asdict(ind) for ind in self.indicators],
            'outputs': [asdict(out) for out in self.outputs],
            'data_quality': self.data_quality,
            'failure_reason': self.failure_reason,
            'warnings': self.warnings,
            'request_params': self.request_params
        }
    
    def save(self, output_dir: str = 'outputs') -> str:
        """Save manifest to JSON file."""
        output_path = Path(output_dir) / f"manifest_{self.run_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        return str(output_path)


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_manifest(run_id: str, mode: str, request_params: Dict[str, Any]) -> RunManifest:
    """Create a new run manifest."""
    return RunManifest(
        run_id=run_id,
        started_at=datetime.now().isoformat(),
        completed_at="",  # Will be set on completion
        status=ManifestStatus.SUCCESS if mode == 'demo' else ManifestStatus.LIVE_FAILED,
        mode=mode,
        request_params=request_params
    )
