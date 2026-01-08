"""
صفحة تكوين النظام للوضع الفعلي
"""
import streamlit as st
import os
import sys
from pathlib import Path

# إضافة المسار للوحدات
sys.path.append(str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="تكوين النظام", page_icon="⚙️", layout="wide")

st.title("⚙️ تكوين Heritage Sentinel Pro")

# تبويبات التكوين
tab1, tab2, tab3, tab4 = st.tabs([
    "مقدمي البيانات", 
    "إعدادات التحليل",
    "المخرجات والتقارير",
    "اختبار النظام"
])

with tab1:
    st.header("🛰️ مقدمي بيانات الأقمار الصناعية")
    
    # Sentinel Hub
    with st.expander("Sentinel Hub API", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            sentinel_client_id = st.text_input("Client ID", type="password")
            sentinel_client_secret = st.text_input("Client Secret", type="password")
        with col2:
            sentinel_instance_id = st.text_input("Instance ID")
            sentinel_max_cloud = st.slider("الحد الأقصى للغيوم %", 0, 100, 30)
    
    # NASA Earthdata
    with st.expander("NASA Earthdata (Landsat)"):
        nasa_username = st.text_input("اسم المستخدم")
        nasa_password = st.text_input("كلمة المرور", type="password")
    
    # حفظ التكوين
    if st.button("💾 حفظ إعدادات البيانات", type="primary"):
        config_data = {
            "sentinel": {
                "client_id": sentinel_client_id,
                "client_secret": sentinel_client_secret,
                "instance_id": sentinel_instance_id,
                "max_cloud_cover": sentinel_max_cloud
            },
            "nasa": {
                "username": nasa_username,
                "password": nasa_password
            }
        }
        
        # حفظ في ملف
        try:
            import yaml
            config_path = Path(__file__).parent.parent.parent / "config" / "api_keys.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True)
            
            st.success("✅ تم حفظ إعدادات API")
        except Exception as e:
            st.error(f"❌ خطأ في الحفظ: {e}")

with tab2:
    st.header("🔍 إعدادات التحليل المتقدم")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("خوارزميات كشف الشذوذ")
        anomaly_algo = st.selectbox(
            "الخوارزمية:",
            ["Isolation Forest", "Local Outlier Factor", "One-Class SVM", "Autoencoder"],
            index=0
        )
        
        contamination = st.slider(
            "مستوى التلوث (contamination)",
            0.01, 0.5, 0.1, 0.01,
            help="النسبة المتوقعة للقيم الشاذة في البيانات"
        )
    
    with col2:
        st.subheader("استخراج الإحداثيات")
        confidence_threshold = st.slider(
            "عتبة الثقة %",
            50, 99, 70, 1
        )
        
        min_area = st.number_input(
            "أقل مساحة (م²)",
            10, 10000, 100, 10
        )
        
        cluster_distance = st.slider(
            "مسافة التجميع (متر)",
            10, 200, 50, 10
        )
    
    # مؤشرات طيفية
    st.subheader("📊 المؤشرات الطيفية")
    spectral_indices = st.multiselect(
        "اختر المؤشرات:",
        ["NDVI", "NDWI", "MSAVI", "NDBI", "NBR", "BAI", "TC_Greenness"],
        default=["NDVI", "NDWI", "MSAVI"]
    )
    
    if st.button("💾 حفظ إعدادات التحليل"):
        analysis_config = {
            "anomaly_detection": {
                "algorithm": anomaly_algo,
                "contamination": contamination
            },
            "coordinate_extraction": {
                "confidence_threshold": confidence_threshold / 100,
                "min_area_m2": min_area,
                "cluster_distance": cluster_distance
            },
            "spectral_indices": spectral_indices
        }
        
        try:
            import yaml
            config_path = Path(__file__).parent.parent.parent / "config" / "analysis_settings.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(analysis_config, f, allow_unicode=True)
            
            st.success("✅ تم حفظ إعدادات التحليل")
        except Exception as e:
            st.error(f"❌ خطأ في الحفظ: {e}")

with tab3:
    st.header("📤 إعدادات المخرجات والتقارير")
    
    output_formats = st.multiselect(
        "تنسيقات التصدير:",
        ["GeoJSON", "KML", "Shapefile", "CSV", "Excel", "PDF", "GeoTIFF"],
        default=["GeoJSON", "CSV", "PDF"]
    )
    
    coordinate_system = st.selectbox(
        "نظام الإحداثيات:",
        ["EPSG:4326 (WGS84)", "EPSG:32636 (UTM 36N)", "EPSG:3857 (Web Mercator)"],
        index=0
    )
    
    # إعدادات التقرير
    st.subheader("📊 إعدادات التقرير")
    report_language = st.radio("لغة التقرير:", ["العربية", "English", "كلاهما"], index=0)
    include_visualizations = st.checkbox("تضمين التصورات البيانية", value=True)
    include_recommendations = st.checkbox("تضمين التوصيات الميدانية", value=True)
    
    if st.button("💾 حفظ إعدادات المخرجات"):
        output_config = {
            "formats": output_formats,
            "coordinate_system": coordinate_system.split()[0],
            "report": {
                "language": report_language,
                "include_visualizations": include_visualizations,
                "include_recommendations": include_recommendations
            }
        }
        
        try:
            import yaml
            config_path = Path(__file__).parent.parent.parent / "config" / "output_settings.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(output_config, f, allow_unicode=True)
            
            st.success("✅ تم حفظ إعدادات المخرجات")
        except Exception as e:
            st.error(f"❌ خطأ في الحفظ: {e}")

with tab4:
    st.header("🧪 اختبار تكامل النظام")
    
    st.info("اختبار اتصال ووظائف النظام قبل الانتقال للوضع الفعلي")
    
    test_col1, test_col2, test_col3 = st.columns(3)
    
    with test_col1:
        if st.button("🔗 اختبار الاتصال بالإنترنت", use_container_width=True):
            try:
                import requests
                response = requests.get("https://www.google.com", timeout=5)
                st.success("✅ الاتصال بالإنترنت نشط")
            except Exception as e:
                st.error(f"❌ فشل الاتصال بالإنترنت: {e}")
    
    with test_col2:
        if st.button("📦 اختبار المكتبات", use_container_width=True):
            try:
                import numpy as np
                import pandas as pd
                import geopandas as gpd
                from sklearn.ensemble import IsolationForest
                st.success("✅ جميع المكتبات مثبتة")
            except ImportError as e:
                st.error(f"❌ مكتبة مفقودة: {e}")
    
    with test_col3:
        if st.button("🛠️ اختبار الخدمات", use_container_width=True):
            try:
                from src.services.coordinate_extractor import CoordinateExtractor
                from src.utils.logging_utils import setup_logger
                st.success("✅ الخدمات الأساسية جاهزة")
            except Exception as e:
                st.error(f"❌ خطأ في الخدمات: {e}")
    
    # اختبار شامل
    if st.button("🚀 تشغيل اختبار شامل", type="primary"):
        with st.spinner("جاري الاختبار الشامل..."):
            test_results = []
            
            # اختبار 1: البيانات الوهمية
            try:
                from src.services.mock_data_service import MockDataService
                mock = MockDataService()
                data = mock.generate_mock_detections()
                test_results.append(("البيانات الوهمية", "✅", f"{len(data)} موقع"))
            except Exception as e:
                test_results.append(("البيانات الوهمية", "❌", f"فشل: {e}"))
            
            # اختبار 2: نظام الملفات
            project_root = Path(__file__).parent.parent.parent
            required_dirs = ['data', 'outputs', 'exports', 'config']
            for dir_name in required_dirs:
                dir_path = project_root / dir_name
                if dir_path.exists():
                    test_results.append((f"مجلد {dir_name}", "✅", "موجود"))
                else:
                    test_results.append((f"مجلد {dir_name}", "⚠️", "مفقود"))
            
            # اختبار 3: ملفات التكوين
            config_files = ['config/config.yaml']
            for config_file in config_files:
                file_path = project_root / config_file
                if file_path.exists():
                    test_results.append((f"ملف {config_file}", "✅", "موجود"))
                else:
                    test_results.append((f"ملف {config_file}", "⚠️", "مفقود"))
            
            # عرض النتائج
            st.subheader("نتائج الاختبار الشامل")
            for test_name, status, details in test_results:
                st.write(f"{status} **{test_name}:** {details}")
            
            # التوصية
            success_count = sum(1 for _, status, _ in test_results if status == "✅")
            total_tests = len(test_results)
            
            if success_count == total_tests:
                st.success(f"🎉 جميع الاختبارات ({total_tests}) ناجحة! النظام جاهز للوضع الفعلي.")
            else:
                st.warning(f"⚠️ {success_count}/{total_tests} اختبارات ناجحة. راجع التحذيرات أعلاه.")

st.divider()
st.info("""
**ملاحظات هامة:**
1. تأكد من حفظ جميع التغييرات قبل الانتقال للوضع الفعلي
2. في الوضع الفعلي، سيتم استهلاك حصص API من مقدمي الخدمة
3. يمكنك الرجوع للوضع التجريبي في أي وقت
""")
