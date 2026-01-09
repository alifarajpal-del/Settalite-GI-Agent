#!/usr/bin/env python3
"""
Entry Point for Heritage Sentinel Pro - Simple Import Proxy

This file serves as a lightweight entry point that avoids bootstrapping conflicts.
Streamlit Cloud will auto-detect and run this file.
"""

import os
import sys

# 1. Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2. Check environment
IN_STREAMLIT_CLOUD = os.environ.get("STREAMLIT_RUNTIME_ENV") or os.environ.get("HOSTNAME") == "streamlit"

if __name__ == "__main__":
    if IN_STREAMLIT_CLOUD:
        # On Cloud: Just import the app directly. Do NOT use bootstrap.
        import app.app
    else:
        # Local: Run via CLI command to ensure environment is loaded
        print("🚀 Running locally...")
        os.system("streamlit run app/app.py")

