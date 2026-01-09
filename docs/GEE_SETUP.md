# Google Earth Engine Setup Guide

## What You Have
- **Project ID**: `concise-perigee-468806-m8`
- **Project Name**: My Project 43136
- **Google Cloud API Key**: `AIzaSyCwKOIgf6t1KIJ3meY7Cysp-tRa_BBwO2g`

⚠️ **Important**: The API key you have is for Google Cloud services (Maps, Places, etc.), NOT for Earth Engine. Earth Engine requires different authentication.

---

## Option 1: Local Development (Easiest)

### Step 1: Install Earth Engine
```bash
pip install earthengine-api
```

### Step 2: Authenticate
```bash
earthengine authenticate --project=concise-perigee-468806-m8
```

This will:
1. Open browser
2. Ask you to login with Google account
3. Grant permissions
4. Save credentials locally

### Step 3: Test
```python
import ee
ee.Initialize(project='concise-perigee-468806-m8')
print(ee.Number(1).getInfo())  # Should print: 1
```

---

## Option 2: Streamlit Cloud (Service Account)

### Step 1: Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project: `concise-perigee-468806-m8`
3. Navigate to **IAM & Admin → Service Accounts**
4. Click **Create Service Account**:
   - Name: `heritage-sentinel-gee`
   - Description: "Earth Engine access for Heritage Sentinel Pro"
5. Click **Create and Continue**
6. Grant role: **Earth Engine Resource Writer**
7. Click **Done**

### Step 2: Generate Key

1. Click on the service account you just created
2. Go to **Keys** tab
3. Click **Add Key → Create new key**
4. Choose **JSON**
5. Download the JSON file

### Step 3: Add to Streamlit Secrets

Copy the entire JSON content and add to `.streamlit/secrets.toml`:

```toml
[gee]
project_id = "concise-perigee-468806-m8"
service_account_json = '''
{
  "type": "service_account",
  "project_id": "concise-perigee-468806-m8",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "heritage-sentinel-gee@concise-perigee-468806-m8.iam.gserviceaccount.com",
  "client_id": "123456789...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
'''
```

### Step 4: Register Service Account with Earth Engine

```bash
# Using your authenticated account
earthengine create --project=concise-perigee-468806-m8
earthengine set_project concise-perigee-468806-m8

# Add service account email to Earth Engine
# Email will be: heritage-sentinel-gee@concise-perigee-468806-m8.iam.gserviceaccount.com
```

Or register via [Earth Engine Code Editor](https://code.earthengine.google.com/):
1. Go to Assets tab
2. Click "NEW" → "Cloud Project"
3. Enter: `concise-perigee-468806-m8`

---

## Option 3: Use Your Current Setup (Limited)

Your current API key can be used for:
- ✅ Google Maps
- ✅ Google Places
- ✅ Geocoding
- ❌ Earth Engine (requires separate auth)

To use Earth Engine, you MUST follow Option 1 or Option 2.

---

## Verify Setup

### Test Script
```python
import ee

# Initialize with project
try:
    ee.Initialize(project='concise-perigee-468806-m8')
    print("✓ Earth Engine connected!")
    
    # Test query
    point = ee.Geometry.Point([35.2332, 31.9522])  # Jerusalem
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(point) \
        .filterDate('2024-01-01', '2024-12-31') \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    
    count = s2.size().getInfo()
    print(f"✓ Found {count} Sentinel-2 images")
    
except Exception as e:
    print(f"✗ Error: {e}")
```

Expected output:
```
✓ Earth Engine connected!
✓ Found 45 Sentinel-2 images
```

---

## Troubleshooting

### "Project is not registered"
Run: `earthengine create --project=concise-perigee-468806-m8`

### "User not authenticated"
Run: `earthengine authenticate --project=concise-perigee-468806-m8`

### "Service account not authorized"
1. Go to [IAM & Admin](https://console.cloud.google.com/iam-admin/iam?project=concise-perigee-468806-m8)
2. Find your service account
3. Add role: "Earth Engine Resource Writer"

### "Cannot find project"
Make sure you're using the correct project ID: `concise-perigee-468806-m8`

---

## Current System Status

✅ **Config Updated**: `config/config.yaml` now includes GEE settings
✅ **Secrets Template**: `.streamlit/secrets.toml` created with your project ID
⏳ **Authentication**: Needs to be completed (Option 1 or 2)

After authentication, the system will automatically:
- Detect available GEE connection
- Use multi-temporal Sentinel-2 analysis
- Enable SAR (Sentinel-1) analysis
- Provide provenance in LIVE mode
