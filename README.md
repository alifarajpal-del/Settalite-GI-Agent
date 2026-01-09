# 🛰️ Heritage Sentinel Pro

Advanced AI-powered system for detecting and precisely locating archaeological sites using remote sensing and machine learning.

[العربية](README_AR.md) | English

## ✨ Key Features

### Core Detection
- 🎯 **Precise Coordinate Extraction** - Up to 10-meter accuracy
- 🤖 **Advanced ML Algorithms** - Isolation Forest, LOF, Ensemble Models
- 📊 **Spectral Analysis** - NDVI, NDWI, MSAVI, NBR indices
- 🗺️ **Multi-format Support** - GeoJSON, KML, Shapefile, CSV
- 📤 **Comprehensive Export** - Validated exports with RFC 7946 compliance

### Advanced Capabilities (NEW)
- 🏛️ **Synthetic Heritage Generator** - Create realistic test datasets with architectural patterns
- 🔄 **Hybrid Data Service** - Combine real, synthetic, and benchmark data seamlessly
- ✅ **Schema Normalizer** - Automatic handling of Arabic/English columns
- 📦 **Benchmark Support** - EuroSAT dataset integration (opt-in)
- 🎨 **Bilingual UI** - Full Arabic/English support throughout

## 🚀 Quick Start

### Demo Mode (Lightweight - Recommended for Testing)

```bash
# Install core dependencies only
pip install -r requirements_core.txt

# Run the application
streamlit run app/app.py
```

Demo mode works with simulated data - no API keys or heavy libraries needed!

### Live Mode (Full Pipeline - Requires Geo Libraries)

```bash
# Install core + geo dependencies
pip install -r requirements_core.txt -r requirements_geo.txt

# Configure API keys (optional)
cp config/config.yaml.example config/config.yaml
# Edit config.yaml with your credentials

# Run the application
streamlit run app/app.py
```
### ML Features (Optional - Enhanced Detection)

```bash
# Install ML dependencies for advanced features
pip install -r requirements_ml.txt

# Test ML models
python scripts/test_models.py
```

ML features include:
- Heritage detection ensemble models
- Feature extraction (NDVI, texture, shape)
- Anomaly detection with IsolationForest
- Benchmark dataset support (EuroSAT)

### Verify Installation

```bash
# Core components
python scripts/smoke_test.py

# ML models
python scripts/test_models.py

# Final 15% integration (new)
python scripts/test_final_15.py

# Full integration
python test_integration.py
```

## 📖 Documentation

### Quick References
- [Installation Guide](docs/installation.md)
- [Configuration](docs/configuration.md)
- [API Reference](docs/api.md)
- [Arabic Documentation](README_AR.md)

### New Features Documentation

#### Synthetic Heritage Generator
Generate realistic archaeological site patterns for testing:

```python
from src.services.synthetic_heritage_generator import SyntheticHeritageGenerator

generator = SyntheticHeritageGenerator(seed=42)
sites = generator.generate(
    aoi_bbox=(46.5, 24.5, 46.9, 24.9),  # Riyadh area
    pattern='mixed',  # grid, organic, axial, random, mixed
    num_sites=50
)
```

#### Hybrid Data Service
Combine multiple data sources:

```python
from src.services.hybrid_data_service import HybridDataService

service = HybridDataService()
combined = service.combine_sources({
    'real': real_detections_df,
    'synthetic': synthetic_df,
    'mock': demo_df
}, deduplicate=True)
```

#### Schema Normalizer
Automatic normalization of Arabic/English columns:

```python
from src.utils.schema_normalizer import normalize_detections

# Works with mixed Arabic/English data
normalized = normalize_detections(raw_dataframe)
# Output: canonical schema (id, lat, lon, confidence, priority, area_m2, site_type)
```

#### GeoJSON Validator
RFC 7946 compliant export with validation:

```python
from src.utils.geojson_validator import create_valid_geojson, quick_geojson_test

geojson_bytes = create_valid_geojson(dataframe)
is_valid = quick_geojson_test(geojson_bytes)  # Always validates before export
```

## 📋 Project Structure

```
heritage-sensing-pro/
├── config/              # Configuration files
├── src/
│   ├── utils/          # Utilities (normalizer, validator)
│   ├── services/       # Core services + generators
│   ├── models/         # ML models (ensemble, detector)
│   └── ml/             # Feature extraction
├── app/                # Streamlit application
├── data/               # Data directory
│   └── benchmarks/     # Optional EuroSAT dataset
├── outputs/            # Outputs and logs
├── exports/            # Exported files
├── scripts/            # Test scripts
│   ├── smoke_test.py           # Basic validation
│   ├── test_models.py          # ML model tests
│   └── test_final_15.py        # Integration tests
└── requirements_*.txt  # Modular dependencies
```

## 🧪 Testing

### Test Hierarchy
1. **Smoke Test** (`scripts/smoke_test.py`) - Basic component availability
2. **Model Tests** (`scripts/test_models.py`) - ML model functionality
3. **Final 15% Tests** (`scripts/test_final_15.py`) - New features integration
4. **Full Integration** (`test_integration.py`) - End-to-end pipeline

### Run All Tests

```bash
# Quick verification
python scripts/smoke_test.py

# ML models (if installed)
python scripts/test_models.py

# New features comprehensive test
python scripts/test_final_15.py

# Full pipeline
python test_integration.py
```

## 🔧 Configuration

### Minimal Configuration (Demo Mode)
No configuration needed! Just run:
```bash
streamlit run app/app.py
```

### Full Configuration (Live Mode)
```yaml
# config/config.yaml
sentinel_hub:
  api_key: "your_api_key"
  instance_id: "your_instance_id"

processing:
  max_cloud_cover: 20
  anomaly_algorithm: "isolation_forest"
  
ml:
  model_mode: "hybrid"  # classic, ensemble, hybrid
  feature_extraction: true
```

## ⚠️ Disclaimer

This system produces statistical predictions for research purposes only. Results require field verification and do not guarantee the presence of actual archaeological sites.

## 📄 License

MIT License - See LICENSE file for details.

---

Developed with ❤️ for cultural heritage protection