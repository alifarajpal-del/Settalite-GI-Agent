#!/usr/bin/env python3
"""
Entry Point for Heritage Sentinel Pro

This file serves as the application entry point for both local and cloud deployment.

Usage:
    streamlit run app/app.py     (Recommended - direct approach)
    streamlit run run.py          (Cloud deployment - works automatically)
    python run.py                 (Local - launches streamlit programmatically)
"""

import sys
import os
from pathlib import Path

# Add project root to PYTHONPATH
project_root = Path(__file__).parent
src_path = project_root / "src"

# Ensure project root and src are on PYTHONPATH for Streamlit Cloud
for p in (project_root, src_path):
    sp = str(p.resolve())
    if sp not in sys.path:
        sys.path.insert(0, sp)


def is_streamlit_cloud():
    """Detect if running on Streamlit Cloud"""
    # Streamlit Cloud sets these environment variables
    return (
        os.getenv("STREAMLIT_SHARING_MODE") is not None or
        os.getenv("STREAMLIT_SERVER_PORT") is not None or
        "streamlit" in sys.modules
    )


def main():
    """Launch the Streamlit app"""
    # Check if we're on Streamlit Cloud or being run via streamlit command
    if is_streamlit_cloud():
        # On Streamlit Cloud or via streamlit run - just import the app
        import app.app  # noqa: F401
        return
    
    # Running locally with python run.py
    print("=" * 60)
    print("Heritage Sentinel Pro - AI-Powered Archaeological Detection")
    print("=" * 60)
    print()
    print("Starting Streamlit application...")
    print()
    print("Recommended command:")
    print("   streamlit run app/app.py")
    print()
    print("Launching with bootstrap...")
    print()
    
    try:
        # Use streamlit's bootstrap to launch the app
        from streamlit.web import cli as st_cli
        
        # Set the script path
        app_path = str(project_root / "app" / "app.py")
        
        # Launch streamlit
        sys.argv = ["streamlit", "run", app_path]
        sys.exit(st_cli.main())
        
    except Exception as e:
        print(f"Failed to launch with bootstrap: {e}")
        print()
        print("Please use the recommended command instead:")
        print("   streamlit run app/app.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
else:
    # Being imported by Streamlit - just import the app
    import app.app  # noqa: F401

