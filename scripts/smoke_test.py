#!/usr/bin/env python3
"""
Heritage Sentinel Pro - Cross-platform Smoke Test
Verifies critical paths, imports, and services without pytest
"""
import sys
import platform
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    
def colored(text, color):
    return f"{color}{text}{Colors.RESET}"

def check_critical_paths():
    """Check if critical paths exist"""
    failures = []
    success = []
    
    print(colored("📁 Critical Paths:", Colors.CYAN))
    critical_paths = [
        "app/app.py",
        "run.py",
        "requirements.txt",
        "src/config/__init__.py",
        "src/services/mock_data_service.py"
    ]
    
    for path_str in critical_paths:
        path = Path(path_str)
        if path.exists():
            print(colored(f"  ✅ {path_str}", Colors.GREEN))
            success.append(f"Path: {path_str}")
        else:
            print(colored(f"  ❌ {path_str} MISSING", Colors.RED))
            failures.append(f"Missing: {path_str}")
    
    return failures, success

def check_config_loader():
    """Test config loader"""
    failures = []
    success = []
    
    print(colored("\n🔧 Config Loader:", Colors.CYAN))
    try:
        from src.config import ConfigLoader
        loader = ConfigLoader()
        success.append("ConfigLoader import")
        print(colored("  ✅ Config loader works", Colors.GREEN))
    except Exception as e:
        print(colored(f"  ❌ Config failed: {e}", Colors.RED))
        failures.append(f"ConfigLoader: {e}")
    
    return failures, success

def check_mock_data_service():
    """Test MockDataService"""
    failures = []
    success = []
    warnings = []
    
    print(colored("\n📊 MockDataService:", Colors.CYAN))
    try:
        from src.services.mock_data_service import MockDataService
        mock = MockDataService()
        print(colored("  ✅ MockDataService.create_mock_aoi()", Colors.GREEN))
        success.append("MockDataService init")
        
        # Try generating mock data
        try:
            mock_aoi = mock.create_mock_aoi()
            if isinstance(mock_aoi, dict) and 'geometry' in mock_aoi:
                success.append("Mock AOI")
            else:
                print(colored("  ⚠️  AOI format unexpected", Colors.YELLOW))
                warnings.append("AOI format")
        except Exception:
            print(colored("  ⚠️  AOI format unexpected", Colors.YELLOW))
            warnings.append("AOI format")
        
        # Try detections
        try:
            detections = mock.create_mock_detections(10, 20)
            if isinstance(detections, object):
                success.append("Detections")
            else:
                print(colored("  ⚠️  Detections format unexpected", Colors.YELLOW))
                warnings.append("Detections format")
        except Exception:
            print(colored("  ⚠️  Detections format unexpected", Colors.YELLOW))
            warnings.append("Detections format")
            
    except Exception as e:
        print(colored(f"  ❌ MockDataService failed: {e}", Colors.RED))
        failures.append(f"MockDataService: {e}")
    
    return failures, success, warnings

def print_summary(failures, warnings, success):
    """Print test summary"""
    print("\n" + colored("=" * 60, Colors.CYAN))
    print(colored("\n📊 Summary:", Colors.CYAN))
    print(colored(f"  ✅ Success: {len(success)}", Colors.GREEN))
    print(colored(f"  ⚠️  Warnings: {len(warnings)}", Colors.YELLOW))
    print(colored(f"  ❌ Failures: {len(failures)}", Colors.RED))
    
    if failures:
        print(colored("\n❌ FAILED", Colors.RED))
        print("\nFailures:")
        for fail in failures:
            print(f"  • {fail}")
        
        print(colored("\nNext steps:", Colors.YELLOW))
        print("  1. pip install -r requirements.txt")
        print("  2. Verify src/ directory structure")
        return 2
    else:
        success_rate = len(success) / (len(success) + len(warnings)) * 100 if success else 0
        print(colored(f"\n✅ PASSED (Success rate: {success_rate:.0f}%)", Colors.GREEN))
        
        if warnings:
            print(colored(f"\n⚠️  {len(warnings)} optional features missing (demo mode still works)", Colors.YELLOW))
        
        return 0

def main():
    print(colored("\n🛰️  Heritage Sentinel Pro - Smoke Test\n", Colors.CYAN))
    
    # System info
    print(colored("📊 System Information:", Colors.CYAN))
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Platform: {platform.system()} {platform.release()}")
    print(f"  Architecture: {platform.machine()}\n")
    
    failures = []
    warnings = []
    success = []
    
    # Critical paths check
    print(colored("📁 Critical Paths:", Colors.CYAN))
    critical_paths = [
        "app/app.py",
        "run.py",
        "requirements.txt",
        "src/config/__init__.py",
        "src/services/mock_data_service.py"
    ]
    
    for path_str in critical_paths:
        path = Path(path_str)
        if path.exists():
            print(colored(f"  ✅ {path_str}", Colors.GREEN))
            success.append(f"Path: {path_str}")
        else:
            print(colored(f"  ❌ {path_str} MISSING", Colors.RED))
            failures.append(f"Missing path: {path_str}")
    
    # List config directory
    config_dir = Path("src/config")
    if config_dir.exists():
        config_files = list(config_dir.glob("*.py"))
        print(f"\n  Config files: {', '.join(f.name for f in config_files)}")
    
    # Required imports
    print(colored("\n📦 Required Imports:", Colors.CYAN))
    required_modules = ["streamlit", "numpy", "pandas"]
    
    for module in required_modules:
        try:
            __import__(module)
            print(colored(f"  ✅ {module}", Colors.GREEN))
            success.append(f"Import: {module}")
        except ImportError:
            print(colored(f"  ❌ {module} MISSING", Colors.RED))
            failures.append(f"Required module: {module}")
    
    # Nice-to-have imports
    print(colored("\n🎁 Recommended Imports:", Colors.CYAN))
    recommended = ["geopandas", "shapely", "pydeck", "folium"]
    
    for module in recommended:
        try:
            __import__(module)
            print(colored(f"  ✅ {module}", Colors.GREEN))
            success.append(f"Import: {module}")
        except ImportError:
            print(colored(f"  ⚠️  {module} (optional)", Colors.YELLOW))
            warnings.append(f"Optional module: {module}")
    
    # Heavy optional imports
    print(colored("\n🏋️  Heavy Optional:", Colors.CYAN))
    heavy_optional = ["rasterio", "scipy"]
    
    for module in heavy_optional:
        try:
            __import__(module)
            print(colored(f"  ✅ {module}", Colors.GREEN))
        except ImportError:
            print(colored(f"  ⚠️  {module} (live mode only)", Colors.YELLOW))
    
    # Service checks
    print(colored("\n🔧 Service Checks:", Colors.CYAN))
    
    # Config loader
    try:
        sys.path.insert(0, str(Path.cwd()))
        from src.config import load_config
        config = load_config()
        
        if isinstance(config, dict) and 'app' in config:
            print(colored("  ✅ Config loader works", Colors.GREEN))
            success.append("Config loader")
        else:
            print(colored("  ❌ Config invalid format", Colors.RED))
            failures.append("Config format")
    except Exception as e:
        print(colored(f"  ❌ Config loader failed: {e}", Colors.RED))
        failures.append(f"Config loader: {e}")
    
    # Mock data service
    try:
        from src.services.mock_data_service import MockDataService
        
        mock = MockDataService()
        
        # Test create_mock_aoi
        aoi = mock.create_mock_aoi()
        if hasattr(aoi, 'is_valid') or hasattr(aoi, 'geom_type'):
            print(colored("  ✅ MockDataService.create_mock_aoi()", Colors.GREEN))
            success.append("Mock AOI")
        else:
            print(colored("  ⚠️  AOI format unexpected", Colors.YELLOW))
            warnings.append("AOI format")
        
        # Test generate_mock_detections
        detections = mock.generate_mock_detections()
        
        if hasattr(detections, 'columns'):
            required_cols = ['خط الطول', 'خط العرض']  # Arabic column names
            has_coords = any(col in detections.columns for col in required_cols)
            
            if len(detections) > 0 and has_coords:
                print(colored(f"  ✅ MockDataService.generate_mock_detections() [{len(detections)} sites]", Colors.GREEN))
                success.append(f"Mock detections: {len(detections)} sites")
            else:
                print(colored("  ⚠️  Detections format unexpected", Colors.YELLOW))
                warnings.append("Detections format")
        else:
            print(colored("  ❌ Detections not a DataFrame", Colors.RED))
            failures.append("Detections format")
            
    except Exception as e:
        print(colored(f"  ❌ MockDataService failed: {e}", Colors.RED))
        failures.append(f"MockDataService: {e}")
    
    # Summary
    print("\n" + colored("=" * 60, Colors.CYAN))
    print(colored("\n📊 Summary:", Colors.CYAN))
    print(colored(f"  ✅ Success: {len(success)}", Colors.GREEN))
    print(colored(f"  ⚠️  Warnings: {len(warnings)}", Colors.YELLOW))
    print(colored(f"  ❌ Failures: {len(failures)}", Colors.RED))
    
    if failures:
        print(colored("\n❌ FAILED", Colors.RED))
        print("\nFailures:")
        for fail in failures:
            print(f"  • {fail}")
        
        print(colored("\nNext steps:", Colors.YELLOW))
        print("  1. pip install -r requirements.txt")
        print("  2. Verify src/ directory structure")
        return 2
    else:
        success_rate = len(success) / (len(success) + len(warnings)) * 100 if success else 0
        print(colored(f"\n✅ PASSED (Success rate: {success_rate:.0f}%)", Colors.GREEN))
        
        if warnings:
            print(colored(f"\n⚠️  {len(warnings)} optional features missing (demo mode still works)", Colors.YELLOW))
        
        return 0

if __name__ == "__main__":
    sys.exit(main())
