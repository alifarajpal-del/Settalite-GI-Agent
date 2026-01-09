#!/usr/bin/env python3
"""
Entry Point for Heritage Sentinel Pro - Cloud-safe import proxy

When executed on Streamlit Cloud, this file imports the app module and explicitly
invokes its main() function to avoid blank screens caused by __name__ guards.
Locally, it simply shells out to the recommended Streamlit CLI command.
"""

import os
import sys

# 1. Add project root to path
root_path = os.path.dirname(os.path.abspath(__file__))
if root_path not in sys.path:
    sys.path.append(root_path)

# 2. Check environment
IN_STREAMLIT_CLOUD = os.environ.get("STREAMLIT_RUNTIME_ENV") or os.environ.get("HOSTNAME") == "streamlit"

if __name__ == "__main__":
    if IN_STREAMLIT_CLOUD:
        # On Cloud: Import AND run main() to bypass __name__ guards
        import app.app  # noqa: F401

        if hasattr(app.app, "main"):
            app.app.main()
        else:
            # Fallback: execute script directly if no main exists
            app_path = os.path.join(root_path, "app", "app.py")
            with open(app_path, "r", encoding="utf-8") as app_file:
                code = compile(app_file.read(), app_path, "exec")
                exec(code, globals(), locals())
    else:
        # Local: Run via CLI command to ensure environment is loaded
        print("🚀 Running locally...")
        os.system("streamlit run app/app.py")

