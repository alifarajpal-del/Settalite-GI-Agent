"""
Heritage Sentinel Pro - Streamlit Cloud Entry Point
Simple entry point that directly runs the app
"""
import sys
from pathlib import Path
import streamlit as st

# Add project root and src to path - MUST be before any imports
project_root = Path(__file__).parent.absolute()
src_path = project_root / "src"
for p in (project_root, src_path):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

try:
    from app.app import main
    main()
except Exception as e:  # Surface errors instead of a blank screen
    st.error(f"Startup failed: {e}")
    st.exception(e)
