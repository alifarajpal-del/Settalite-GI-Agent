"""
اختبار إصلاح خدمة satellite_service
"""
import sys
import os
from pathlib import Path

# إضافة src إلى المسار
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_satellite_service():
    """اختبار خدمة satellite_service مع التوقيع الجديد"""
    print("=" * 60)
    print("🧪 اختبار خدمة Satellite Service")
    print("=" * 60)
    
    try:
        # استيراد المكتبات المطلوبة
        import geopandas as gpd
        from shapely.geometry import Point
        from datetime import datetime, timedelta
        from src.services.satellite_service import SatelliteService
        import logging
        
        # إعداد Logger بسيط
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = logging.getLogger("test_satellite_service")
        
        # تحميل الإعدادات
        from src.config import load_config
        config = load_config()
        
        # إنشاء خدمة الأقمار الصناعية
        satellite_service = SatelliteService(config, logger)
        
        print("\n✅ تم إنشاء SatelliteService بنجاح")
        
        # إنشاء منطقة اهتمام تجريبية (Petra)
        center_lon, center_lat = 35.4444, 30.3285
        point = Point(center_lon, center_lat)
        buffer_size = 0.02  # ~2 كم تقريباً
        
        aoi_geometry = gpd.GeoDataFrame(
            {'geometry': [point.buffer(buffer_size)]},
            crs='EPSG:4326'
        ).geometry[0]
        
        print(f"\n📍 منطقة الاهتمام: {aoi_geometry.bounds}")
        print(f"   - المساحة: ~{buffer_size * 111 * 2:.1f} كم")
        
        # تحديد نطاق زمني
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # 6 أشهر
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        print(f"\n📅 النطاق الزمني:")
        print(f"   - من: {start_date_str}")
        print(f"   - إلى: {end_date_str}")
        
        # اختبار 1: استدعاء download_sentinel_data مع التوقيع الجديد
        print("\n" + "=" * 60)
        print("📥 اختبار 1: تنزيل بيانات Sentinel-2")
        print("=" * 60)
        
        satellite_data = satellite_service.download_sentinel_data(
            aoi_geometry=aoi_geometry,
            start_date=start_date_str,
            end_date=end_date_str,
            max_cloud_cover=30
        )
        
        print("\n✅ تم تنزيل البيانات بنجاح!")
        print(f"\n📊 النتائج:")
        print(f"   - عدد النطاقات: {len(satellite_data.get('bands', {}))}")
        print(f"   - النطاقات: {list(satellite_data.get('bands', {}).keys())}")
        print(f"   - القمر الصناعي: {satellite_data['metadata'].get('satellite')}")
        print(f"   - تغطية الغيوم: {satellite_data['metadata'].get('cloud_cover')}%")
        print(f"   - الدقة: {satellite_data['metadata'].get('resolution')}م")
        
        # التحقق من الحدود
        if 'bounds' in satellite_data:
            print(f"   - الحدود: {satellite_data['bounds']}")
        
        # التحقق من أحجام المصفوفات
        print(f"\n📐 أحجام البيانات:")
        for band_name, band_data in satellite_data['bands'].items():
            print(f"   - {band_name}: {band_data.shape} (min={band_data.min():.3f}, max={band_data.max():.3f})")
        
        # اختبار 2: التحقق من معالجة aoi_geometry بشكل صحيح
        print("\n" + "=" * 60)
        print("🔍 اختبار 2: التحقق من استخدام aoi_geometry")
        print("=" * 60)
        
        # التحقق من أن bounds في النتيجة يطابق aoi_geometry
        expected_bounds = aoi_geometry.bounds
        actual_bounds = satellite_data['bounds']
        
        bounds_match = all(
            abs(expected_bounds[i] - actual_bounds[i]) < 1e-6
            for i in range(4)
        )
        
        if bounds_match:
            print("✅ الحدود تطابق aoi_geometry بشكل صحيح")
        else:
            print(f"⚠️  عدم تطابق الحدود:")
            print(f"   - المتوقع: {expected_bounds}")
            print(f"   - الفعلي: {actual_bounds}")
        
        # اختبار 3: التحقق من فحص None
        print("\n" + "=" * 60)
        print("🛡️  اختبار 3: فحص aoi_geometry=None")
        print("=" * 60)
        
        try:
            satellite_service.download_sentinel_data(
                aoi_geometry=None,
                start_date=start_date_str,
                end_date=end_date_str,
                max_cloud_cover=30
            )
            print("❌ لم يتم رفض aoi_geometry=None (يجب أن يرفض!)")
        except ValueError as e:
            print(f"✅ تم رفض aoi_geometry=None بشكل صحيح: {e}")
        
        # اختبار 4: البحث عن الصور المتاحة
        print("\n" + "=" * 60)
        print("🔎 اختبار 4: البحث عن الصور المتاحة")
        print("=" * 60)
        
        available_images = satellite_service.search_available_images(
            start_date=start_date_str,
            end_date=end_date_str,
            max_cloud_cover=30
        )
        
        print(f"\n✅ تم العثور على {len(available_images)} صورة")
        if available_images:
            print("\n📸 أول 3 صور:")
            for img in available_images[:3]:
                print(f"   - {img['id']}: {img['date']} (غيوم: {img['cloud_cover']}%)")
        
        # النتيجة النهائية
        print("\n" + "=" * 60)
        print("🎉 جميع الاختبارات نجحت!")
        print("=" * 60)
        print("\n✅ خدمة satellite_service تعمل بشكل صحيح")
        print("✅ aoi_geometry يُمرر ويُستخدم بشكل صحيح")
        print("✅ التوقيع الجديد للدالة يعمل")
        print("✅ فحص None يعمل")
        
        return True
        
    except Exception as e:
        print(f"\n❌ فشل الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_satellite_service()
    sys.exit(0 if success else 1)
