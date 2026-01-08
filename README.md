# 🛰️ Heritage Sentinel Pro

Advanced AI-powered system for detecting and precisely locating archaeological sites using remote sensing and machine learning.

[العربية](README_AR.md) | English

## ✨ Key Features

- 🎯 **Precise Coordinate Extraction** - Up to 10-meter accuracy
- 🤖 **Advanced ML Algorithms** - Isolation Forest, LOF, and more
- 📊 **Spectral Analysis** - NDVI, NDWI, MSAVI, NBR indices
- 🗺️ **Multi-format Support** - GeoJSON, KML, Shapefile, CSV
- 📤 **Comprehensive Export** - Multiple output formats with detailed reports

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

### Verify Installation

```bash
# Windows
.\scripts\verify.ps1

# Linux/Mac
python scripts/smoke_test.py && python test_integration.py
```

## 📖 Documentation

See [README_AR.md](README_AR.md) for full Arabic documentation.

## 📋 Project Structure

```
heritage-sensing-pro/
├── config/              # Configuration files
├── src/
│   ├── utils/          # Utility modules
│   ├── services/       # Core services
│   └── models/         # ML models
├── app/                # Streamlit application
├── data/               # Data directory
├── outputs/            # Outputs and logs
└── exports/            # Exported files
```

## ⚠️ Disclaimer

This system produces statistical predictions for research purposes only. Results require field verification and do not guarantee the presence of actual archaeological sites.

## 📄 License

MIT License - See LICENSE file for details.

---

Developed with ❤️ for cultural heritage protection