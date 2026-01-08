"""
Custom exception classes for dependency management
"""
from typing import List, Optional


class DependencyMissingError(Exception):
    """
    Exception raised when required dependencies are missing
    
    This exception provides clear information about:
    - Which libraries are missing
    - How to install them
    - Whether the operation can continue without them
    """
    
    def __init__(
        self, 
        missing_libs: List[str],
        operation: str = "this operation",
        install_hint: Optional[str] = None,
        is_critical: bool = True
    ):
        """
        Initialize DependencyMissingError
        
        Args:
            missing_libs: List of missing library names
            operation: Description of the operation that requires these libraries
            install_hint: Custom installation instruction (auto-generated if None)
            is_critical: Whether this error should stop execution
        """
        self.missing_libs = missing_libs
        self.operation = operation
        self.is_critical = is_critical
        
        # Generate install hint if not provided
        if install_hint is None:
            if len(missing_libs) == 1:
                self.install_hint = f"pip install {missing_libs[0]}"
            else:
                libs_str = " ".join(missing_libs)
                self.install_hint = f"pip install {libs_str}"
            
            # Check if this matches our requirements files
            if all(lib in ['geopandas', 'rasterio', 'scipy', 'fiona', 'pyproj'] for lib in missing_libs):
                self.install_hint = "pip install -r requirements_core.txt -r requirements_geo.txt"
        else:
            self.install_hint = install_hint
        
        # Build error message
        libs_formatted = ", ".join(missing_libs)
        message = (
            f"❌ Missing required dependencies for {operation}: {libs_formatted}\n\n"
            f"📦 To install:\n"
            f"   {self.install_hint}\n\n"
        )
        
        if not is_critical:
            message += "💡 This feature is optional. The application can continue without it."
        
        super().__init__(message)


class ServiceInitializationError(Exception):
    """Exception raised when a service fails to initialize"""
    
    def __init__(self, service_name: str, reason: str, suggestion: str = ""):
        self.service_name = service_name
        self.reason = reason
        self.suggestion = suggestion
        
        message = f"Failed to initialize {service_name}: {reason}"
        if suggestion:
            message += f"\n💡 {suggestion}"
        
        super().__init__(message)


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors"""
    
    def __init__(self, config_key: str, issue: str):
        self.config_key = config_key
        self.issue = issue
        
        message = f"Configuration error for '{config_key}': {issue}"
        super().__init__(message)
