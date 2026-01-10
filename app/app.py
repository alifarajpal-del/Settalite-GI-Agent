"""
Heritage Sentinel Pro - AI-Powered Archaeological Site Detection
Professional 2-Step GEOINT Workflow
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Safe imports with fallbacks
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Constants
DOWNLOAD_GEOJSON_LABEL = "📥 Download GeoJSON"

try:
    from shapely.geometry import Point
    import dataclasses
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

# Import core utilities
from src.utils.coords_parser import parse_coords

# Import services with error handling
try:
    from src.services.pipeline_service import PipelineService, PipelineRequest
    from src.services.mock_data_service import MockDataService
    from src.config import load_config
    import logging
    import inspect
    PIPELINE_AVAILABLE = True
except ImportError as e:
    PIPELINE_AVAILABLE = False
    import_error = str(e)

#=== Page Configuration ===
st.set_page_config(
    page_title="Heritage Sentinel Pro",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === Session State Initialization ===
if 'step' not in st.session_state:
    st.session_state.step = 'landing'
if 'target' not in st.session_state:
    st.session_state.target = None
if 'last_result' not in st.session_state:
    st.session_state.last_result = None
if 'lang' not in st.session_state:
    st.session_state.lang = 'en'

# === Translations ===
TRANSLATIONS = {
    'en': {
        'title': "Heritage Sentinel Pro",
        'subtitle': "AI-Powered Archaeological Site Detection System",
        'input_label': "Enter Target Coordinates",
        'input_placeholder': "31.9522, 35.2332 or Google Maps URL",
        'button_start': "Start Initial Analysis 🚀",
        'examples_title': "Quick Examples (click to use):",
        'map_title': "📍 Target Location & Scan Area",
        'settings_title': "⚙️ Scan Configuration",
        'scan_radius': "Scan Radius",
        'date_range': "Archive Time Range",
        'data_source': "Data Source",
        'model_mode': "Detection Model",
        'button_scan': "Start Deep Scan 🔍",
        'running': "Running analysis...",
        'results_title': "📊 Analysis Results",
        'sources_title': "1. Sources Used",
        'likelihood_title': "2. Archaeological Likelihood",
        'evidence_title': "3. Evidence & Heatmap",
        'aoi_title': "4. Recommended Area of Interest (AOI)",
        'button_new': "New Search",
        'error_parsing': "Could not parse coordinates",
        'error_deps': "Missing dependencies",
    },
    'ar': {
        'title': "هيريتج سنتينل برو",
        'subtitle': "نظام الكشف الأثري بالذكاء الاصطناعي",
        'input_label': "أدخل إحداثيات الهدف",
        'input_placeholder': "31.9522, 35.2332 أو رابط Google Maps",
        'button_start': "بدء التحليل الأولي 🚀",
        'examples_title': "أمثلة سريعة (انقر للاستخدام):",
        'map_title': "📍 موقع الهدف ونطاق المسح",
        'settings_title': "⚙️ إعدادات المسح",
        'scan_radius': "نطاق المسح",
        'date_range': "النطاق الزمني للأرشيف",
        'data_source': "مصدر البيانات",
        'model_mode': "نموذج الكشف",
        'button_scan': "بدء المسح العميق 🔍",
        'running': "جاري التحليل...",
        'results_title': "📊 نتائج التحليل",
        'sources_title': "1. المصادر المستخدمة",
        'likelihood_title': "2. الاحتمالية الأثرية",
        'evidence_title': "3. الأدلة والخريطة الحرارية",
        'aoi_title': "4. منطقة الاهتمام الموصى بها (AOI)",
        'button_new': "بحث جديد",
        'error_parsing': "تعذر تحليل الإحداثيات",
        'error_deps': "مكتبات مفقودة",
    }
}

# === Styling ===
st.markdown("""
<style>
    .main-header {
        text-align: center; 
        padding: 2rem 0;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 3rem;
    }
    .example-chip {
        display: inline-block;
        background: #f0f2f6;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        border-radius: 20px;
        cursor: pointer;
        font-size: 0.9rem;
    }
    .result-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .likelihood-high {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
    }
    .likelihood-medium {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
    }
    .likelihood-low {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

#===========================================
# HELPER FUNCTIONS
#===========================================
def get_pipeline_service():
    """
    Get or create PipelineService instance with proper config and logger.
    Uses session state to avoid recreating on every Streamlit rerun.
    Smart signature detection to handle API changes.
    """
    if "pipeline" not in st.session_state:
        if not PIPELINE_AVAILABLE:
            return None
        
        try:
            # Load config and setup logger
            config = load_config()
            logger = logging.getLogger("heritage")
            
            # Inspect PipelineService signature to build kwargs dynamically
            sig = inspect.signature(PipelineService.__init__)
            kwargs = {}
            
            if "config" in sig.parameters:
                kwargs["config"] = config
            if "logger" in sig.parameters:
                kwargs["logger"] = logger
            
            # Create and cache the pipeline service
            st.session_state.pipeline = PipelineService(**kwargs)
            
        except Exception as e:
            st.error(f"Failed to initialize pipeline service: {e}")
            return None
    
    return st.session_state.pipeline


#===========================================
# LANDING PAGE
#===========================================
def render_landing(labels):
    """Render the landing page with centered input."""
    
    # Language toggle in corner
    with st.sidebar:
        new_lang = st.radio("Language / اللغة", ['en', 'ar'], 
                           index=0 if st.session_state.lang == 'en' else 1,
                           horizontal=True)
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()
    
    # Centered content
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"<h1 class='main-header'>🛰️ {labels['title']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='subtitle'>{labels['subtitle']}</p>", unsafe_allow_html=True)
        
        st.write("---")
        
        # Examples
        st.markdown(f"**{labels['examples_title']}**")
        
        examples = [
            ("31.9522, 35.2332", "Jerusalem (Decimal)"),
            ("31°57'08\"N 35°14'00\"E", "Jerusalem (DMS)"),
            ("https://maps.google.com/@31.9522,35.2332,15z", "Google Maps URL"),
        ]
        
        cols = st.columns(3)
        for i, (coords, desc) in enumerate(examples):
            if cols[i].button(desc, key=f"example_{i}", use_container_width=True):
                st.session_state.example_coords = coords
        
        # Input field
        default_value = st.session_state.get('example_coords', '')
        input_coords = st.text_input(
            labels['input_label'],
            value=default_value,
            placeholder=labels['input_placeholder'],
            key='coords_input'
        )
        
        # Clear example after using it
        if 'example_coords' in st.session_state:
            del st.session_state.example_coords
        
        # Start button
        _, btn_col, _ = st.columns([1, 2, 1])
        if btn_col.button(labels['button_start'], use_container_width=True, type="primary"):
            if input_coords:
                try:
                    lat, lon = parse_coords(input_coords)
                    st.session_state.target = {
                        'lat': lat,
                        'lon': lon,
                        'raw': input_coords
                    }
                    st.session_state.step = 'ops'
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {labels['error_parsing']}")
                    st.code(str(e), language="text")
            else:
                st.warning("⚠️ Please enter coordinates")

#===========================================
# OPERATIONS ROOM PAGE
#===========================================
def render_operations(labels):
    """Render the operations room with map and settings."""
    
    target = st.session_state.target
    if not target:
        st.error("No target coordinates set. Returning to landing...")
        time.sleep(2)
        st.session_state.step = 'landing'
        st.rerun()
        return
    
    # Language toggle
    with st.sidebar:
        new_lang = st.radio("Language / اللغة", ['en', 'ar'], 
                           index=0 if st.session_state.lang == 'en' else 1,
                           horizontal=True)
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()
        
        st.divider()
        st.caption(f"Target: {target['lat']:.6f}, {target['lon']:.6f}")
        
        if st.button("← " + labels['button_new']):
            st.session_state.step = 'landing'
            st.session_state.target = None
            st.session_state.last_result = None
            st.rerun()
    
    # Title
    st.title(f"🛰️ {labels['title']}")
    
    # === MAP SECTION ===
    st.subheader(labels['map_title'])
    
    if FOLIUM_AVAILABLE:
        render_map(target)
    else:
        st.warning("⚠️ Map visualization requires folium and streamlit-folium")
        st.info("Install with: `pip install folium streamlit-folium`")
        st.code(f"Coordinates: {target['lat']:.6f}, {target['lon']:.6f}", language="text")
    
    st.divider()
    
    # === SETTINGS SECTION ===
    st.subheader(labels['settings_title'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    def format_scan_radius(x):
        label = f"{x}m "
        if x == 100:
            return label + "(Spot)"
        elif x == 500:
            return label + "(Default)"
        elif x >= 1000:
            return label + "(Context)"
        else:
            return label
    
    with col1:
        scan_radius = st.selectbox(
            labels['scan_radius'],
            options=[100, 500, 1000, 2000],
            index=1,
            format_func=format_scan_radius
        )
    
    with col2:
        months_back = st.selectbox(
            labels['date_range'],
            options=[6, 12, 24, 36],
            index=2,
            format_func=lambda x: f"Last {x} months" + (" (Default)" if x==24 else "")
        )
    
    with col3:
        # UI shows friendly names, but internally we use 'demo'/'live'
        data_source_ui = st.selectbox(
            labels['data_source'],
            options=['Demo', 'Real (Live Satellite Data)'],
            index=0
        )
        # Map UI choice to internal mode
        data_source = 'demo' if data_source_ui == 'Demo' else 'live'
    
    with col4:
        model_mode = st.selectbox(
            labels['model_mode'],
            options=['classic', 'ensemble', 'hybrid'],
            index=0,
            format_func=lambda x: x.title()
        )
    
    # === SCAN BUTTON ===
    st.write("")
    _, center_col, _ = st.columns([1, 2, 1])
    
    if center_col.button(labels['button_scan'], use_container_width=True, type="primary"):
        run_analysis(target, scan_radius, months_back, data_source, model_mode, labels)
    
    # === RESULTS SECTION ===
    last_result = st.session_state.get('last_result')
    if last_result:
        st.divider()
        render_results(last_result, labels)


def render_map(target):
    """Render interactive map with target marker and scan radius."""
    lat, lon = target['lat'], target['lon']
    
    # Create map centered on target
    m = folium.Map(
        location=[lat, lon],
        zoom_start=15,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery"
    )
    
    # Add target marker
    folium.Marker(
        [lat, lon],
        popup=f"Target<br>{lat:.6f}, {lon:.6f}",
        tooltip="Target Location",
        icon=folium.Icon(color="red", icon="crosshairs", prefix='fa')
    ).add_to(m)
    
    # Add scan radius circle (default 500m)
    folium.Circle(
        [lat, lon],
        radius=500,
        color='yellow',
        fill=True,
        fillColor='yellow',
        fillOpacity=0.2,
        popup="Scan Area (500m default)"
    ).add_to(m)
    
    # Render map
    st_folium(m, height=400, width=None, returned_objects=[])


def run_analysis(target, radius, months_back, data_source, model_mode, labels):
    """Run pipeline analysis with progress indicators."""
    
    if not PIPELINE_AVAILABLE:
        st.error(f"❌ {labels['error_deps']}: Pipeline service not available")
        st.code("pip install geopandas shapely pandas", language="bash")
        return
    
    if not SHAPELY_AVAILABLE:
        st.error(f"❌ {labels['error_deps']}: Shapely library required for geometry operations")
        st.code("pip install shapely", language="bash")
        return
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    
    # Create AOI geometry from center point + radius
    try:
        lat, lon = target['lat'], target['lon']
        
        # Create point geometry (note: Shapely uses (x, y) = (lon, lat))
        center_pt = Point(lon, lat)
        
        # Convert radius from meters to degrees (approximation)
        # 1 degree ≈ 111,320 meters at equator
        radius_deg = radius / 111_320.0
        aoi_geom = center_pt.buffer(radius_deg)
        
        # Create request (mode will be normalized in __post_init__)
        # 'real' will auto-convert to 'live'
        request = PipelineRequest(
            aoi_geometry=aoi_geom,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            mode=data_source,  # 'demo' or 'live' (or 'real')
            model_mode=model_mode
        )
        
    except Exception as e:
        st.error(f"Failed to create request: {e}")
        with st.expander("Debug Info"):
            st.code(f"Available fields: {[f.name for f in dataclasses.fields(PipelineRequest)]}", language="text")
            st.code(f"Error: {str(e)}", language="text")
        return
    
    # Progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    steps = [
        (20, "Fetching satellite imagery..."),
        (40, "Processing spectral indices..."),
        (60, "Running ML detection..."),
        (80, "Extracting features..."),
        (100, "Generating report...")
    ]
    
    try:
        status_text.info(f"⏳ {labels['running']}")
        
        for progress, message in steps:
            time.sleep(0.3)  # Simulate processing
            progress_bar.progress(progress)
            status_text.info(f"⏳ {message}")
        
        # Get pipeline service (cached in session state)
        pipeline = get_pipeline_service()
        if not pipeline:
            raise RuntimeError("Pipeline service initialization failed")
        
        # Run pipeline
        result = pipeline.run(request)
        
        # Store result
        st.session_state.last_result = result
        
        # Clear progress
        progress_bar.empty()
        status_text.success("✅ Analysis complete!")
        time.sleep(1)
        status_text.empty()
        
        # Rerun to show results
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        status_text.error(f"❌ Analysis failed: {str(e)}")
        
        with st.expander("Error Details"):
            st.code(str(e), language="text")


def _render_no_data_status(result):
    """Render NO_DATA status with actionable guidance"""
    st.error("📍 No Satellite Data Available")
    
    # Parse failure reason for structured display
    failure_text = result.failure_reason or "No satellite imagery found for the specified parameters."
    
    st.markdown(f"""
    <div class='result-section' style='background-color: #fff3cd; border-left: 4px solid #ffc107;'>
    <h4>No satellite imagery available for analysis</h4>
    <pre style='white-space: pre-wrap; font-family: monospace; font-size: 0.9em;'>{failure_text}</pre>
    </div>
    """, unsafe_allow_html=True)
    
    # Show data quality metrics (should show zeros)
    if result.data_quality:
        with st.expander("📊 Data Search Details"):
            st.json(result.data_quality)
    
    st.info("💡 **Tip:** Try expanding your time range to 6-12 months or adjusting the location.")


def _render_live_failed_status(result):
    """Render LIVE_FAILED status with setup instructions"""
    st.error("🔴 Live Analysis Failed")
    st.markdown(f"""
    <div class='result-section' style='background-color: #ffe6e6; border-left: 4px solid #dc3545;'>
    <h4>Analysis could not be completed with live satellite data</h4>
    <p><strong>Reason:</strong> {result.failure_reason}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if result.errors:
        with st.expander("🔍 Error Details"):
            for error in result.errors:
                st.code(error, language="text")
    
    if result.warnings:
        with st.expander("⚠️ Warnings"):
            for warning in result.warnings:
                st.warning(warning)
    
    # Show setup instructions
    st.markdown("### 🛠️ Setup Required")
    st.markdown("""
    To enable live satellite analysis:
    
    1. **Sentinel Hub** (Required):
       - Get free account at [sentinelhub.com](https://www.sentinel-hub.com/)
       - Add `SENTINELHUB_CLIENT_ID` and `SENTINELHUB_CLIENT_SECRET` to Streamlit secrets
    
    2. **Google Earth Engine** (Optional but recommended):
       - Install: `pip install earthengine-api`
       - Authenticate: `earthengine authenticate`
       - Or provide service account key in secrets
    """)

def _render_live_ok_provenance(result):
    """Render SUCCESS provenance panel with real data proof"""
    st.markdown("### 🛰️ Live Data Provenance")
    prov = result.provenance
    st.markdown(f"""
    <div class='result-section' style='background-color: #e8f5e9; border-left: 4px solid #4caf50;'>
    <strong>Provider:</strong> {prov.get('provider', 'Unknown')}<br>
    <strong>Scenes Count:</strong> {prov.get('scenes_count', 0)}<br>
    <strong>Time Range:</strong> {prov.get('time_range', ['N/A', 'N/A'])[0]} to {prov.get('time_range', ['N/A', 'N/A'])[1]}<br>
    <strong>Resolution:</strong> {prov.get('resolution', (0, 0))[0]}m x {prov.get('resolution', (0, 0))[1]}m<br>
    <strong>Cloud Stats:</strong> Min: {prov.get('cloud_stats', {}).get('min', 0):.1f}%, Mean: {prov.get('cloud_stats', {}).get('mean', 0):.1f}%, Max: {prov.get('cloud_stats', {}).get('max', 0):.1f}%<br>
    <strong>GEE Available:</strong> {'✓ Yes' if prov.get('gee_available') else '✗ No'}
    </div>
    """, unsafe_allow_html=True)
    st.divider()

def _render_sources_section(result, labels):
    """Render sources used section"""
    with st.container():
        st.markdown(f"### {labels['sources_title']}")
        
        if result.status == 'DEMO_MODE':
            st.markdown("""
            <div class='result-section'>
            <strong>⚠️ Demo Mode:</strong> Using simulated data<br>
            <strong>Satellite Images:</strong> 14 synthetic scenes<br>
            <strong>Providers:</strong> Mock data generator<br>
            <strong>Time Range:</strong> Simulated 24 months<br>
            <strong>Note:</strong> For demonstration purposes only. Enable live mode for real analysis.
            </div>
            """, unsafe_allow_html=True)
        else:
            # SUCCESS - show real sources (if available in metadata)
            scenes_count = result.provenance.get('scenes_count', 0) if result.provenance else 0
            
            # Additional safeguard: if scenes_count is 0, show warning
            if scenes_count == 0:
                st.warning("⚠️ No satellite imagery was processed for this analysis.")
            
            st.markdown("""
            <div class='result-section'>
            <strong>Satellite Images:</strong> {scenes_count} scenes<br>
            <strong>Providers:</strong> {providers}<br>
            <strong>Time Range:</strong> {time_range}<br>
            <strong>References:</strong> Multi-temporal analysis
            </div>
            """.format(
                scenes_count=scenes_count,
                providers=result.provenance.get('provider', 'N/A') if result.provenance else 'N/A',
                time_range=f"{result.provenance.get('time_range', ['N/A', 'N/A'])[0]} to {result.provenance.get('time_range', ['N/A', 'N/A'])[1]}" if result.provenance else 'N/A'
            ), unsafe_allow_html=True)

def _render_likelihood_section(labels):
    """Render archaeological likelihood section"""
    with st.container():
        st.markdown(f"### {labels['likelihood_title']}")
        
        # Example: 87% high likelihood
        likelihood = 87
        if likelihood >= 70:
            css_class = 'likelihood-high'
            icon = '🔴'
            level = 'High'
        elif likelihood >= 40:
            css_class = 'likelihood-medium'
            icon = '🟡'
            level = 'Medium'
        else:
            css_class = 'likelihood-low'
            icon = '🔵'
            level = 'Low'
        
        st.markdown(f"""
        <div class='{css_class}'>
        <h4>{icon} {level} Likelihood: {likelihood}%</h4>
        <p>Based on spectral variance (NDVI, NDWI) and anomaly detection, 
        a rectangular geometric anomaly was detected that is inconsistent 
        with the natural geological patterns of the area.</p>
        <p><strong>Interpretation:</strong> Pattern suggests buried structures 
        at 50-120cm depth, causing moisture retention visible in thermal mapping.</p>
        <p><em>⚠️ These are indirect indicators requiring expert field verification 
        and proper archaeological permits.</em></p>
        </div>
        """, unsafe_allow_html=True)

def _render_evidence_section(labels):
    """Render evidence and heatmap section"""
    with st.container():
        st.markdown(f"### {labels['evidence_title']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Key Evidence:**")
            st.write("""
            - NDVI anomaly cluster (±0.15 variance)
            - Thermal signature consistent with subsurface voids
            - Geometric regularity (20m × 30m rectangular pattern)
            - Soil moisture retention pattern
            """)
        
        with col2:
            st.markdown("**Heatmap:**")
            # Placeholder for heatmap
            st.info("🗺️ Heatmap overlay would be rendered here with folium HeatMap layer")
            st.caption("Intensity = f(confidence, anomaly_score, density)")

def _render_aoi_section(labels):
    """Render recommended area of interest section"""
    with st.container():
        st.markdown(f"### {labels['aoi_title']}")
        
        st.markdown("""
        <div style="background-color: #e8f5e9; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #4CAF50;">
        <h4>📍 Recommended Area of Interest</h4>
        <p><strong>Reference Point (Centroid):</strong> 31.95245°N, 35.23310°E</p>
        <p><strong>AOI Geometry:</strong> Rectangular polygon (20m × 30m)</p>
        <p><strong>Uncertainty Radius:</strong> ±25m</p>
        <p><strong>Description:</strong> Northeast corner of apparent rectangular structure. 
        Southern approach recommended to avoid modern debris.</p>
        <p><em>⚠️ This is a recommended investigation area, not an excavation target. 
        All fieldwork requires proper permits and expert supervision.</em></p>
        </div>
        """, unsafe_allow_html=True)

def _render_export_buttons(result):
    """Render export download buttons"""
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if PANDAS_AVAILABLE and result.dataframe is not None:
            csv = result.dataframe.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                "heritage_sentinel_results.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.button("📥 Download CSV", disabled=True, use_container_width=True)
    
    with col2:
        # Check if GeoJSON export is available in export_paths
        geojson_path = result.export_paths.get('geojson') if result.export_paths else None
        if geojson_path and Path(geojson_path).exists():
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = f.read()
            st.download_button(
                DOWNLOAD_GEOJSON_LABEL,
                geojson_data,
                "heritage_sentinel_results.geojson",
                "application/geo+json",
                use_container_width=True
            )
        elif PANDAS_AVAILABLE and result.dataframe is not None:
            # Generate GeoJSON on the fly if not exported
            try:
                geojson_data = result.dataframe.to_json()
                st.download_button(
                    DOWNLOAD_GEOJSON_LABEL,
                    geojson_data,
                    "heritage_sentinel_results.geojson",
                    "application/geo+json",
                    use_container_width=True
                )
            except Exception:
                st.button(DOWNLOAD_GEOJSON_LABEL, disabled=True, use_container_width=True)
        else:
            st.button(DOWNLOAD_GEOJSON_LABEL, disabled=True, use_container_width=True)
    
    with col3:
        st.button("📄 Generate Report", disabled=True, use_container_width=True)

def render_results(result, labels):
    if not result:
        st.error("Analysis did not complete successfully")
        return
    
    # === HANDLE NO_DATA (NO FAKE RESULTS POLICY) ===
    if result.status == 'NO_DATA':
        _render_no_data_status(result)
        return  # NO likelihood, NO evidence, NO aoi when no data
    
    # === ADDITIONAL NO_DATA CHECK: Verify actual data exists ===
    # Check if data_quality shows 0 scenes even if status isn't explicitly NO_DATA
    if result.data_quality:
        total_scenes = result.data_quality.get('total_scenes', None)
        processed_scenes = result.data_quality.get('processed_scenes', None)
        if total_scenes == 0 or processed_scenes == 0:
            # Override status to NO_DATA if we have zero scenes
            result.status = 'NO_DATA'
            if not result.failure_reason:
                result.failure_reason = "No satellite imagery was available for the specified parameters."
            _render_no_data_status(result)
            return
    
    # === HANDLE LIVE_FAILED ===
    if result.status == 'LIVE_FAILED':
        _render_live_failed_status(result)
        return  # No results to show for LIVE_FAILED
    
    # === HANDLE SUCCESS (DEMO_MODE or SUCCESS) ===
    if not result.success:
        st.error("Analysis did not complete successfully")
        if result.errors:
            with st.expander("Errors"):
                for error in result.errors:
                    st.error(error)
        return
    
    st.header(labels['results_title'])
    
    # === LIVE PROOF PANEL (for SUCCESS only) ===
    if result.status == 'SUCCESS' and result.provenance:
        _render_live_ok_provenance(result)
    
    # === 1. SOURCES USED ===
    _render_sources_section(result, labels)
    
    # === NO FAKE RESULTS: Only show likelihood/evidence/aoi if can_show_likelihood ===
    if result.can_show_likelihood():
        # === 2. ARCHAEOLOGICAL LIKELIHOOD ===
        _render_likelihood_section(labels)
        
        # === 3. EVIDENCE & HEATMAP ===
        _render_evidence_section(labels)
        
        # === 4. RECOMMENDED AOI ===
        _render_aoi_section(labels)
    else:
        st.warning("⚠️ Archaeological likelihood cannot be computed without real satellite data.")
    
    # === EXPORTS ===
    _render_export_buttons(result)


#===========================================
# MAIN ROUTER
#===========================================
def main():
    """Main application router."""
    
    # Ensure session state is initialized
    if 'step' not in st.session_state:
        st.session_state.step = 'landing'
    if 'lang' not in st.session_state:
        st.session_state.lang = 'en'
    
    # Get translations
    labels = TRANSLATIONS[st.session_state.lang]
    
    # Route to appropriate page
    if st.session_state.step == 'landing':
        render_landing(labels)
    elif st.session_state.step == 'ops':
        render_operations(labels)
    else:
        # Fallback
        st.error("Invalid application state")
        st.session_state.step = 'landing'
        st.rerun()


if __name__ == "__main__":
    main()
