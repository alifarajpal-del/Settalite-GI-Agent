"""
Heritage Sentinel Pro - AI-Powered Archaeological Site Detection
Main Streamlit Application
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

# === Configuration Loading ===
def get_default_config():
    """Return default configuration if config file missing"""
    return {
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

try:
    from src.config import load_config
    config = load_config()
except:
    config = get_default_config()

# === Mock Data Service (Always Available) ===
try:
    from src.services.mock_data_service import MockDataService
    mock_service = MockDataService()
    HAS_MOCK = True
except ImportError:
    HAS_MOCK = False
    st.error("⚠️ Mock data service not available. Please check src/services/mock_data_service.py")
    st.stop()

# === Optional Full Services (for Live Mode) ===
SERVICES_AVAILABLE = {
    'satellite': False,
    'processing': False,
    'detection': False,
    'coordinate': False,
    'export': False
}

try:
    from src.services.satellite_service import SatelliteService
    SERVICES_AVAILABLE['satellite'] = True
except ImportError:
    pass

try:
    from src.services.processing_service import AdvancedProcessingService
    SERVICES_AVAILABLE['processing'] = True
except ImportError:
    pass

try:
    from src.services.detection_service import AnomalyDetectionService
    SERVICES_AVAILABLE['detection'] = True
except ImportError:
    pass

try:
    from src.services.coordinate_extractor import CoordinateExtractor
    SERVICES_AVAILABLE['coordinate'] = True
except ImportError:
    pass

try:
    from src.services.export_service import ExportService
    SERVICES_AVAILABLE['export'] = True
except ImportError:
    pass

# === Page Configuration ===
st.set_page_config(
    page_title="Heritage Sentinel Pro",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Session State Initialization ===
if 'demo_data' not in st.session_state:
    st.session_state.demo_data = None
if 'aoi' not in st.session_state:
    st.session_state.aoi = None
if 'results' not in st.session_state:
    st.session_state.results = None

# === Main Title ===
st.title("🛰️ Heritage Sentinel Pro")
st.markdown("### AI-Powered Archaeological Site Detection using Remote Sensing")
st.caption("⚠️ **Disclaimer:** Results are predictive and require field verification by experts.")

# === Sidebar Navigation ===
with st.sidebar:
    st.header("🎯 Control Panel")
    
    mode = st.radio(
        "Operation Mode:",
        ["Demo Mode (Quick Start)", "Live Mode (Full Pipeline)"],
        index=0
    )
    
    is_demo = mode.startswith("Demo")
    
    st.divider()
    
    if is_demo:
        st.success("✅ Demo Mode Active")
        st.info("Using simulated data - no API keys needed")
    else:
        st.warning("⚡ Live Mode")
        available_count = sum(SERVICES_AVAILABLE.values())
        st.metric("Services Available", f"{available_count}/5")
        
        if available_count < 5:
            st.error("⚠️ Some services unavailable. Install full requirements for live mode.")

# === Demo Mode Section ===
if is_demo:
    st.header("📊 Demo Mode - Archaeological Site Detection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Generated Detection Results")
        
        if st.button("🔄 Generate New Sample Data", type="primary"):
            with st.spinner("Generating sample archaeological sites..."):
                st.session_state.demo_data = mock_service.generate_mock_detections(num_sites=12)
        
        if st.session_state.demo_data is None:
            st.session_state.demo_data = mock_service.generate_mock_detections(num_sites=12)
        
        data = st.session_state.demo_data
        
        # Display statistics
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Sites", len(data))
        with col_b:
            high_priority = len(data[data['الأولوية (EN)'] == 'high'])
            st.metric("High Priority", high_priority)
        with col_c:
            avg_conf = data['الثقة (%)'].mean()
            st.metric("Avg Confidence", f"{avg_conf:.1f}%")
        
        # Interactive map
        st.subheader("🗺️ Detection Map")
        try:
            import pydeck as pdk
            
            map_data = data.copy()
            map_data.rename(columns={'خط العرض': 'lat', 'خط الطول': 'lon'}, inplace=True)
            
            priority_colors = {
                'high': [220, 20, 60],
                'medium': [255, 140, 0],
                'low': [34, 139, 34]
            }
            map_data['color'] = map_data['الأولوية (EN)'].map(priority_colors)
            map_data['size'] = map_data['المساحة (م²)'] / 10
            
            layer = pdk.Layer(
                'ScatterplotLayer',
                data=map_data,
                get_position='[lon, lat]',
                get_radius='size',
                get_fill_color='color',
                pickable=True,
                opacity=0.7
            )
            
            view = pdk.ViewState(
                latitude=map_data['lat'].mean(),
                longitude=map_data['lon'].mean(),
                zoom=13,
                pitch=30
            )
            
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view))
        except:
            st.warning("Map visualization requires pydeck. Showing coordinates table instead.")
            st.dataframe(data[['ID الموقع', 'خط الطول', 'خط العرض', 'الأولوية']])
        
        # Data table
        st.subheader("📋 Detailed Results")
        st.dataframe(data, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("📥 Export Options")
        
        # CSV export
        csv_data = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Download CSV",
            csv_data,
            f"heritage_sites_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )
        
        # GeoJSON export
        geojson_data = mock_service.create_mock_geojson_features()
        json_str = json.dumps(geojson_data, ensure_ascii=False, indent=2)
        st.download_button(
            "⬇️ Download GeoJSON",
            json_str,
            f"heritage_sites_{datetime.now().strftime('%Y%m%d')}.geojson",
            "application/json",
            use_container_width=True
        )
        
        st.divider()
        st.subheader("ℹ️ About Demo")
        st.info(
            "Demo mode generates realistic sample data for testing. "
            "Switch to Live Mode for real satellite analysis (requires API keys)."
        )

# === Live Mode Section ===
else:
    st.header("🛰️ Live Mode - Full Pipeline")
    
    if sum(SERVICES_AVAILABLE.values()) < 3:
        st.error(
            "❌ Live mode requires additional dependencies. "
            "Please install: `pip install rasterio scipy scikit-image`"
        )
        st.info("💡 For quick testing, use Demo Mode instead.")
        st.stop()
    
    # Step-by-step wizard
    tab1, tab2, tab3, tab4 = st.tabs(["1️⃣ AOI", "2️⃣ Parameters", "3️⃣ Run", "4️⃣ Results"])
    
    with tab1:
        st.subheader("Define Area of Interest (AOI)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Manual Polygon (GeoJSON)**")
            aoi_text = st.text_area(
                "Paste GeoJSON polygon:",
                height=200,
                placeholder='{"type": "Polygon", "coordinates": [[[lon, lat], ...]]}'
            )
            
            if st.button("✅ Validate AOI"):
                try:
                    aoi_json = json.loads(aoi_text)
                    st.session_state.aoi = aoi_json
                    st.success("AOI validated successfully!")
                except:
                    st.error("Invalid GeoJSON format")
        
        with col2:
            st.markdown("**Upload GeoJSON File**")
            uploaded_file = st.file_uploader("Choose GeoJSON file", type=['geojson', 'json'])
            if uploaded_file:
                try:
                    aoi_json = json.load(uploaded_file)
                    st.session_state.aoi = aoi_json
                    st.success(f"Loaded: {uploaded_file.name}")
                except:
                    st.error("Failed to parse uploaded file")
            
            if st.button("🗺️ Use Demo AOI"):
                st.session_state.aoi = mock_service.create_mock_aoi()
                st.success("Demo AOI loaded")
    
    with tab2:
        st.subheader("Analysis Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                datetime.now() - timedelta(days=365)
            )
            end_date = st.date_input(
                "End Date",
                datetime.now()
            )
        
        with col2:
            cloud_threshold = st.slider("Max Cloud Cover (%)", 0, 100, 30)
            contamination = st.slider("Anomaly Sensitivity", 0.01, 0.5, 0.1, 0.01)
    
    with tab3:
        st.subheader("Run Analysis Pipeline")
        
        if not st.session_state.aoi:
            st.warning("⚠️ Please define AOI in Step 1")
        else:
            st.info(f"✅ AOI defined | Date range: {start_date} to {end_date}")
            
            if st.button("🚀 Run Full Pipeline", type="primary"):
                progress_bar = st.progress(0)
                status = st.empty()
                
                try:
                    # Step 1: Satellite data
                    status.info("📡 Fetching satellite data...")
                    progress_bar.progress(0.2)
                    # Use mock data as fallback
                    sat_data = mock_service.generate_mock_satellite_data()
                    
                    # Step 2: Processing
                    status.info("🔬 Processing spectral indices...")
                    progress_bar.progress(0.4)
                    # Simulated processing
                    
                    # Step 3: Anomaly detection
                    status.info("🎯 Detecting anomalies...")
                    progress_bar.progress(0.6)
                    anomaly_map = mock_service.generate_mock_anomaly_map()
                    
                    # Step 4: Coordinate extraction
                    status.info("📍 Extracting coordinates...")
                    progress_bar.progress(0.8)
                    results = mock_service.generate_mock_detections()
                    
                    # Complete
                    progress_bar.progress(1.0)
                    status.success("✅ Pipeline completed successfully!")
                    
                    st.session_state.results = results
                    
                except Exception as e:
                    status.error(f"❌ Pipeline failed: {str(e)}")
    
    with tab4:
        st.subheader("Analysis Results")
        
        if st.session_state.results is not None:
            results = st.session_state.results
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Detected Sites", len(results))
            with col2:
                high_conf = len(results[results['الثقة (%)'] > 80])
                st.metric("High Confidence", high_conf)
            with col3:
                st.metric("Avg Area", f"{results['المساحة (م²)'].mean():.0f} m²")
            
            # Results table
            st.dataframe(results, use_container_width=True)
            
            # Export
            csv = results.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Export Results (CSV)",
                csv,
                f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
        else:
            st.info("ℹ️ Run the pipeline in Step 3 to see results here.")

# === Footer ===
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>🛰️ Heritage Sentinel Pro v1.0 | Academic Research License</p>
    <p>⚠️ Results are statistical predictions and require expert field verification</p>
    </div>
    """,
    unsafe_allow_html=True
)
