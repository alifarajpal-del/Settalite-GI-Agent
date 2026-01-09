"""
Model Registry for Heritage Sentinel Pro
Handles saving, loading, versioning, and metadata management for trained models
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import joblib


class ModelRegistry:
    """
    Central registry for managing trained ML models.
    Provides version control, metadata tracking, and safe persistence.
    """
    
    def __init__(self, registry_dir: str = 'models/registry'):
        """
        Initialize model registry.
        
        Args:
            registry_dir: Directory to store models and metadata
        """
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.registry_dir / 'registry_metadata.json'
        
        # Load or initialize registry metadata
        self._load_registry_metadata()
    
    def _load_registry_metadata(self):
        """Load existing registry metadata or create new"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)
        else:
            self.registry = {
                'models': {},
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self._save_registry_metadata()
    
    def _save_registry_metadata(self):
        """Persist registry metadata to disk"""
        self.registry['last_updated'] = datetime.now().isoformat()
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
    
    def save_model(
        self, 
        model: Any, 
        model_name: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a model with metadata.
        
        Args:
            model: Trained model object (scikit-learn compatible)
            model_name: Unique identifier for the model
            metadata: Additional metadata (version, description, metrics, etc.)
        
        Returns:
            Path to saved model file
        
        Raises:
            ValueError: If model_name is invalid
            IOError: If save operation fails
        """
        if not model_name or not model_name.strip():
            raise ValueError("model_name cannot be empty")
        
        # Create versioned filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version = metadata.get('version', '1.0.0') if metadata else '1.0.0'
        safe_name = model_name.replace(' ', '_').replace('/', '_')
        model_filename = f"{safe_name}_v{version}_{timestamp}.joblib"
        model_path = self.registry_dir / model_filename
        
        try:
            # Save model using joblib
            joblib.dump(model, model_path)
            
            # Update registry metadata
            model_info = {
                'name': model_name,
                'path': str(model_path),
                'version': version,
                'created_at': timestamp,
                'file_size_bytes': model_path.stat().st_size,
                'model_type': type(model).__name__,
                'metadata': metadata or {}
            }
            
            # Add to registry
            if model_name not in self.registry['models']:
                self.registry['models'][model_name] = []
            
            self.registry['models'][model_name].append(model_info)
            self._save_registry_metadata()
            
            return str(model_path)
        
        except Exception as e:
            raise IOError(f"Failed to save model '{model_name}': {str(e)}")
    
    def load_model(
        self, 
        model_name: str, 
        version: Optional[str] = None
    ) -> Any:
        """
        Load a model by name and optional version.
        
        Args:
            model_name: Name of the model to load
            version: Specific version (default: latest)
        
        Returns:
            Loaded model object
        
        Raises:
            ValueError: If model not found
            IOError: If load operation fails
        """
        if model_name not in self.registry['models']:
            raise ValueError(f"Model '{model_name}' not found in registry")
        
        model_versions = self.registry['models'][model_name]
        
        if not model_versions:
            raise ValueError(f"No versions found for model '{model_name}'")
        
        # Find requested version or use latest
        if version:
            model_info = next(
                (m for m in model_versions if m['version'] == version),
                None
            )
            if not model_info:
                raise ValueError(
                    f"Version '{version}' not found for model '{model_name}'"
                )
        else:
            # Use most recent version
            model_info = model_versions[-1]
        
        model_path = Path(model_info['path'])
        
        if not model_path.exists():
            raise IOError(
                f"Model file not found: {model_path}. "
                "Registry metadata may be out of sync."
            )
        
        try:
            return joblib.load(model_path)
        except Exception as e:
            raise IOError(f"Failed to load model '{model_name}': {str(e)}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all registered models with their metadata.
        
        Returns:
            List of model info dictionaries
        """
        models_list = []
        
        for model_name, versions in self.registry['models'].items():
            if not versions:
                continue
            
            # Get latest version info
            latest = versions[-1]
            
            models_list.append({
                'name': model_name,
                'latest_version': latest['version'],
                'created_at': latest['created_at'],
                'model_type': latest['model_type'],
                'file_size_bytes': latest['file_size_bytes'],
                'total_versions': len(versions),
                'path': latest['path']
            })
        
        return models_list
    
    def delete_model(
        self, 
        model_name: str, 
        version: Optional[str] = None
    ) -> bool:
        """
        Delete a model version (or all versions if version=None).
        
        Args:
            model_name: Name of model to delete
            version: Specific version to delete (None = all versions)
        
        Returns:
            True if deletion successful
        
        Raises:
            ValueError: If model not found
        """
        if model_name not in self.registry['models']:
            raise ValueError(f"Model '{model_name}' not found in registry")
        
        if version:
            # Delete specific version
            versions = self.registry['models'][model_name]
            model_info = next(
                (m for m in versions if m['version'] == version),
                None
            )
            
            if not model_info:
                raise ValueError(
                    f"Version '{version}' not found for model '{model_name}'"
                )
            
            # Delete file
            model_path = Path(model_info['path'])
            if model_path.exists():
                model_path.unlink()
            
            # Remove from registry
            self.registry['models'][model_name].remove(model_info)
        else:
            # Delete all versions
            for model_info in self.registry['models'][model_name]:
                model_path = Path(model_info['path'])
                if model_path.exists():
                    model_path.unlink()
            
            # Remove from registry
            del self.registry['models'][model_name]
        
        self._save_registry_metadata()
        return True
    
    def get_model_info(
        self, 
        model_name: str, 
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model
            version: Specific version (default: latest)
        
        Returns:
            Model information dictionary
        
        Raises:
            ValueError: If model or version not found
        """
        if model_name not in self.registry['models']:
            raise ValueError(f"Model '{model_name}' not found in registry")
        
        versions = self.registry['models'][model_name]
        
        if version:
            model_info = next(
                (m for m in versions if m['version'] == version),
                None
            )
            if not model_info:
                raise ValueError(
                    f"Version '{version}' not found for model '{model_name}'"
                )
        else:
            model_info = versions[-1]
        
        return model_info.copy()
