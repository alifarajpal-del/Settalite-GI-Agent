#!/usr/bin/env python3
"""
نقطة البداية لـ Heritage Sentinel Pro على Streamlit Cloud
هذا الملف يقوم بتحميل التطبيق الرئيسي من مجلد app/
"""
import sys
from pathlib import Path

# إضافة مسار المشروع
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# استيراد التطبيق الرئيسي
# سيتم تشغيل كل محتويات app/app.py تلقائياً
exec(open("app/app.py", encoding='utf-8').read())
