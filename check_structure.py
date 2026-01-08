"""فحص هيكل المشروع"""
import os
import sys

print("📁 فحص هيكل المشروع...")
project_files = []
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            rel_path = os.path.join(root, file)
            project_files.append(rel_path)

print(f"✅ تم العثور على {len(project_files)} ملف Python")

# عرض الملفات الرئيسية
core_files = [f for f in project_files if any(x in f for x in [
    'coordinate_extractor', 'processing_service', 'detection_service',
    'satellite_service', 'anomaly_detector', 'mock_data_service'
])]

print("\n🔍 الملفات الأساسية الموجودة:")
for f in core_files:
    print(f"  - {f}")

# فحص ملفات التطبيق
app_files = [f for f in project_files if 'app' in f and 'app.py' in f]
print("\n📱 ملفات التطبيق:")
for f in app_files:
    print(f"  - {f}")

# فحص ملفات الإعدادات
config_files = [f for f in project_files if 'config' in f or 'demo_mode' in f]
print("\n⚙️ ملفات الإعدادات:")
for f in config_files:
    print(f"  - {f}")

# فحص ملفات الاختبار
test_files = [f for f in project_files if 'test' in f]
print(f"\n🧪 ملفات الاختبار: {len(test_files)}")
