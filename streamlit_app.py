"""
Heritage Sentinel Pro - Streamlit Cloud Entry Point
Redirects to the main application
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main app
from app.app import main

if __name__ == "__main__":
    main()
