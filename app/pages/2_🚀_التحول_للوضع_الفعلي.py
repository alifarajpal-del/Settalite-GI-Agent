"""
صفحة التحول التدريجي من الوضع التجريبي إلى الفعلي
"""
import streamlit as st
import sys
import time
from pathlib import Path

# إضافة المسار للوحدات
sys.path.append(str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="التحول للوضع الفعلي", page_icon="🚀", layout="wide")

st.title("🚀 التحول للوضع الفعلي")

st.info("""
هذه الصفحة تساعدك في التحول التدريجي من النظام التجريبي إلى النظام الفعلي.
سيتم اختبار كل مكون على حدة قبل التشغيل الكامل.
""")

# مراحل التحول
migration_steps = [
    {
        "name": "التحقق من المكتبات",
        "description": "تأكد من تثبيت جميع المكتبات المطلوبة",
        "test_function": "check_libraries"
    },
    {
        "name": "فحص ملفات الخدمات",
        "description": "التأكد من وجود جميع ملفات الخدمات",
        "test_function": "check_service_files"
    },
    {
        "name": "اختبار خدمة المعالجة",
        "description": "اختبار قدرات المعالجة المتقدمة",
        "test_function": "test_processing_service"
    },
    {
        "name": "اختبار خدمة كشف الشذوذ",
        "description": "اختبار خوارزميات ML لكشف الأنماط",
        "test_function": "test_detection_service"
    },
    {
        "name": "اختبار استخراج الإحداثيات",
        "description": "اختبار دقة استخراج الإحداثيات",
        "test_function": "test_coordinate_extractor"
    },
    {
        "name": "اختبار تكامل كامل",
        "description": "اختبار خط الأنابيب بالكامل",
        "test_function": "test_full_pipeline"
    }
]

def check_libraries():
    """فحص المكتبات المطلوبة"""
    required_libs = [
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('geopandas', 'geopandas'),
        ('sklearn', 'scikit-learn'),
        ('shapely', 'shapely'),
        ('yaml', 'pyyaml')
    ]
    
    missing_libs = []
    available_libs = []
    
    for import_name, package_name in required_libs:
        try:
            __import__(import_name)
            available_libs.append(package_name)
        except ImportError:
            missing_libs.append(package_name)
    
    return available_libs, missing_libs

def check_service_files():
    """فحص وجود ملفات الخدمات"""
    project_root = Path(__file__).parent.parent.parent
    service_files = [
        "src/services/processing_service.py",
        "src/services/detection_service.py", 
        "src/services/coordinate_extractor.py",
        "src/services/satellite_service.py",
        "src/services/export_service.py",
        "src/services/mock_data_service.py",
        "src/services/live_mode_service.py"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in service_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            existing_files.append(file_path)
    
    return existing_files, missing_files

def test_processing_service():
    """اختبار خدمة المعالجة"""
    try:
        from src.services.mock_data_service import MockDataService
        from src.services.processing_service import AdvancedProcessingService
        from src.config import load_config
        from src.utils.logging_utils import setup_logger
        
        config = load_config()
        logger = setup_logger(config['paths']['outputs'])
        
        # توليد بيانات تجريبية
        mock = MockDataService()
        test_data = mock.generate_mock_satellite_data(width=50, height=50)
        
        # اختبار المعالجة
        processor = AdvancedProcessingService(config, logger)
        indices = processor.calculate_spectral_indices(test_data['bands'])
        
        return True, f"تم حساب {len(indices)} مؤشر بنجاح"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def test_detection_service():
    """اختبار خدمة كشف الشذوذ"""
    try:
        from src.services.mock_data_service import MockDataService
        from src.services.processing_service import AdvancedProcessingService
        from src.services.detection_service import AnomalyDetectionService
        from src.config import load_config
        from src.utils.logging_utils import setup_logger
        
        config = load_config()
        logger = setup_logger(config['paths']['outputs'])
        
        # توليد بيانات تجريبية
        mock = MockDataService()
        test_data = mock.generate_mock_satellite_data(width=50, height=50)
        
        # معالجة
        processor = AdvancedProcessingService(config, logger)
        indices = processor.calculate_spectral_indices(test_data['bands'])
        
        # كشف الشذوذ
        detector = AnomalyDetectionService(config, logger)
        anomaly_results = detector.detect_anomalies(indices, contamination=0.1)
        
        anomaly_count = anomaly_results['statistics']['anomaly_pixels']
        return True, f"تم اكتشاف {anomaly_count} بكسل شاذ"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def test_coordinate_extractor():
    """اختبار استخراج الإحداثيات"""
    try:
        from src.services.mock_data_service import MockDataService
        from src.services.coordinate_extractor import CoordinateExtractor
        from src.config import load_config
        from src.utils.logging_utils import setup_logger
        
        config = load_config()
        logger = setup_logger(config['paths']['outputs'])
        
        # توليد بيانات تجريبية
        mock = MockDataService()
        anomaly_map = mock.generate_mock_anomaly_map(width=50, height=50)
        test_data = mock.generate_mock_satellite_data(width=50, height=50)
        aoi = mock.create_mock_aoi()
        
        # استخراج الإحداثيات
        extractor = CoordinateExtractor(config, logger)
        coords = extractor.extract_precise_coordinates(
            anomaly_map,
            test_data['transform'],
            test_data['crs'],
            aoi
        )
        
        detection_count = coords['total_detections']
        return True, f"تم استخراج {detection_count} موقع"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def test_full_pipeline():
    """اختبار خط الأنابيب الكامل"""
    try:
        from src.services.live_mode_service import LiveModeService
        from src.services.mock_data_service import MockDataService
        
        # تهيئة الخدمة
        live_service = LiveModeService()
        services_status = live_service.initialize_services()
        
        # عدد الخدمات الناجحة
        success_count = sum(1 for status in services_status.values() if '✅' in status)
        total_count = len(services_status)
        
        # توليد AOI تجريبي
        mock = MockDataService()
        test_aoi = mock.create_mock_aoi()
        
        # اختبار خط الأنابيب
        results = live_service.run_full_pipeline(
            aoi_geometry=test_aoi,
            start_date="2025-01-01",
            end_date="2026-01-01"
        )
        
        if results['status'] == 'completed':
            detections = results.get('detections', {}).get('total_detections', 0)
            return True, f"اكتمل التحليل بنجاح ({success_count}/{total_count} خدمات، {detections} اكتشاف)"
        else:
            return False, f"فشل التحليل: {results.get('error', 'غير معروف')}"
            
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def _update_library_check_status(step, status, available, missing):
    """Update status and display results for library check"""
    if missing:
        status.update(label=f"⚠️ {step['name']} - مكتمل مع تحذيرات", state="complete")
        st.warning(f"مكتبات مفقودة: {', '.join(missing)}")
        st.success(f"مكتبات متوفرة: {', '.join(available)}")
    else:
        status.update(label=f"✅ {step['name']} - ناجح", state="complete")
        st.success(f"جميع المكتبات متوفرة ({len(available)} مكتبة)")

def _update_service_files_status(step, status, existing, missing):
    """Update status and display results for service files check"""
    if missing:
        status.update(label=f"❌ {step['name']} - فشل", state="error")
        st.error(f"ملفات مفقودة: {', '.join(missing)}")
    else:
        status.update(label=f"✅ {step['name']} - ناجح", state="complete")
        st.success(f"جميع ملفات الخدمات موجودة ({len(existing)} ملف)")

def _handle_library_check(step, status):
    """Handle library check step"""
    available, missing = check_libraries()
    _update_library_check_status(step, status, available, missing)
    return not bool(missing)

def _handle_service_files_check(step, status):
    """Handle service files check step"""
    existing, missing = check_service_files()
    _update_service_files_status(step, status, existing, missing)
    return not bool(missing)

def _handle_test_step(step, status, test_func):
    """Handle generic test step (processing, detection, coordinate, pipeline)"""
    success, message = test_func()
    if success:
        status.update(label=f"✅ {step['name']} - ناجح", state="complete")
        st.success(message)
        return True
    else:
        status.update(label=f"❌ {step['name']} - فشل", state="error")
        st.error(message)
        return False

def run_migration_step(step_index):
    """تشغيل خطوة تحول"""
    step = migration_steps[step_index]
    
    with st.status(f"جاري: {step['name']}...", expanded=True) as status:
        st.write(step['description'])
        time.sleep(0.5)
        
        try:
            test_func = step['test_function']
            
            if test_func == 'check_libraries':
                return _handle_library_check(step, status)
            elif test_func == 'check_service_files':
                return _handle_service_files_check(step, status)
            elif test_func == 'test_processing_service':
                return _handle_test_step(step, status, test_processing_service)
            elif test_func == 'test_detection_service':
                return _handle_test_step(step, status, test_detection_service)
            elif test_func == 'test_coordinate_extractor':
                return _handle_test_step(step, status, test_coordinate_extractor)
            elif test_func == 'test_full_pipeline':
                return _handle_test_step(step, status, test_full_pipeline)
            
        except Exception as e:
            status.update(label=f"❌ {step['name']} - خطأ", state="error")
            st.error(f"خطأ غير متوقع: {str(e)}")
            return False

# واجهة التحول
st.subheader("مراحل التحول")

completed_steps = st.session_state.get('completed_steps', [])
current_step = len(completed_steps)

if current_step < len(migration_steps):
    # عرض الخطوة الحالية
    current_step_info = migration_steps[current_step]
    
    st.info(f"**الخطوة الحالية ({current_step + 1}/{len(migration_steps)}):** {current_step_info['name']}")
    st.write(current_step_info['description'])
    
    if st.button(f"▶️ بدء {current_step_info['name']}", type="primary", use_container_width=True):
        success = run_migration_step(current_step)
        
        if success:
            completed_steps.append(current_step_info['name'])
            st.session_state.completed_steps = completed_steps
            time.sleep(1)
            st.rerun()
        else:
            st.error("فشلت الخطوة. راجع الأخطاء وحاول مرة أخرى.")
    
    # عرض التقدم
    st.divider()
    progress_value = current_step / len(migration_steps)
    st.progress(progress_value, text=f"التقدم: {current_step}/{len(migration_steps)} خطوات")
    
else:
    # اكتمال جميع الخطوات
    st.success("🎉 اكتمل التحول بنجاح!")
    st.balloons()
    
    st.subheader("ملخص التحول")
    for i, step_name in enumerate(completed_steps):
        st.write(f"✅ **الخطوة {i+1}:** {step_name}")
    
    st.divider()
    st.subheader("الخطوات التالية")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 الانتقال للوضع الفعلي", type="primary", use_container_width=True):
            st.session_state['demo_mode'] = False
            st.session_state['live_mode_initialized'] = False
            st.success("✅ تم التبديل للوضع الفعلي!")
            st.info("ارجع للصفحة الرئيسية واضغط 'تهيئة الوضع الفعلي'")
            time.sleep(2)
    
    with col2:
        if st.button("🔄 بدء تحول جديد", use_container_width=True):
            st.session_state.completed_steps = []
            st.rerun()

# عرض حالة التقدم
st.divider()
st.subheader("📊 التقدم الحالي")

col1, col2 = st.columns([2, 1])

with col1:
    for i, step in enumerate(migration_steps):
        if step['name'] in completed_steps:
            status = "✅"
        elif i == current_step:
            status = "🔄"
        else:
            status = "⏳"
        
        if step['name'] in completed_steps:
            label = "مكتمل"
        elif i == current_step:
            label = "قيد التنفيذ"
        else:
            label = "في الانتظار"
        
        st.write(f"{status} **{i+1}. {step['name']}** - {label}")

with col2:
    completion_rate = len(completed_steps) / len(migration_steps)
    st.metric("معدل الإكمال", f"{completion_rate*100:.0f}%")
    st.metric("الخطوات المتبقية", len(migration_steps) - len(completed_steps))
