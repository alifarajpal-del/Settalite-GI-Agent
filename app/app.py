"""
Heritage Sentinel Pro - AI-Powered Archaeological Site Detection
Modern SaaS Dashboard with Bilingual Support
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.pipeline_service import PipelineService, PipelineRequest, PipelineResult
from src.services.mock_data_service import MockDataService
from src.utils.dependency_errors import DependencyMissingError

# === Translations ===
TRANSLATIONS = {
    'en': {
        'title': "Heritage Sentinel Pro",
        'subtitle': "AI-Powered Archaeological Site Detection",
        'sidebar_language': "Language",
        'sidebar_settings': "Settings",
        'mode_demo': "Demo Mode",
        'mode_live': "Live Mode",
        'mode_label': "Operation Mode",
        'kpi_total_sites': "Total Sites",
        'kpi_avg_confidence': "Avg Confidence",
        'kpi_high_priority': "High Priority",
        'kpi_total_area': "Total Area (m²)",
        'run_analysis': "Run Analysis",
        'running': "Running Analysis...",
        'step_fetch': "Fetching satellite data...",
        'step_process': "Processing spectral indices...",
        'step_detect': "Detecting anomalies...",
        'step_extract': "Extracting coordinates...",
        'step_export': "Exporting results...",
        'error': "Error",
        'warning': "Warning",
        'success': "Success",
        'results': "Detection Results",
        'map_title': "Detection Map",
        'stats_title': "Statistics",
        'table_title': "Detailed Results",
        'export_section': "Export Data",
        'export_csv': "Download CSV",
        'export_geojson': "Download GeoJSON",
        'filter_priority': "Filter by Priority",
        'filter_confidence': "Min Confidence (%)",
        'filter_search': "Search (Site ID or Type)",
        'errors_title': "Errors Encountered",
        'warnings_title': "Warnings",
        'no_results': "No results available. Run an analysis first.",
        'footer': "Results are statistical predictions and require expert field verification",
        'theme_note': "Theme changes require page refresh",
        'demo_note': "Demo mode uses simulated data - no API keys required",
    },
    'ar': {
        'title': "هيريتج سنتينل برو",
        'subtitle': "الكشف عن المواقع الأثرية بالذكاء الاصطناعي",
        'sidebar_language': "اللغة",
        'sidebar_settings': "الإعدادات",
        'mode_demo': "الوضع التجريبي",
        'mode_live': "الوضع المباشر",
        'mode_label': "وضع التشغيل",
        'kpi_total_sites': "إجمالي المواقع",
        'kpi_avg_confidence': "متوسط الثقة",
        'kpi_high_priority': "أولوية عالية",
        'kpi_total_area': "إجمالي المساحة (م²)",
        'run_analysis': "تشغيل التحليل",
        'running': "جاري التحليل...",
        'step_fetch': "جلب بيانات الأقمار الصناعية...",
        'step_process': "معالجة المؤشرات الطيفية...",
        'step_detect': "كشف الشذوذات...",
        'step_extract': "استخراج الإحداثيات...",
        'step_export': "تصدير النتائج...",
        'error': "خطأ",
        'warning': "تحذير",
        'success': "نجح",
        'results': "نتائج الكشف",
        'map_title': "خريطة الكشف",
        'stats_title': "الإحصائيات",
        'table_title': "النتائج التفصيلية",
        'export_section': "تصدير البيانات",
        'export_csv': "تنزيل CSV",
        'export_geojson': "تنزيل GeoJSON",
        'filter_priority': "تصفية حسب الأولوية",
        'filter_confidence': "الحد الأدنى للثقة (%)",
        'filter_search': "بحث (معرف الموقع أو النوع)",
        'errors_title': "الأخطاء المواجهة",
        'warnings_title': "التحذيرات",
        'no_results': "لا توجد نتائج متاحة. قم بتشغيل التحليل أولاً.",
        'footer': "النتائج هي تنبؤات إحصائية وتتطلب التحقق الميداني من قبل الخبراء",
        'theme_note': "تتطلب تغييرات السمة تحديث الصفحة",
        'demo_note': "يستخدم الوضع التجريبي بيانات محاكاة - لا حاجة لمفاتيح API",
    }
}

# === Session State Initialization ===
if 'lang' not in st.session_state:
    st.session_state.lang = 'en'
if 'last_result' not in st.session_state:
    st.session_state.last_result = None
if 'last_request_params' not in st.session_state:
    st.session_state.last_request_params = None

# === Page Configuration ===
st.set_page_config(
    page_title="Heritage Sentinel Pro",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === RTL Styling for Arabic ===
def inject_rtl_css(lang: str):
    """Inject RTL CSS when Arabic is selected"""
    if lang == 'ar':
        st.markdown("""
        <style>
        .stApp {
            direction: rtl;
            text-align: right;
        }
        .stMarkdown, .stText {
            text-align: right;
        }
        /* Keep numbers and metrics LTR for readability */
        [data-testid="stMetricValue"] {
            direction: ltr;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp {
            direction: ltr;
            text-align: left;
        }
        </style>
        """, unsafe_allow_html=True)

# === Cached Demo Data Generation ===
@st.cache_data(ttl=300)
def get_demo_data():
    """Generate demo data with caching"""
    mock_service = MockDataService()
    return mock_service.generate_mock_detections(num_sites=15)

# === Render Results Dashboard ===
def render_results(result: PipelineResult, labels: dict):
    """
    Render comprehensive results dashboard.
    
    Args:
        result: PipelineResult object from pipeline execution
        labels: Translation labels dictionary
    """
    if not result or not result.success or result.dataframe is None:
        st.info(labels['no_results'])
        return
    
    df = result.dataframe
    
    # === 1. KPI Cards Row ===
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        # Total sites
        total_sites = len(df)
        col1.metric(labels['kpi_total_sites'], total_sites)
        
        # Average confidence
        if 'الثقة (%)' in df.columns:
            avg_conf = df['الثقة (%)'].mean()
            col2.metric(labels['kpi_avg_confidence'], f"{avg_conf:.1f}%")
        else:
            col2.metric(labels['kpi_avg_confidence'], "N/A")
        
        # High priority count
        if 'الأولوية (EN)' in df.columns:
            high_priority = len(df[df['الأولوية (EN)'] == 'high'])
            col3.metric(labels['kpi_high_priority'], high_priority)
        else:
            col3.metric(labels['kpi_high_priority'], "N/A")
        
        # Total area
        if 'المساحة (م²)' in df.columns:
            total_area = df['المساحة (م²)'].sum()
            col4.metric(labels['kpi_total_area'], f"{total_area:,.0f}")
        else:
            col4.metric(labels['kpi_total_area'], "N/A")
    
    st.divider()
    
    # === 2. Map + Summary Panel ===
    col_map, col_stats = st.columns([7, 3])
    
    with col_map:
        st.subheader(f"🗺️ {labels['map_title']}")
        
        # Prepare map data
        if 'خط العرض' in df.columns and 'خط الطول' in df.columns:
            map_df = df.copy()
            map_df['lat'] = map_df['خط العرض']
            map_df['lon'] = map_df['خط الطول']
            
            # Try pydeck for advanced visualization
            try:
                import pydeck as pdk
                
                # Color mapping for priorities
                priority_colors = {
                    'high': [220, 20, 60, 200],
                    'medium': [255, 165, 0, 180],
                    'low': [34, 139, 34, 160]
                }
                
                if 'الأولوية (EN)' in map_df.columns:
                    map_df['color'] = map_df['الأولوية (EN)'].map(priority_colors)
                else:
                    map_df['color'] = [[100, 100, 255, 180]] * len(map_df)
                
                # Size based on area
                if 'المساحة (م²)' in map_df.columns:
                    map_df['size'] = map_df['المساحة (م²)'] / 20
                else:
                    map_df['size'] = 100
                
                layer = pdk.Layer(
                    'ScatterplotLayer',
                    data=map_df,
                    get_position='[lon, lat]',
                    get_radius='size',
                    get_fill_color='color',
                    pickable=True,
                    auto_highlight=True
                )
                
                view_state = pdk.ViewState(
                    latitude=map_df['lat'].mean(),
                    longitude=map_df['lon'].mean(),
                    zoom=12,
                    pitch=30
                )
                
                st.pydeck_chart(pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip={"text": "Site: {ID الموقع}\nConfidence: {الثقة (%)}%"}
                ))
            except ImportError:
                # Fallback to basic Streamlit map
                st.map(map_df[['lat', 'lon']])
        else:
            st.warning("Map data not available (missing coordinates)")
    
    with col_stats:
        st.subheader(f"📊 {labels['stats_title']}")
        
        # Priority distribution
        if 'الأولوية (EN)' in df.columns:
            priority_counts = df['الأولوية (EN)'].value_counts()
            st.markdown("**Priority Distribution:**")
            for priority, count in priority_counts.items():
                st.markdown(f"- {priority.upper()}: {count}")
        
        st.divider()
        
        # Confidence distribution
        if 'الثقة (%)' in df.columns:
            st.markdown("**Confidence Range:**")
            st.markdown(f"- Min: {df['الثقة (%)'].min():.1f}%")
            st.markdown(f"- Max: {df['الثقة (%)'].max():.1f}%")
            st.markdown(f"- Median: {df['الثقة (%)'].median():.1f}%")
        
        st.divider()
        
        # Area statistics
        if 'المساحة (م²)' in df.columns:
            st.markdown("**Area Statistics:**")
            st.markdown(f"- Total: {df['المساحة (م²)'].sum():,.0f} m²")
            st.markdown(f"- Average: {df['المساحة (م²)'].mean():,.0f} m²")
    
    st.divider()
    
    # === 3. Filterable Table ===
    st.subheader(f"📋 {labels['table_title']}")
    
    # Filters in expandable section
    with st.expander("🔍 Filters", expanded=False):
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            if 'الأولوية (EN)' in df.columns:
                priorities = ['all'] + df['الأولوية (EN)'].unique().tolist()
                selected_priority = st.selectbox(labels['filter_priority'], priorities)
            else:
                selected_priority = 'all'
        
        with filter_col2:
            if 'الثقة (%)' in df.columns:
                min_confidence = st.slider(
                    labels['filter_confidence'],
                    0.0, 100.0, 0.0, 5.0
                )
            else:
                min_confidence = 0.0
        
        with filter_col3:
            search_text = st.text_input(labels['filter_search'], "")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_priority != 'all' and 'الأولوية (EN)' in df.columns:
        filtered_df = filtered_df[filtered_df['الأولوية (EN)'] == selected_priority]
    
    if 'الثقة (%)' in df.columns:
        filtered_df = filtered_df[filtered_df['الثقة (%)'] >= min_confidence]
    
    if search_text:
        mask = filtered_df.astype(str).apply(
            lambda row: row.str.contains(search_text, case=False, na=False).any(),
            axis=1
        )
        filtered_df = filtered_df[mask]
    
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(filtered_df)} of {len(df)} sites")
    
    st.divider()
    
    # === 4. Export Section ===
    st.subheader(f"📥 {labels['export_section']}")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        # CSV export
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"⬇️ {labels['export_csv']}",
            data=csv_data,
            file_name=f"heritage_sites_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with export_col2:
        # GeoJSON export
        if 'خط العرض' in filtered_df.columns and 'خط الطول' in filtered_df.columns:
            features = []
            for _, row in filtered_df.iterrows():
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [row['خط الطول'], row['خط العرض']]
                    },
                    "properties": row.to_dict()
                }
                features.append(feature)
            
            geojson_data = {
                "type": "FeatureCollection",
                "features": features
            }
            
            json_str = json.dumps(geojson_data, ensure_ascii=False, indent=2)
            st.download_button(
                label=f"⬇️ {labels['export_geojson']}",
                data=json_str,
                file_name=f"heritage_sites_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.button(
                label=f"⬇️ {labels['export_geojson']}",
                disabled=True,
                help="GeoJSON requires coordinate data",
                use_container_width=True
            )
    
    # === 5. Warnings Section ===
    if result.warnings:
        st.divider()
        with st.expander(f"⚠️ {labels['warnings_title']} ({len(result.warnings)})", expanded=False):
            for warning in result.warnings:
                st.warning(warning)
    
    # === 6. Errors Section (should be minimal in successful run) ===
    if result.errors:
        st.divider()
        with st.expander(f"❌ {labels['errors_title']} ({len(result.errors)})", expanded=False):
            for error in result.errors:
                st.error(error)
            st.info("💡 **Tip:** These errors were non-fatal. The pipeline completed with partial results.")


# === Main App ===
def main():
    # Get current language
    lang = st.session_state.lang
    labels = TRANSLATIONS[lang]
    
    # Inject RTL CSS if Arabic
    inject_rtl_css(lang)
    
    # === Sidebar ===
    with st.sidebar:
        st.header(f"🌐 {labels['sidebar_language']}")
        new_lang = st.radio(
            "Select / اختر",
            ['en', 'ar'],
            index=0 if lang == 'en' else 1,
            horizontal=True
        )
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()
        
        st.divider()
        
        st.header(f"⚙️ {labels['sidebar_settings']}")
        
        mode = st.radio(
            labels['mode_label'],
            [labels['mode_demo'], labels['mode_live']],
            index=0
        )
        
        is_demo = (mode == labels['mode_demo'])
        
        if is_demo:
            st.success("✅ Demo Mode Active")
            st.info(labels['demo_note'])
        else:
            st.warning("⚡ Live Mode")
            st.caption("Requires heavy dependencies and API keys")
        
        st.divider()
        st.caption(labels['theme_note'])
    
    # === Main Title ===
    st.title(f"🛰️ {labels['title']}")
    st.markdown(f"### {labels['subtitle']}")
    
    st.divider()
    
    # === Analysis Control Section ===
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{labels['run_analysis']}**")
        
        with col2:
            run_button = st.button(
                f"▶️ {labels['run_analysis']}",
                type="primary",
                use_container_width=True
            )
    
    # === Run Analysis ===
    if run_button:
        # Progress placeholder
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        try:
            # Initialize pipeline
            pipeline = PipelineService()
            
            # Create mock AOI for demo
            mock_service = MockDataService()
            aoi = mock_service.create_mock_aoi()
            
            # Create request
            request = PipelineRequest(
                aoi_geometry=aoi,
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                mode='demo' if is_demo else 'live',
                max_cloud_cover=30,
                contamination=0.1,
                export_formats=['geojson', 'csv'],
                output_dir='outputs',
                metadata={'app_version': '2.0', 'language': lang}
            )
            
            # Save request params
            st.session_state.last_request_params = {
                'mode': 'demo' if is_demo else 'live',
                'timestamp': datetime.now().isoformat()
            }
            
            # Execute pipeline with progress updates
            status_placeholder.info(f"⏳ {labels['step_fetch']}")
            progress_bar.progress(0.2)
            
            # Run pipeline (it handles all steps internally)
            result = pipeline.run(request)
            
            # Update progress for each step
            if result.step_completed and 'fetch' in result.step_completed.lower():
                status_placeholder.info(f"⏳ {labels['step_process']}")
                progress_bar.progress(0.4)
            
            if result.step_completed and 'process' in result.step_completed.lower():
                status_placeholder.info(f"⏳ {labels['step_detect']}")
                progress_bar.progress(0.6)
            
            if result.step_completed and 'detect' in result.step_completed.lower():
                status_placeholder.info(f"⏳ {labels['step_extract']}")
                progress_bar.progress(0.8)
            
            if result.step_completed and 'extract' in result.step_completed.lower():
                status_placeholder.info(f"⏳ {labels['step_export']}")
                progress_bar.progress(0.9)
            
            progress_bar.progress(1.0)
            
            # Store result in session state
            st.session_state.last_result = result
            
            # Check for errors
            if result.errors and not result.success:
                status_placeholder.error(f"❌ {labels['error']}: Pipeline failed")
                
                # Show friendly error messages
                with st.expander(f"🔍 {labels['errors_title']}", expanded=True):
                    for error in result.errors:
                        # Check for dependency errors
                        if 'DependencyMissingError' in error or 'missing' in error.lower():
                            st.error("⚠️ **Missing Dependencies**")
                            st.markdown(
                                "The pipeline requires additional libraries. "
                                "Please install them or switch to Demo Mode."
                            )
                            st.code("pip install -r requirements_geo.txt", language="bash")
                        else:
                            st.error(error)
                    
                    st.info("💡 **Next Steps:** Try Demo Mode or install missing dependencies.")
            
            elif result.warnings:
                status_placeholder.warning(f"⚠️ {labels['warning']}: Completed with warnings")
            else:
                status_placeholder.success(f"✅ {labels['success']}!")
            
            # Clear progress indicators after brief delay
            import time
            time.sleep(1)
            status_placeholder.empty()
            progress_bar.empty()
        
        except DependencyMissingError as e:
            progress_bar.empty()
            status_placeholder.error(f"❌ {labels['error']}: Missing dependencies")
            
            st.error("⚠️ **Missing Required Dependencies**")
            st.markdown(str(e))
            st.code("pip install -r requirements_geo.txt", language="bash")
            st.info("💡 **Tip:** Use Demo Mode to explore features without installing heavy libraries.")
        
        except Exception as e:
            progress_bar.empty()
            status_placeholder.error(f"❌ {labels['error']}: Unexpected error")
            
            st.error("⚠️ **Unexpected Error Occurred**")
            st.markdown("An error occurred during pipeline execution. Please try again.")
            
            # Show error details in expandable section (not full stacktrace)
            with st.expander("🔍 Error Details", expanded=False):
                st.code(f"{type(e).__name__}: {str(e)}", language="text")
            
            st.info("💡 **Tip:** Try Demo Mode for a guaranteed working experience.")
    
    # === Display Results ===
    if st.session_state.last_result:
        st.divider()
        st.header(f"📊 {labels['results']}")
        render_results(st.session_state.last_result, labels)
    
    # === Footer ===
    st.divider()
    footer_text = f"🛰️ Heritage Sentinel Pro v2.0 | {labels['footer']}"
    
    if lang == 'ar':
        st.markdown(
            f"""
            <div style='text-align: center; color: gray; font-size: 0.9em; direction: rtl;'>
            <p>{footer_text}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style='text-align: center; color: gray; font-size: 0.9em;'>
            <p>{footer_text}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()
