#!/usr/bin/env python3
"""
ملف التشغيل الرئيسي لنظام Heritage Sentinel Pro
"""
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def check_dependencies():
    """فحص التبعيات والمكتبات المطلوبة"""
    required = [
        'streamlit', 'numpy', 'geopandas', 'rasterio', 
        'scikit-learn', 'plotly', 'shapely'
    ]
    
    missing = []
    for lib in required:
        try:
            __import__(lib)
        except ImportError:
            missing.append(lib)
    
    return missing

def main():
    """الدالة الرئيسية للتشغيل"""
    print("=" * 60)
    print("🛰️  Heritage Sentinel Pro - نظام كشف الآثار بالذكاء الاصطناعي")
    print("=" * 60)
    
    # فحص التبعيات
    print("\n🔍 فحص التبعيات...")
    missing = check_dependencies()
    
    if missing:
        print(f"❌ المكتبات المفقودة: {', '.join(missing)}")
        print("الرجاء تثبيتها باستخدام:")
        print("pip install " + " ".join(missing))
        return
    
    print("✅ جميع التبعيات مثبتة")
    
    # إنشاء المجلدات المطلوبة
    print("\n📁 إنشاء هيكل المجلدات...")
    folders = ['data', 'data/raw', 'data/processed', 'outputs', 'exports', 'temp']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"  ✓ {folder}")
    
    # عرض خيارات التشغيل
    print("\n🎯 خيارات التشغيل:")
    print("1. تشغيل الواجهة الرسومية (Streamlit)")
    print("2. الخروج")
    
    choice = input("\nاختر الخيار (1-2): ").strip()
    
    if choice == '1':
        print("\n🚀 تشغيل الواجهة الرسومية...")
        print("سيتم فتح المتصفح تلقائياً على العنوان: http://localhost:8501")
        print("اضغط Ctrl+C لإيقاف الخادم\n")
        
        # تشغيل Streamlit
        os.system("streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501")
    
    else:
        print("\n👋 وداعاً!")

if __name__ == "__main__":
    main()
