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
