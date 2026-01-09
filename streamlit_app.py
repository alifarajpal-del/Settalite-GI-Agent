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

# Import the app module - Streamlit will execute it automatically
from app.app import main

# Call main() immediately for Streamlit Cloud
main()
