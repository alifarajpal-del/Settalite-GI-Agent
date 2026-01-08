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
import json
import pydeck as pdk

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

try:
    from src.config.demo_mode import DEMO_MODE, MOCK_DATA_SOURCE, MOCK_SERVICE
except ImportError:
    DEMO_MODE = False
    MOCK_DATA_SOURCE = False
    MOCK_SERVICE = None

if 'demo_mode' not in st.session_state:
    st.session_state['demo_mode'] = DEMO_MODE

# استخدم القيمة من حالة الجلسة بدلاً من الثابت
ACTIVE_DEMO_MODE = st.session_state.get('demo_mode', DEMO_MODE)
USE_MOCK_DATA = bool(ACTIVE_DEMO_MODE and MOCK_DATA_SOURCE and MOCK_SERVICE)

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
    
    # إعدادات النظام وتبديل الوضع
    st.divider()
    st.subheader("⚙️ إعدادات النظام")
    
    # تهيئة حالة الوضع
    if 'demo_mode' not in st.session_state:
        st.session_state['demo_mode'] = DEMO_MODE
    
    # زر تبديل الوضع
    if st.button("🔄 تبديل الوضع (تجريبي/فعلي)", type="secondary", use_container_width=True):
        st.session_state['demo_mode'] = not st.session_state.get('demo_mode', True)
        st.rerun()
    
    # عرض حالة النظام
    current_demo_mode = st.session_state.get('demo_mode', True)
    status_color = "🟢" if current_demo_mode else "🔴"
    st.write(f"{status_color} **الوضع الحالي:** {'تجريبي' if current_demo_mode else 'فعلي'}")
    
    if not current_demo_mode:
        st.warning("⚠️ الوضع الفعلي يتطلب:")
        st.write("- 🔑 مفاتيح API للأقمار الصناعية")
        st.write("- ⏳ اتصال بالإنترنت")
        st.write("- 📡 بيانات حقيقية")
    
    st.divider()
    
    tab = st.radio(
        "اختر المهمة:",
        ["🎯 إدارة المنطقة", "🛰️ جلب البيانات", "🔍 تحليل متقدم", "📊 عرض النتائج", "📤 تصدير البيانات"],
        horizontal=False
    )
    
    with st.expander("معلومات النظام"):
        st.info(f"الإصدار: {config['app']['version']}")
        st.info(f"الدقة: {config['satellite']['providers']['sentinel']['resolution']}م")
        st.info("الحالة: ✅ جاهز")
        if USE_MOCK_DATA:
            st.warning("وضع تجريبي نشط - يتم استخدام بيانات تجريبية")

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

        if USE_MOCK_DATA and st.button("تحميل AOI تجريبية", use_container_width=True):
            st.session_state.aoi_geometry = MOCK_SERVICE.create_mock_aoi()
            st.success("تم إنشاء AOI تجريبية بناءً على الإعدادات الافتراضية")
    
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
        if USE_MOCK_DATA:
            st.warning("سيتم استخدام بيانات تجريبية ثابتة في هذا الوضع")
        
        if st.button("🚀 جلب البيانات", type="primary", use_container_width=True):
            with st.spinner("جاري جلب البيانات..."):
                try:
                    logger = setup_logger(config['paths']['outputs'])
                    if USE_MOCK_DATA:
                        data = MOCK_SERVICE.generate_mock_satellite_data()
                    else:
                        satellite_service = SatelliteService(config, logger)
                        data = satellite_service.download_sentinel_data(
                            st.session_state.aoi_geometry,
                            start_date.strftime("%Y-%m-%d"),
                            end_date.strftime("%Y-%m-%d"),
                            max_cloud_cover
                        )
                    
                    st.session_state.run_data['satellite_data'] = data
                    if USE_MOCK_DATA:
                        st.success("تم تحميل البيانات التجريبية بنجاح!")
                    else:
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

# ============================================================================
# قسم العرض التجريبي (يظهر فقط في DEMO_MODE)
# ============================================================================
if USE_MOCK_DATA:
    st.sidebar.divider()
    st.sidebar.subheader("🔄 أدوات العرض التجريبي")
    
    if st.sidebar.button("🔄 توليد بيانات وهمية جديدة", use_container_width=True):
        st.session_state['mock_data'] = MOCK_SERVICE.generate_mock_detections()
        st.session_state['mock_geojson'] = MOCK_SERVICE.create_mock_geojson_features()
        st.rerun()
    
    if 'mock_data' not in st.session_state:
        st.session_state['mock_data'] = MOCK_SERVICE.generate_mock_detections()
        st.session_state['mock_geojson'] = MOCK_SERVICE.create_mock_geojson_features()
    
    st.divider()
    st.subheader("📊 العرض التجريبي - بيانات وهمية")
    
    col_info, col_stats = st.columns([2, 1])
    
    with col_info:
        st.info(
            """
            **معلومات الوضع التجريبي:**
            - جميع البيانات المعروضة هي بيانات وهمية للاختبار
            - تم توليد 12 موقعاً افتراضياً في منطقة القاهرة التاريخية
            - انقر على 'توليد بيانات وهمية جديدة' لأخذ عينة مختلفة
            """
        )
    
    with col_stats:
        st.metric("عدد المواقع المكتشفة", len(st.session_state['mock_data']))
        st.metric(
            "متوسط مستوى الثقة",
            f"{st.session_state['mock_data']['الثقة (%)'].mean():.1f}%"
        )
        st.metric(
            "المواقع عالية الأولوية",
            int(
                len(
                    st.session_state['mock_data'][
                        st.session_state['mock_data']['الأولوية (EN)'] == 'high'
                    ]
                )
            )
        )
    
    st.subheader("🗺️ الخريطة التفاعلية للمواقع المكتشفة")
    map_data = st.session_state['mock_data'].copy()
    map_data.rename(columns={'خط العرض': 'lat', 'خط الطول': 'lon'}, inplace=True)
    priority_colors = {'high': [220, 20, 60], 'medium': [255, 140, 0], 'low': [34, 139, 34]}
    map_data['color_rgb'] = map_data['الأولوية (EN)'].map(priority_colors)
    map_data['color_rgb'] = map_data['color_rgb'].apply(
        lambda color: color if isinstance(color, list) else [0, 102, 204]
    )
    map_data['size'] = np.clip(map_data['المساحة (م²)'] / 15.0, 80, 400)
    mean_lat = map_data['lat'].mean()
    mean_lon = map_data['lon'].mean()
    layer = pdk.Layer(
        'ScatterplotLayer',
        data=map_data,
        get_position='[lon, lat]',
        get_radius='size',
        get_fill_color='color_rgb',
        pickable=True,
        opacity=0.7
    )
    view_state = pdk.ViewState(latitude=mean_lat, longitude=mean_lon, zoom=13, pitch=30)
    st.pydeck_chart(pdk.Deck(map_style='mapbox://styles/mapbox/light-v9', initial_view_state=view_state, layers=[layer]))
    
    st.subheader("📋 جدول البيانات التفصيلي")
    st.dataframe(
        st.session_state['mock_data'],
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID الموقع": st.column_config.TextColumn(width="medium"),
            "خط الطول": st.column_config.NumberColumn(format="%.6f"),
            "خط العرض": st.column_config.NumberColumn(format="%.6f"),
            "الثقة (%)": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
            "المساحة (م²)": st.column_config.NumberColumn(format="%d"),
        }
    )
    
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    
    with col_dl1:
        csv_data = st.session_state['mock_data'].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 تحميل البيانات (CSV)",
            data=csv_data,
            file_name=f"heritage_detections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col_dl2:
        json_data = json.dumps(
            st.session_state['mock_geojson'],
            ensure_ascii=False,
            indent=2
        ).encode('utf-8')
        st.download_button(
            label="📥 تحميل البيانات (GeoJSON)",
            data=json_data,
            file_name=f"heritage_detections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson",
            mime="application/json",
            use_container_width=True
        )
    
    with col_dl3:
        if st.button("🖨️ إنشاء تقرير سريع", use_container_width=True):
            outputs_dir = Path(config['paths']['outputs'])
            outputs_dir.mkdir(parents=True, exist_ok=True)
            report_path = outputs_dir / f"demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            report_lines = [
                "Heritage Sentinel Pro - Demo Report",
                f"Total detections: {len(st.session_state['mock_data'])}",
                f"Average confidence: {st.session_state['mock_data']['الثقة (%)'].mean():.1f}%",
                f"High priority: {int(len(st.session_state['mock_data'][st.session_state['mock_data']['الأولوية (EN)'] == 'high']))}",
            ]
            report_path.write_text("\n".join(report_lines), encoding='utf-8')
            st.success(f"تم إنشاء تقرير تجريبي: {report_path.name}")
    
    st.divider()
    st.caption("🔬 هذا قسم العرض التجريبي. للتحول إلى الوضع الفعلي قم بتعيين DEMO_MODE = False في الإعدادات.")

# ============================================================================
# قسم الوضع الفعلي
# ============================================================================
current_demo_mode = st.session_state.get('demo_mode', DEMO_MODE)

if not current_demo_mode and st.session_state.get('live_mode_initialized', False):
    st.divider()
    st.header("🛰️ الوضع الفعلي - تحليل حقيقي")
    
    # عرض حالة الخدمات
    st.subheader("حالة الخدمات")
    
    if 'live_services_status' in st.session_state:
        cols = st.columns(len(st.session_state.live_services_status))
        for idx, (service_name, status) in enumerate(st.session_state.live_services_status.items()):
            with cols[idx]:
                st.write(status)
                st.caption(service_name.replace('_', ' ').title())
    
    # معلومات AOI
    if st.session_state.get('aoi_geometry'):
        st.info("✅ منطقة الاهتمام (AOI) محددة وجاهزة للتحليل")
    else:
        st.warning("⚠️ يرجى تحديد منطقة الاهتمام (AOI) أولاً من تبويب 'إدارة المنطقة'")
    
    # تشغيل تحليل حقيقي
    if st.button("🚀 تشغيل تحليل حقيقي", type="primary", disabled=not st.session_state.get('aoi_geometry')):
        with st.spinner("جاري التحليل الحقيقي... قد يستغرق عدة دقائق"):
            try:
                # استخدام خدمة الوضع الفعلي
                from src.services.live_mode_service import LiveModeService
                live_service = LiveModeService()
                
                # تهيئة الخدمات
                services_status = live_service.initialize_services()
                st.session_state.live_services_status = services_status
                
                # تشغيل خط الأنابيب
                results = live_service.run_full_pipeline(
                    aoi_geometry=st.session_state.get('aoi_geometry'),
                    start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                    end_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                # عرض النتائج
                if results['status'] == 'completed':
                    st.success("✅ اكتمل التحليل الحقيقي!")
                    
                    # عرض النتائج
                    if results['detections']:
                        detections = results['detections']
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("المواقع المكتشفة", detections.get('total_detections', 0))
                        with col2:
                            high_conf = detections.get('statistics', {}).get('high_confidence_detections', 0)
                            st.metric("عالية الثقة", high_conf)
                        with col3:
                            success_rate = len([s for s in results['steps'].values() 
                                              if s['status'] == 'success']) / max(len(results['steps']), 1)
                            st.metric("معدل النجاح", f"{success_rate*100:.1f}%")
                        
                        # حفظ النتائج
                        st.session_state.coordinates = detections
                        
                        # عرض البيانات
                        if not detections['clusters'].empty:
                            st.subheader("📊 المواقع المكتشفة")
                            st.dataframe(
                                detections['clusters'][
                                    ['cluster_id', 'centroid_lat', 'centroid_lon', 
                                     'confidence', 'area_m2']
                                ].round(6),
                                use_container_width=True
                            )
                    
                    # عرض تفاصيل الخطوات
                    with st.expander("📋 تفاصيل خطوات التنفيذ"):
                        for step_name, step_info in results['steps'].items():
                            status_icon = "✅" if step_info['status'] == 'success' else "⚠️" if step_info['status'] == 'warning' else "❌"
                            st.write(f"{status_icon} **{step_name}:** {step_info['message']}")
                
                else:
                    st.error(f"❌ فشل التحليل: {results.get('error', 'سبب غير معروف')}")
                    
            except Exception as e:
                st.error(f"❌ خطأ في الوضع الفعلي: {str(e)}")
                st.info("💡 النصيحة: يمكنك الرجوع للوضع التجريبي أو التحقق من إعدادات API")
    
    # زر العودة للوضع التجريبي
    st.divider()
    if st.button("↩️ العودة للوضع التجريبي"):
        st.session_state['demo_mode'] = True
        st.rerun()

elif not current_demo_mode:
    # تهيئة الوضع الفعلي لأول مرة
    st.divider()
    st.warning("⚠️ الوضع الفعلي يحتاج تهيئة")
    
    st.info("""
    **متطلبات الوضع الفعلي:**
    - ✓ جميع الخدمات الأساسية مثبتة
    - ⚠️ مفاتيح API للأقمار الصناعية (اختياري - سيتم استخدام بيانات وهمية كبديل)
    - ✓ اتصال بالإنترنت
    """)
    
    if st.button("🛠️ تهيئة الوضع الفعلي", type="primary"):
        with st.spinner("جاري تهيئة الخدمات الفعلية..."):
            try:
                from src.services.live_mode_service import LiveModeService
                live_service = LiveModeService()
                services_status = live_service.initialize_services()
                
                st.session_state.live_services_status = services_status
                st.session_state.live_mode_initialized = True
                
                st.success("✅ تم تهيئة الوضع الفعلي بنجاح!")
                
                # عرض حالة الخدمات
                st.subheader("حالة الخدمات:")
                for service_name, status in services_status.items():
                    st.write(f"{status} {service_name}")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ فشل التهيئة: {str(e)}")
                st.info("""
                **الحلول المقترحة:**
                1. تأكد من وجود جميع ملفات الخدمات في مجلد `src/services/`
                2. تحقق من ملفات التكوين في `config/`
                3. جرب تثبيت المكتبات المطلوبة: `pip install scikit-learn rasterio`
                """)

# تذييل الصفحة
st.divider()
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.9em;">
<p>🛰️ Heritage Sentinel Pro v1.0 | نظام محمي بترخيص بحثي أكاديمي</p>
<p>⚠️ التحذير: هذا النظام ينتج توقعات إحصائية ولا يضمن وجود آثار فعلية</p>
</div>
""", unsafe_allow_html=True)
