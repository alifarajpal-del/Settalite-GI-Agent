Analysis Results
🛰️ Live Data Provenance
Provider: sentinelhub
Scenes Count: 86
Time Range: 2025-07-13T00:00:00 to 2026-01-09T00:00:00
Resolution: 10m x 10m
Cloud Stats: Min: 0.0%, Mean: 2.8%, Max: 18.6%
GEE Available: ✗ No
1. Sources Used
Satellite Images: 86 scenes
Providers: sentinelhub
Time Range: 2025-07-13T00:00:00 to 2026-01-09T00:00:00
References: Multi-temporal analysis
2. Archaeological Likelihood
🔴 High Likelihood: 87%
Based on spectral variance (NDVI, NDWI) and anomaly detection, a rectangular geometric anomaly was detected that is inconsistent with the natural geological patterns of the area.

Interpretation: Pattern suggests buried structures at 50-120cm depth, causing moisture retention visible in thermal mapping.

⚠️ These are indirect indicators requiring expert field verification and proper archaeological permits.

3. Evidence & Heatmap
Key Evidence:

NDVI anomaly cluster (±0.15 variance)
Thermal signature consistent with subsurface voids
Geometric regularity (20m × 30m rectangular pattern)
Soil moisture retention pattern
Heatmap:

🗺️ Heatmap overlay would be rendered here with folium HeatMap layer

Intensity = f(confidence, anomaly_score, density)

4. Recommended Area of Interest (AOI)
📍 Recommended Area of Interest
Reference Point (Centroid): 31.95245°N, 35.23310°E

AOI Geometry: Rectangular polygon (20m × 30m)

Uncertainty Radius: ±25m

Description: Northeast corner of apparent rectangular structure. Southern approach recommended to avoid modern debris.

⚠️ This is a recommended investigation area, not an excavation target. All fieldwork requires proper permits and expert supervision.

# 🔐 How to Add Secrets to Streamlit Cloud

## ⚠️ NEVER Commit secrets.toml to Git!

Your credentials are stored locally in `.streamlit/secrets.toml` which is now **ignored by Git** for security.

---

## ✅ Add Secrets to Streamlit Cloud

### Step 1: Go to Your App Dashboard
1. Open: https://share.streamlit.io/
2. Find: **Settalite-GI-Agent**
3. Click: **⚙️ Settings** (3 dots menu)

### Step 2: Navigate to Secrets
1. Click: **Secrets** tab
2. You'll see a text editor

### Step 3: Get Sentinel Hub OAuth Credentials

**IMPORTANT:** You need OAuth credentials, not API keys!

1. Go to: https://apps.sentinel-hub.com/dashboard/
2. Login or create free account
3. Click: **User Settings** (top right)
4. Click: **OAuth clients** tab
5. Click: **+ Create new OAuth client**
6. Name: `Heritage Sentinel Pro`
7. Copy the **Client ID** and **Client Secret**

### Step 4: Copy to Streamlit Secrets Editor

Paste this format (replace with YOUR credentials):

```toml
# Sentinel Hub OAuth Configuration
[sentinelhub]
client_id = "YOUR_CLIENT_ID_HERE"
client_secret = "YOUR_CLIENT_SECRET_HERE"

# Google Earth Engine (optional)
[gee]
project_id = "your-gee-project-id"
```

**⚠️ WARNING:** Do NOT use `api_key` or `instance_id` - these are OLD formats!

### Step 5: Paste and Save
1. Paste the content into Streamlit Cloud secrets editor
2. Click **Save**
3. Your app will automatically restart with new secrets
4. Check logs for: `✓ Sentinel Hub OAuth credentials loaded`

---

## 🔒 Security Notes

### ✅ Safe:
- Storing in `.streamlit/secrets.toml` locally (ignored by Git)
- Adding via Streamlit Cloud dashboard
- Environment variables

### ❌ Dangerous:
- Committing to Git (even private repos)
- Sharing screenshots with keys visible
- Hard-coding in source files

---

## 🧪 Test After Adding Secrets

Once secrets are added to Streamlit Cloud, test:

1. Go to: https://settalite-gi-agent-b34bd6ngdeibrnq7t8dayb.streamlit.app/
2. Select: **"Real (Live Satellite Data)"**
3. Enter coordinates and click **"Start Deep Scan"**
4. Should see: **LIVE PROOF PANEL** (not LIVE_FAILED)

---

## 🔄 Update Secrets

To change credentials:
1. Go to Streamlit Cloud → Settings → Secrets
2. Update the values
3. Save (app will restart automatically)

---

## 📋 Template for Others

Share this with collaborators (without actual values):

```toml
# .streamlit/secrets.toml template
# Get Sentinel Hub credentials from: https://apps.sentinel-hub.com/dashboard/
[sentinelhub]
client_id = "your-oauth-client-id"  # From OAuth clients page
client_secret = "your-oauth-client-secret"  # From OAuth clients page

# Optional: Google Earth Engine
[gee]
project_id = "your-gee-project-id"
```

---

## 🆘 If Credentials Were Exposed

If you accidentally committed secrets:

1. **Immediately revoke** the API keys:
   - Sentinel Hub: https://apps.sentinel-hub.com/dashboard/
   - Google Cloud: https://console.cloud.google.com/apis/credentials
   
2. **Generate new credentials**

3. **Update** `.streamlit/secrets.toml` locally and Streamlit Cloud

4. **Clean Git history** (advanced):
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .streamlit/secrets.toml" \
     --prune-empty --tag-name-filter cat -- --all
   ```

---

## ✅ Current Status

- ✅ `.streamlit/secrets.toml` is in `.gitignore`
- ✅ Local secrets are safe
- ⏳ **Next step**: Add secrets to Streamlit Cloud dashboard
- ⏳ Then test Live mode!
