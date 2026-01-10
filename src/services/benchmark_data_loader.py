"""
Benchmark Data Loader for Heritage Sentinel Pro
Provides opt-in access to EuroSAT dataset for model validation.

The EuroSAT dataset contains 27,000 labeled Sentinel-2 satellite images
across 10 land cover classes. This loader:
- Downloads EuroSAT dataset (opt-in only)
- Extracts relevant classes for heritage detection
- Converts to canonical schema for testing
- Provides train/test splits

Dataset: https://github.com/phelber/EuroSAT
Citation: Helber et al. (2019)
"""
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BenchmarkDataLoader:
    """
    Loader for benchmark datasets (EuroSAT) with privacy-aware opt-in design.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize benchmark data loader.
        
        Args:
            data_dir: Directory for storing benchmark data (default: ./data/benchmarks)
        """
        if data_dir is None:
            data_dir = os.path.join(os.getcwd(), 'data', 'benchmarks')
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # EuroSAT configuration
        self.eurosat_url = "https://zenodo.org/record/7711810/files/EuroSAT.zip"
        self.eurosat_dir = self.data_dir / "eurosat"
        
        # Heritage-relevant classes from EuroSAT
        self.heritage_classes = {
            'AnnualCrop': 0.3,      # Agricultural areas (ancient fields)
            'Pasture': 0.2,         # Pastoral areas
            'HerbaceousVegetation': 0.4,  # Vegetation covering ruins
            'Highway': 0.6,         # Modern roads (may overlay ancient routes)
            'Residential': 0.7,     # Settlement areas
            'River': 0.5,           # Water features (ancient irrigation)
            'Forest': 0.3           # Forest (may hide ruins)
        }
        
        logger.info(f"BenchmarkDataLoader initialized (data_dir={self.data_dir})")
    
    def is_eurosat_available(self) -> bool:
        """
        Check if EuroSAT dataset is already downloaded.
        
        Returns:
            True if available, False otherwise
        """
        if not self.eurosat_dir.exists():
            return False
        
        # Check if has class folders
        class_folders = list(self.eurosat_dir.glob("*/"))
        return len(class_folders) > 0
    
    def download_eurosat(self, consent: bool = False) -> bool:
        """
        Download EuroSAT dataset (requires explicit consent).
        
        Args:
            consent: User must explicitly opt-in (True)
        
        Returns:
            True if download successful, False otherwise
        """
        if not consent:
            logger.warning("EuroSAT download requires explicit consent")
            logger.info("Set consent=True to download")
            logger.info("Dataset size: ~89 MB (compressed)")
            logger.info("License: Attribution 4.0 International (CC BY 4.0)")
            logger.info("Citation: Helber et al. (2019)")
            return False
        
        logger.info("Downloading EuroSAT dataset...")
        logger.info(f"URL: {self.eurosat_url}")
        logger.info(f"Destination: {self.eurosat_dir}")
        
        try:
            import requests
            import zipfile
            
            # Download
            zip_path = self.data_dir / "eurosat.zip"
            
            logger.info("Downloading... (this may take a few minutes)")
            response = requests.get(self.eurosat_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            logger.info(f"Download progress: {progress:.1f}%")
            
            logger.info("Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.eurosat_dir)
            
            # Clean up zip
            zip_path.unlink()
            
            logger.info("✓ EuroSAT dataset downloaded successfully")
            return True
        
        except ImportError:
            logger.error("Missing 'requests' library - install with: pip install requests")
            return False
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def load_eurosat_samples(
        self,
        num_samples: int = 100,
        heritage_only: bool = True,
        as_canonical: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Load EuroSAT samples for testing.
        
        Args:
            num_samples: Number of samples to load
            heritage_only: Only load heritage-relevant classes
            as_canonical: Convert to canonical schema
        
        Returns:
            DataFrame with samples, or None if not available
        """
        if not self.is_eurosat_available():
            logger.warning("EuroSAT dataset not available")
            logger.info("Call download_eurosat(consent=True) first")
            return None
        
        logger.info(f"Loading {num_samples} EuroSAT samples...")
        
        samples = []
        
        # Get class folders
        class_folders = list(self.eurosat_dir.glob("*/"))
        
        if heritage_only:
            # Filter to heritage-relevant classes
            class_folders = [
                f for f in class_folders
                if f.name in self.heritage_classes
            ]
        
        if not class_folders:
            logger.error("No valid class folders found")
            return None
        
        # Calculate samples per class
        samples_per_class = max(1, num_samples // len(class_folders))
        
        for class_folder in class_folders:
            class_name = class_folder.name
            
            # Get image files
            image_files = list(class_folder.glob("*.jpg")) + list(class_folder.glob("*.png"))
            
            if not image_files:
                continue
            
            # Sample random images
            num_to_sample = min(samples_per_class, len(image_files))
            rng = np.random.default_rng(42)
            sampled_files = rng.choice(image_files, size=num_to_sample, replace=False)
            
            for image_file in sampled_files:
                # Extract metadata from filename (if available)
                # EuroSAT filenames typically: {class}_{id}.jpg
                
                samples.append({
                    'image_path': str(image_file),
                    'class': class_name,
                    'filename': image_file.name,
                    'heritage_relevance': self.heritage_classes.get(class_name, 0.5)
                })
        
        df = pd.DataFrame(samples)
        
        logger.info(f"✓ Loaded {len(df)} samples from {len(class_folders)} classes")
        
        if as_canonical and not df.empty:
            df = self._convert_to_canonical(df)
        
        return df
    
    def _convert_to_canonical(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert EuroSAT samples to canonical heritage schema.
        
        Args:
            df: DataFrame with EuroSAT samples
        
        Returns:
            DataFrame with canonical schema
        """
        logger.info("Converting to canonical schema...")
        
        # Generate synthetic coordinates (distributed across Europe)
        # EuroSAT covers European countries
        num_samples = len(df)
        
        # Random locations in Europe (rough bounds)
        europe_lat_range = (36.0, 71.0)
        europe_lon_range = (-10.0, 40.0)
        
        rng = np.random.default_rng(42)
        df['lat'] = rng.uniform(europe_lat_range[0], europe_lat_range[1], num_samples)
        df['lon'] = rng.uniform(europe_lon_range[0], europe_lon_range[1], num_samples)
        
        # Use heritage relevance as confidence
        df['confidence'] = (df['heritage_relevance'] * 100).clip(0, 100)
        
        # Generate priority
        def get_priority(c):
            if c >= 80:
                return 'high'
            elif c >= 65:
                return 'medium'
            else:
                return 'low'
        df['priority'] = df['confidence'].apply(get_priority)
        
        # Generate synthetic areas
        df['area_m2'] = rng.uniform(500, 5000, num_samples)
        
        # Map class to site_type
        class_to_site_type = {
            'AnnualCrop': 'agricultural',
            'Pasture': 'agricultural',
            'HerbaceousVegetation': 'burial',  # Vegetation may cover burial mounds
            'Highway': 'settlement',           # Roads suggest settlements
            'Residential': 'settlement',
            'River': 'agricultural',           # Irrigation
            'Forest': 'temple'                 # Sacred groves
        }
        
        df['site_type'] = df['class'].map(class_to_site_type).fillna('unknown')
        
        # Generate IDs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df['id'] = [f"EUROSAT_{timestamp}_{i:04d}" for i in range(len(df))]
        
        # Add source
        df['source'] = 'eurosat'
        
        # Keep only canonical columns
        canonical_cols = ['id', 'lat', 'lon', 'confidence', 'priority', 'area_m2', 'site_type', 'source']
        
        # Add any missing columns
        for col in canonical_cols:
            if col not in df.columns:
                df[col] = None
        
        df = df[canonical_cols]
        
        logger.info("✓ Converted to canonical schema")
        return df
    
    def create_train_test_split(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create train/test split for model validation.
        
        Args:
            df: DataFrame with samples
            test_size: Proportion for test set (0.0-1.0)
            random_state: Random seed
        
        Returns:
            Tuple of (train_df, test_df)
        """
        logger.info(f"Creating train/test split (test_size={test_size})...")
        
        # Shuffle indices
        rng = np.random.default_rng(random_state)
        indices = np.arange(len(df))
        rng.shuffle(indices)
        
        # Split point
        split_idx = int(len(df) * (1 - test_size))
        
        train_indices = indices[:split_idx]
        test_indices = indices[split_idx:]
        
        train_df = df.iloc[train_indices].reset_index(drop=True)
        test_df = df.iloc[test_indices].reset_index(drop=True)
        
        logger.info(f"✓ Split: {len(train_df)} train, {len(test_df)} test")
        
        return train_df, test_df
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about available benchmark data.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'eurosat_available': self.is_eurosat_available(),
            'data_dir': str(self.data_dir),
            'heritage_classes': list(self.heritage_classes.keys())
        }
        
        if stats['eurosat_available']:
            # Count images per class
            class_counts = {}
            for class_name in self.heritage_classes:
                class_folder = self.eurosat_dir / class_name
                if class_folder.exists():
                    image_count = len(list(class_folder.glob("*.jpg")) + list(class_folder.glob("*.png")))
                    class_counts[class_name] = image_count
            
            stats['class_counts'] = class_counts
            stats['total_images'] = sum(class_counts.values())
        
        return stats


def quick_benchmark_test(download: bool = False) -> Optional[pd.DataFrame]:
    """
    Quick test function for benchmark loader.
    
    Args:
        download: Whether to download EuroSAT if not available
    
    Returns:
        DataFrame with samples, or None if not available
    """
    loader = BenchmarkDataLoader()
    
    # Check availability
    if not loader.is_eurosat_available():
        logger.info("EuroSAT not available")
        if download:
            logger.info("Attempting download (requires consent)...")
            success = loader.download_eurosat(consent=True)
            if not success:
                return None
        else:
            logger.info("Set download=True to download dataset")
            return None
    
    # Load samples
    df = loader.load_eurosat_samples(num_samples=50, heritage_only=True)
    
    if df is not None:
        logger.info(f"Loaded {len(df)} samples")
        logger.info(f"Confidence range: {df['confidence'].min():.1f} - {df['confidence'].max():.1f}")
        logger.info(f"Site types: {df['site_type'].value_counts().to_dict()}")
    
    return df
