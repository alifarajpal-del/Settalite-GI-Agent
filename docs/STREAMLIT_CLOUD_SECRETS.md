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

### Step 3: Copy Your Local Secrets
Open your local `.streamlit/secrets.toml` and copy the content:

```toml
# Google Earth Engine Configuration
[gee]
project_id = "concise-perigee-468806-m8"
project_name = "My Project 43136"

# Sentinel Hub Configuration
[sentinelhub]
client_id = "1v9QzKh110t6DCaSb0k4bbWtrFu3uviK"
client_secret = "594cd8d4233042a857b4c6f5a9cd713b3b26f853"
instance_id = "1v9QzKh110t6DCaSb0k4bbWtrFu3uviK"

# Google Cloud API
[google_cloud]
api_key = "AIzaSyCwKOIgf6t1KIJ3meY7Cysp-tRa_BBwO2g"
project_id = "concise-perigee-468806-m8"
```

### Step 4: Paste and Save
1. Paste the content into Streamlit Cloud secrets editor
2. Click **Save**
3. Your app will automatically restart with new secrets

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
[gee]
project_id = "your-gee-project-id"

[sentinelhub]
client_id = "your-sentinelhub-client-id"
client_secret = "your-sentinelhub-client-secret"

[google_cloud]
api_key = "your-google-cloud-api-key"
project_id = "your-project-id"
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
