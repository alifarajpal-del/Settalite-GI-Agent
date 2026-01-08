#!/usr/bin/env python3
"""
Entry Point for Heritage Sentinel Pro

This file serves as the application entry point for Streamlit Cloud.
It can also be used to launch the app locally.

Usage:
    streamlit run app/app.py     (Recommended - direct approach)
    streamlit run run.py          (Alternative - via this wrapper)
    python run.py                 (Launches streamlit programmatically)
"""

import sys
from pathlib import Path

# Add project root to PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Launch the Streamlit app"""
    # Check if we're being run directly (python run.py)
    if __name__ == "__main__":
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
            import os
            
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
    else:
        # Being imported by Streamlit - just import the app
        import app.app  # noqa: F401


if __name__ == "__main__":
    main()
else:
    # Import when used with streamlit run
    import app.app  # noqa: F401

