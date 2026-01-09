#!/usr/bin/env python3
"""
Entry Point for Heritage Sentinel Pro - Simple Import Proxy

This file serves as a lightweight entry point that avoids bootstrapping conflicts.
Streamlit Cloud will auto-detect and run this file.
"""

import os
import sys

# 1. Add project root to path
root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_path)

# 2. Check environment
IN_STREAMLIT_CLOUD = os.environ.get("STREAMLIT_RUNTIME_ENV") or os.environ.get("HOSTNAME") == "streamlit"

if __name__ == "__main__":
    if IN_STREAMLIT_CLOUD:
        # On Cloud: Import AND run main()
        import app.app
        if hasattr(app.app, 'main'):
            app.app.main()
        else:
            # Fallback if no main function exists (execute script directly)
            with open(os.path.join(root_path, "app", "app.py")) as f:
                exec(f.read(), globals(), locals())
    else:
        # Local: Run via CLI command
        print("🚀 Running locally...")
        os.system("streamlit run app/app.py")

