"""
التطبيق الرئيسي لمنصة Heritage Sentinel Pro
"""
import streamlit as st
import sys
from pathlib import Path
import geopandas as gpd
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# إضافة المسار للوحدات
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.config import load_config
    from src.utils.logging_utils import setup_logger
    from src.services.satellite_service import SatelliteService
    from src.services.processing_service import AdvancedProcessingService
    from src.services.detection_service import AnomalyDetectionService
    from src.services.coordinate_extractor import CoordinateExtractor
    from src.services.export_service import ExportService
except ImportError as e:
    st.error(f"خطأ في تحميل الوحدات: {e}")
    st.stop()

# إعداد الصفحة
st.set_page_config(
    page_title="Heritage Sentinel Pro",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تحميل التكوين
try:
    config = load_config()
except Exception as e:
    st.error(f"خطأ في تحميل التكوين: {e}")
    st.warning("استخدام إعدادات افتراضية")
    config = {
        'app': {'name': 'Heritage Sentinel Pro', 'version': '1.0.0'},
        'satellite': {'providers': {'sentinel': {'resolution': 10}}},
        'processing': {
            'coordinate_extraction': {
                'min_anomaly_area': 100,
                'confidence_threshold': 0.7,
                'cluster_distance': 50
            }
        },
        'output': {'formats': ['geojson', 'csv']},
        'paths': {'outputs': 'outputs', 'exports': 'exports'}
    }

# حالة الجلسة
if 'run_data' not in st.session_state:
    st.session_state.run_data = {}
if 'coordinates' not in st.session_state:
    st.session_state.coordinates = None
if 'aoi_geometry' not in st.session_state:
    st.session_state.aoi_geometry = None

# العنوان الرئيسي
st.title("🛰️ Heritage Sentinel Pro")
st.markdown("""
### نظام كشف وتحديد الإحداثيات الدقيقة للمواقع الأثرية باستخدام الذكاء الاصطناعي
*منصة احترافية للاستشعار عن بعد وتحليل البيانات الفضائية*
""")

# الشريط الجانبي
with st.sidebar:
    st.title("مركز التحكم")
    
    tab = st.radio(
        "اختر المهمة:",
        ["🎯 إدارة المنطقة", "🛰️ جلب البيانات", "🔍 تحليل متقدم", "📊 عرض النتائج", "📤 تصدير البيانات"],
        horizontal=False
    )
    
    with st.expander("معلومات النظام"):
        st.info(f"الإصدار: {config['app']['version']}")
        st.info(f"الدقة: {config['satellite']['providers']['sentinel']['resolution']}م")
        st.info("الحالة: ✅ جاهز")

# علامة تبويب إدارة المنطقة
if tab == "🎯 إدارة المنطقة":
    st.header("🎯 تحديد منطقة الاهتمام (AOI)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        input_method = st.radio(
            "طريقة الإدخال:",
            ["إحداثيات يدوية", "GeoJSON ملف", "WKT نص"]
        )
        
        if input_method == "إحداثيات يدوية":
            col_lat, col_lon = st.columns(2)
            with col_lat:
                min_lat = st.number_input("الحد الأدنى لخط العرض", value=30.0)
                max_lat = st.number_input("الحد الأقصى لخط العرض", value=31.0)
            with col_lon:
                min_lon = st.number_input("الحد الأدنى لخط الطول", value=30.0)
                max_lon = st.number_input("الحد الأقصى لخط الطول", value=31.0)
            
            if st.button("إنشاء AOI"):
                from shapely.geometry import Polygon
                polygon = Polygon([
                    (min_lon, min_lat),
                    (max_lon, min_lat),
                    (max_lon, max_lat),
                    (min_lon, max_lat),
                    (min_lon, min_lat)
                ])
                st.session_state.aoi_geometry = polygon
                st.success("✅ تم إنشاء AOI!")
        
        elif input_method == "GeoJSON ملف":
            geojson_file = st.file_uploader("رفع ملف GeoJSON", type=['geojson', 'json'])
            if geojson_file:
                import json
                geojson_data = json.load(geojson_file)
                st.session_state.aoi_geometry = geojson_data
                st.success("✅ تم تحميل ملف GeoJSON!")
    
    with col2:
        st.subheader("معلومات AOI")
        if st.session_state.aoi_geometry:
            try:
                if hasattr(st.session_state.aoi_geometry, 'area'):
                    area_km2 = st.session_state.aoi_geometry.area * 111 * 111
                    st.metric("المساحة (كم²)", f"{area_km2:.2f}")
                st.success("AOI جاهز للمعالجة")
            except:
                st.info("AOI محمل")

# علامة تبويب جلب البيانات
elif tab == "🛰️ جلب البيانات":
    st.header("🛰️ جلب بيانات الأقمار الصناعية")
    
    if st.session_state.aoi_geometry is None:
        st.warning("⚠️ الرجاء تحديد منطقة الاهتمام أولاً")
        st.stop()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        satellite_source = st.selectbox(
            "القمر الصناعي:",
            ["Sentinel-2", "Landsat 8/9"],
            index=0
        )
        
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input(
                "تاريخ البداية",
                datetime.now() - timedelta(days=365)
            )
        with col_end:
            end_date = st.date_input(
                "تاريخ النهاية",
                datetime.now()
            )
        
        max_cloud_cover = st.slider("الحد الأقصى لتغطية الغيوم (%)", 0, 100, 30)
    
    with col2:
        st.subheader("معاينة الطلب")
        st.info(f"**القمر الصناعي:** {satellite_source}")
        st.info(f"**الفترة:** {start_date} إلى {end_date}")
        
        if st.button("🚀 جلب البيانات", type="primary", use_container_width=True):
            with st.spinner("جاري جلب البيانات..."):
                try:
                    logger = setup_logger(config['paths']['outputs'])
                    satellite_service = SatelliteService(config, logger)
                    
                    data = satellite_service.download_sentinel_data(
                        st.session_state.aoi_geometry,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        max_cloud_cover
                    )
                    
                    st.session_state.run_data['satellite_data'] = data
                    st.success("✅ تم جلب البيانات بنجاح!")
                    
                except Exception as e:
                    st.error(f"خطأ: {str(e)}")

# علامة تبويب التحليل المتقدم
elif tab == "🔍 تحليل متقدم":
    st.header("🔍 تحليل متقدم باستخدام الذكاء الاصطناعي")
    
    if 'satellite_data' not in st.session_state.run_data:
        st.warning("⚠️ الرجاء جلب بيانات الأقمار الصناعية أولاً")
        st.stop()
    
    analysis_tabs = st.tabs(["المؤشرات الطيفية", "كشف الشذوذ", "استخراج الإحداثيات"])
    
    with analysis_tabs[0]:
        st.subheader("المؤشرات الطيفية المتقدمة")
        
        if st.button("🧮 حساب المؤشرات", type="secondary"):
            with st.spinner("جاري حساب المؤشرات..."):
                try:
                    logger = setup_logger(config['paths']['outputs'])
                    processor = AdvancedProcessingService(config, logger)
                    
                    bands_data = st.session_state.run_data['satellite_data']['bands']
                    indices_results = processor.calculate_spectral_indices(bands_data)
                    
                    st.session_state.run_data['indices'] = indices_results
                    st.success(f"✅ تم حساب {len(indices_results)} مؤشر")
                    
                    # عرض المؤشرات
                    for name, data in indices_results.items():
                        with st.expander(f"مؤشر {name}"):
                            fig = px.imshow(data, title=name, color_continuous_scale='viridis')
                            st.plotly_chart(fig, use_container_width=True)
                            
                except Exception as e:
                    st.error(f"خطأ: {str(e)}")
    
    with analysis_tabs[1]:
        st.subheader("كشف الشذوذ")
        
        contamination = st.slider("مستوى التلوث", 0.01, 0.5, 0.1, 0.01)
        
        if st.button("🔍 بدء الكشف", type="primary"):
            with st.spinner("جاري كشف الأنماط الشاذة..."):
                try:
                    logger = setup_logger(config['paths']['outputs'])
                    detector = AnomalyDetectionService(config, logger)
                    
                    if 'indices' not in st.session_state.run_data:
                        st.warning("الرجاء حساب المؤشرات أولاً")
                    else:
                        anomaly_map = detector.detect_anomalies(
                            st.session_state.run_data['indices'],
                            contamination=contamination
                        )
                        
                        st.session_state.run_data['anomaly_map'] = anomaly_map
                        st.success("✅ تم كشف الأنماط الشاذة!")
                        
                        fig = px.imshow(
                            anomaly_map['anomaly_surface'],
                            title="خريطة الشذوذ",
                            color_continuous_scale='hot'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                except Exception as e:
                    st.error(f"خطأ: {str(e)}")
    
    with analysis_tabs[2]:
        st.subheader("استخراج الإحداثيات الدقيقة")
        
        if 'anomaly_map' not in st.session_state.run_data:
            st.warning("⚠️ الرجاء تشغيل كشف الشذوذ أولاً")
        else:
            confidence_threshold = st.slider("عتبة الثقة (%)", 50, 99, 70, 1) / 100
            
            if st.button("📍 استخراج الإحداثيات", type="primary"):
                with st.spinner("جاري استخراج الإحداثيات..."):
                    try:
                        logger = setup_logger(config['paths']['outputs'])
                        extractor = CoordinateExtractor(config, logger)
                        
                        coordinates_result = extractor.extract_precise_coordinates(
                            st.session_state.run_data['anomaly_map']['anomaly_surface'],
                            st.session_state.run_data['satellite_data']['transform'],
                            st.session_state.run_data['satellite_data']['crs'],
                            st.session_state.aoi_geometry
                        )
                        
                        st.session_state.coordinates = coordinates_result
                        st.success(f"✅ تم استخراج {coordinates_result['total_detections']} إحداثية!")
                        
                        if not coordinates_result['clusters'].empty:
                            st.dataframe(
                                coordinates_result['clusters'][
                                    ['cluster_id', 'centroid_lat', 'centroid_lon', 
                                     'confidence', 'area_m2']
                                ].round(6),
                                use_container_width=True
                            )
                        
                    except Exception as e:
                        st.error(f"خطأ: {str(e)}")

# علامة تبويب عرض النتائج
elif tab == "📊 عرض النتائج":
    st.header("📊 لوحة تحكم النتائج")
    
    if st.session_state.coordinates is None:
        st.warning("⚠️ لا توجد نتائج لعرضها")
        st.stop()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "إجمالي المواقع",
            st.session_state.coordinates['total_detections']
        )
    
    with col2:
        st.metric(
            "متوسط الثقة",
            f"{st.session_state.coordinates['statistics'].get('avg_confidence', 0):.1%}"
        )
    
    with col3:
        st.metric(
            "المساحة الإجمالية",
            f"{st.session_state.coordinates['statistics'].get('total_area_m2', 0):,.0f} م²"
        )
    
    with col4:
        st.metric(
            "كثافة الاكتشاف",
            f"{st.session_state.coordinates['statistics'].get('density_per_km2', 0):.1f}/كم²"
        )
    
    if not st.session_state.coordinates['clusters'].empty:
        st.subheader("توزيع مستويات الثقة")
        fig = px.histogram(
            st.session_state.coordinates['clusters'],
            x='confidence',
            nbins=20,
            title='توزيع مستويات الثقة'
        )
        st.plotly_chart(fig, use_container_width=True)

# علامة تبويب تصدير البيانات
elif tab == "📤 تصدير البيانات":
    st.header("📤 تصدير النتائج")
    
    if st.session_state.coordinates is None:
        st.warning("⚠️ لا توجد نتائج للتصدير")
        st.stop()
    
    export_formats = st.multiselect(
        "اختر تنسيقات التصدير:",
        ["GeoJSON", "CSV", "Excel"],
        default=["GeoJSON", "CSV"]
    )
    
    if st.button("💾 تصدير جميع النتائج", type="primary"):
        with st.spinner("جاري تصدير البيانات..."):
            try:
                import os
                logger = setup_logger(config['paths']['outputs'])
                export_service = ExportService(config, logger)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = f"heritage_detections_{timestamp}"
                
                # إنشاء مجلد exports إذا لم يكن موجوداً
                os.makedirs(config['paths']['exports'], exist_ok=True)
                
                export_results = export_service.export_all(
                    st.session_state.coordinates['clusters'],
                    export_formats,
                    config['paths']['exports'],
                    base_name
                )
                
                st.success("✅ تم التصدير بنجاح!")
                
                for fmt, path in export_results.items():
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            st.download_button(
                                label=f"تحميل {fmt}",
                                data=f,
                                file_name=os.path.basename(path),
                                mime="application/octet-stream"
                            )
                
            except Exception as e:
                st.error(f"خطأ في التصدير: {str(e)}")

# تذييل الصفحة
st.divider()
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.9em;">
<p>🛰️ Heritage Sentinel Pro v1.0 | نظام محمي بترخيص بحثي أكاديمي</p>
<p>⚠️ التحذير: هذا النظام ينتج توقعات إحصائية ولا يضمن وجود آثار فعلية</p>
</div>
""", unsafe_allow_html=True)
