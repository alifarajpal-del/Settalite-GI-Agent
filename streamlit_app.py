"""
Heritage Sentinel Pro - Streamlit Cloud Entry Point
Simple entry point that directly runs the app
"""
import sys
from pathlib import Path

# Add project root to path - MUST be before any imports
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import and run the app
if __name__ == "__main__":
    # Direct execution by streamlit
    from app.app import main
    main()
else:
    # Import as module
    from app import app
