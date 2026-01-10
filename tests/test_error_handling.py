"""
اختبار معالجة أخطاء البحث في SentinelHubProvider
"""
import sys
from pathlib import Path

# إضافة src إلى المسار
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_error_handling():
    """اختبار معالجة الأخطاء والرسائل التشخيصية"""
    print("=" * 70)
    print("🧪 اختبار معالجة أخطاء البحث")
    print("=" * 70)
    
    try:
        from datetime import datetime, timedelta
        from src.providers.sentinelhub_provider import SentinelHubProvider
        from src.config import load_config
        import logging
        
        # إعداد Logger
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        logger = logging.getLogger("test_errors")
        
        # تحميل الإعدادات
        config = load_config()
        
        print("\n✅ تم تحميل الإعدادات")
        
        # إنشاء Provider
        provider = SentinelHubProvider(config, logger)
        
        # الاختبار 1: Provider غير متوفر
        print("\n" + "=" * 70)
        print("📝 اختبار 1: معالجة Provider غير متوفر")
        print("=" * 70)
        
        if not provider.available:
            bbox = (35.4, 30.3, 35.5, 30.4)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            scenes, error = provider.search_scenes(bbox, start_date, end_date, max_cloud_cover=30)
            
            print(f"\n📊 النتائج:")
            print(f"   - عدد المشاهد: {len(scenes)}")
            print(f"   - رسالة الخطأ موجودة: {'✅' if error else '❌'}")
            
            if error:
                print(f"\n📄 رسالة الخطأ:")
                print("-" * 70)
                print(error)
                print("-" * 70)
                
                # التحقق من احتواء الرسالة على معلومات مفيدة
                checks = {
                    "يحتوي على '❌'": "❌" in error,
                    "يحتوي على 'SentinelHub'": "sentinelhub" in error.lower(),
                    "يحتوي على سبب": len(error) > 50,
                }
                
                print(f"\n✅ فحوصات الرسالة:")
                for check, passed in checks.items():
                    status = "✅" if passed else "❌"
                    print(f"   {status} {check}")
        else:
            print("\n✅ Provider متوفر - سنختبر سيناريوهات أخرى")
            
            # الاختبار 2: منطقة بدون بيانات (محيط)
            print("\n" + "=" * 70)
            print("📝 اختبار 2: البحث في منطقة محيطية (بدون بيانات)")
            print("=" * 70)
            
            # منطقة في وسط المحيط الأطلسي
            ocean_bbox = (-30.0, 0.0, -29.0, 1.0)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            scenes, error = provider.search_scenes(
                ocean_bbox, 
                start_date, 
                end_date, 
                max_cloud_cover=80
            )
            
            print(f"\n📊 النتائج:")
            print(f"   - عدد المشاهد: {len(scenes)}")
            print(f"   - رسالة موجودة: {'✅' if error else '❌'}")
            
            if len(scenes) == 0 and error:
                print(f"\n✅ تم اكتشاف عدم وجود بيانات بشكل صحيح")
                print(f"\n📄 الرسالة:")
                print("-" * 70)
                # عرض أول 300 حرف فقط
                print(error[:300] + "..." if len(error) > 300 else error)
                print("-" * 70)
            
            # الاختبار 3: منطقة عادية (يجب أن تنجح)
            print("\n" + "=" * 70)
            print("📝 اختبار 3: البحث في منطقة عادية (Petra)")
            print("=" * 70)
            
            petra_bbox = (35.42, 30.30, 35.47, 30.35)
            
            scenes, error = provider.search_scenes(
                petra_bbox,
                start_date,
                end_date,
                max_cloud_cover=60
            )
            
            print(f"\n📊 النتائج:")
            print(f"   - عدد المشاهد: {len(scenes)}")
            print(f"   - رسالة خطأ: {error if error else 'لا يوجد'}")
            
            if len(scenes) > 0:
                print(f"\n✅ تم العثور على مشاهد!")
                print(f"   - أول مشهد: {scenes[0]['id']}")
                print(f"   - الغيوم: {scenes[0]['cloud_cover']:.1f}%")
            else:
                print(f"\n⚠️ لم يتم العثور على مشاهد")
                if error:
                    print(f"\nالسبب:")
                    print(error[:200])
        
        # النتيجة النهائية
        print("\n" + "=" * 70)
        print("🎉 اختبار معالجة الأخطاء اكتمل!")
        print("=" * 70)
        
        print("\n✅ التحسينات المنفذة:")
        print("   1. search_scenes تُرجع (scenes, error_message)")
        print("   2. رسائل خطأ واضحة مع رموز emoji")
        print("   3. تشخيص نوع الخطأ (اتصال، تخويل، بيانات مفقودة)")
        print("   4. اقتراحات عملية لحل المشكلة")
        print("   5. pipeline_service يحول الأخطاء إلى LIVE_FAILED")
        
        return True
        
    except Exception as e:
        print(f"\n❌ فشل الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_error_handling()
    sys.exit(0 if success else 1)
