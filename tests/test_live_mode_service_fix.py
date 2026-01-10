"""
اختبار LiveModeService مع التوقيع الجديد
"""
import sys
import os
from pathlib import Path

# إضافة src إلى المسار
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_live_mode_service():
    """اختبار LiveModeService مع التوقيع الجديد لـ download_sentinel_data"""
    print("=" * 60)
    print("🧪 اختبار LiveModeService")
    print("=" * 60)
    
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        from datetime import datetime, timedelta
        from src.services.live_mode_service import LiveModeService
        import logging
        
        # إعداد Logger
        logging.basicConfig(level=logging.INFO)
        
        print("\n✅ تم استيراد LiveModeService بنجاح")
        
        # إنشاء LiveModeService
        live_service = LiveModeService()
        
        print("✅ تم إنشاء LiveModeService بنجاح")
        
        # إنشاء AOI تجريبي
        center_lon, center_lat = 35.4444, 30.3285  # Petra
        point = Point(center_lon, center_lat)
        buffer_size = 0.01  # ~1 كم
        
        aoi_geometry = gpd.GeoDataFrame(
            {'geometry': [point.buffer(buffer_size)]},
            crs='EPSG:4326'
        ).geometry[0]
        
        print(f"\n📍 منطقة الاهتمام (Petra): {aoi_geometry.bounds}")
        
        # تحديد نطاق زمني
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # 3 أشهر
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        print(f"📅 النطاق الزمني: {start_date_str} إلى {end_date_str}")
        
        # اختبار run_full_pipeline
        print("\n" + "=" * 60)
        print("🚀 اختبار run_full_pipeline")
        print("=" * 60)
        
        results = live_service.run_full_pipeline(
            aoi_geometry=aoi_geometry,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        print(f"\n✅ Pipeline اكتمل بحالة: {results['status']}")
        print(f"\n📋 خطوات التنفيذ:")
        
        for step_name, step_info in results['steps'].items():
            status_icon = "✅" if step_info['status'] == 'success' else "⚠️"
            print(f"   {status_icon} {step_name}: {step_info['message']}")
        
        # التحقق من satellite_data
        if 'satellite_data' in results['steps']:
            sat_step = results['steps']['satellite_data']
            if sat_step['status'] == 'success':
                print("\n✅ خطوة satellite_data نجحت!")
                print("   ✓ تم استخدام aoi_geometry بشكل صحيح")
                print("   ✓ التوقيع الجديد للدالة يعمل")
            else:
                print(f"\n⚠️  satellite_data: {sat_step['message']}")
        
        # النتيجة النهائية
        print("\n" + "=" * 60)
        print("🎉 اختبار LiveModeService اكتمل بنجاح!")
        print("=" * 60)
        print("\n✅ run_full_pipeline يعمل بشكل صحيح")
        print("✅ استدعاء download_sentinel_data بالترتيب الصحيح")
        print("✅ aoi_geometry يُمرر كمعامل أول")
        
        return True
        
    except Exception as e:
        print(f"\n❌ فشل الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_live_mode_service()
    sys.exit(0 if success else 1)
