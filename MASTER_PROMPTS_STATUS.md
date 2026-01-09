# Master PROMPTS Implementation - Heritage Sentinel Pro

## System Goal (PROMPT 0)

**"تحديد مؤشرات غير مباشرة لاحتمال وجود فراغات/غرف/دفائن مدفونة عبر آثار سطحية/قريبة من السطح، وليس كشف مباشر تحت الأرض."**

### Hard Rules

1. **LIVE_FAILED** → No likelihood, no heatmap, no fake results
2. Results are called **"Indirect Archaeological Indicators"** only
3. Output: **Recommended Investigation AOI + Uncertainty + Evidence Breakdown**
4. No "dig here" instructions

---

## Implementation Status

### ✅ Completed (Current Commit)

1. **PROMPT 1 - Fixed API Mismatches**:
   - ✅ UI shows "Demo" vs "Real" but internally uses 'demo'/'live'
   - ✅ Mode validation: only 'demo' or 'live' allowed
   - ✅ PipelineRequest uses `aoi_geometry` (not center_lat/lon)
   - ✅ PipelineService initialized with `config` and `logger`

2. **PROMPT 3 - Live Engine Structure**:
   - ✅ `src/services/sentinelhub_fetcher.py` - Sentinel Hub integration skeleton
   - ✅ `src/services/gee_analyzer.py` - Google Earth Engine analyzer skeleton
   - ✅ Pipeline integration with provenance tracking

3. **PROMPT 5 - No-Fake-Live Contract**:
   - ✅ PipelineResult now has `status: 'DEMO_OK' | 'LIVE_OK' | 'LIVE_FAILED'`
   - ✅ `provenance` field for live data metadata
   - ✅ `failure_reason` for LIVE_FAILED cases
   - ✅ UI renders LIVE PROOF PANEL for LIVE_OK
   - ✅ UI shows clear failure message for LIVE_FAILED (no fake results)
   - ✅ Demo mode clearly labeled

### 🔄 In Progress

4. **PROMPT 3 - Complete Live Implementation**:
   - ⏳ Sentinel Hub Catalog API integration (scene metadata query)
   - ⏳ GEE multi-temporal NDVI/NDWI analysis
   - ⏳ SAR (Sentinel-1) moisture/roughness proxy
   - ⏳ Actual imagery download and processing

5. **PROMPT 4 - Indirect Likelihood Model**:
   - ⏳ Evidence signals: veg_anomaly, moisture_anomaly, geometric_regularity
   - ⏳ Multi-source agreement scoring
   - ⏳ Persistence score calculation
   - ⏳ Coverage quality checks
   - ⏳ Uncertainty estimation

### ⏳ Pending

6. **PROMPT 6 - Streamlit Cloud Setup**:
   - ⏳ Add secrets documentation
   - ⏳ Test with real Sentinel Hub credentials
   - ⏳ GEE service account integration

---

## Live Mode Setup (PROMPT 6)

### Sentinel Hub (Required for Live Mode)

1. **Get Free Account**:
   - Go to [https://www.sentinel-hub.com/](https://www.sentinel-hub.com/)
   - Sign up (free tier: 10,000 Processing Units/month)
   - Create OAuth client in [Dashboard → User Settings → OAuth Clients](https://apps.sentinel-hub.com/dashboard/#/account/settings)

2. **Configure Streamlit Cloud Secrets**:
   ```toml
   # .streamlit/secrets.toml (or Streamlit Cloud secrets UI)
   [sentinelhub]
   client_id = "your-client-id-here"
   client_secret = "your-client-secret-here"
   ```

3. **Local Testing**:
   ```bash
   # Set environment variables
   export SENTINELHUB_CLIENT_ID="your-client-id"
   export SENTINELHUB_CLIENT_SECRET="your-client-secret"
   ```

### Google Earth Engine (Optional but Recommended)

**Local Development**:
```bash
# Install
pip install earthengine-api

# Authenticate (opens browser)
earthengine authenticate
```

**Streamlit Cloud** (Service Account):
1. Create GEE service account: [https://developers.google.com/earth-engine/guides/service_account](https://developers.google.com/earth-engine/guides/service_account)
2. Download JSON key file
3. Add to Streamlit secrets:
   ```toml
   [gee]
   service_account_key = "/path/to/key.json"
   ```
   Or paste entire JSON as string:
   ```toml
   [gee]
   service_account_json = '''
   {
     "type": "service_account",
     "project_id": "your-project",
     ...
   }
   '''
   ```

---

## Current Behavior

### Demo Mode (Works Now)
- Status: `DEMO_OK`
- Uses synthetic data
- Clear "Demo Mode" labeling
- Results are illustrative only

### Live Mode (Partial - Returns LIVE_FAILED)
- Status: `LIVE_FAILED`
- Reason: `IMPLEMENTATION_PENDING: Live imagery processing in development`
- Shows setup instructions
- No fake results

**Next Steps**: Complete Sentinel Hub Catalog API integration + GEE multi-temporal analysis.

---

## Testing

```bash
# Syntax validation
python -m py_compile app/app.py src/services/pipeline_service.py

# Run locally
streamlit run app/app.py

# Test mode validation
# 1. Select "Demo" → should work (DEMO_OK)
# 2. Select "Real" → should fail gracefully (LIVE_FAILED with clear message)
```

---

## Commit Message Template

```
feat(live): Master PROMPTS implementation - No-Fake-Live contract

PROMPT 1: Fix mode validation (real→live)
- UI shows "Demo" vs "Real (Live Satellite Data)"
- Internal mode: 'demo' or 'live' only
- Added validation to reject invalid modes

PROMPT 3: Live engine structure
- Created SentinelHubFetcher with provenance tracking
- Created GoogleEarthEngineAnalyzer for multi-temporal analysis
- Integrated into PipelineService with LIVE_FAILED returns

PROMPT 5: No-Fake-Live contract enforcement
- PipelineResult.status: DEMO_OK | LIVE_OK | LIVE_FAILED
- Added provenance field for live data metadata
- Added failure_reason for LIVE_FAILED
- UI shows LIVE PROOF PANEL for LIVE_OK
- UI shows clear failure + setup instructions for LIVE_FAILED
- Demo mode clearly labeled (no confusion)

Status: Core architecture complete, awaiting:
- Sentinel Hub Catalog API implementation
- GEE multi-temporal analysis
- Full imagery processing pipeline

Dependencies added:
- sentinelhub>=3.9.0
- earthengine-api>=0.1.350
```
