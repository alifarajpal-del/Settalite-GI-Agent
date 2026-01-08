#!/usr/bin/env python3
"""
نقطة البداية لـ Heritage Sentinel Pro على Streamlit Cloud
يستورد التطبيق الرئيسي من مجلد app/
"""

import sys
from pathlib import Path

# تضمين مسار المشروع في PYTHONPATH حتى يمكن تحميل الحزم المحلية
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# استيراد التطبيق الرئيسي (التنفيذ يحدث أثناء الاستيراد)
import app.app  # noqa: F401

if __name__ == "__main__":
	# لا حاجة لتشغيل أي شيء إضافي؛ Streamlit ينفذ الشيفرة عند الاستيراد
	pass
