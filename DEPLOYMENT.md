git commit -m "Prepare for production deployment"
git push origin main
git push origin main
# 🚀 Deployment Guide: BRIA Pixel Playground (Railway + Vercel)

Deploy your **BRIA Pixel Playground** to production using **Railway** (backend) and **Vercel** (frontend).

## 📋 Prerequisites

1. **GitHub Repository**: https://github.com/Artxie3/Pixel_BRIA
2. **Accounts**:
   - [Railway](https://railway.app) - Free trial/credit
   - [Vercel](https://vercel.com) - Free tier
3. **API Keys** (you already have):
   - BRIA API Token
   - Supabase URL and Key

---

## 🖥️ Part 1: Deploy Backend to Railway

### Step 1: Push Your Code to GitHub

First, ensure your code is pushed to your GitHub repository:

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 2: Create Railway Project & Connect GitHub

1. Go to [railway.app](https://railway.app) and sign up/log in
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository: `Artxie3/Pixel_BRIA`

### Step 3: Configure the Service

Railway will auto-detect the Dockerfile. No need to set build/start commands.

### Step 4: Add Environment Variables

In the **Variables** tab, add these variables:

| Key | Value |
|-----|-------|
| `BRIA_API_TOKEN` | Your BRIA API token |
| `SUPABASE_URL` | `https://ryksfgrxanynfrbmyzbv.supabase.co` |
| `SUPABASE_KEY` | Your Supabase anon key |
| `PYTHONUNBUFFERED` | `1` |

### Step 5: Deploy

1. Railway will build and deploy automatically
2. Once deployed, you'll get a URL like: `https://bria-pixel-playground-production.up.railway.app`

### Step 6: Test the Backend

Open your Railway URL in a browser and add `/health`:
```
https://bria-pixel-playground-production.up.railway.app/health
```

You should see:
```json
{"status":"healthy","storage":true}
```

---

## 🌐 Part 2: Deploy Frontend to Vercel

### Step 1: Update Frontend API URL

**IMPORTANT**: Before deploying, update the API URL in `frontend/app.js`:

```javascript
const API_BASE_URL = "https://bria-pixel-playground-production.up.railway.app";
```

Commit and push:

```bash
git add frontend/app.js
git commit -m "Set Railway API URL"
git push origin main
```

### Step 2: Create Vercel Account & Import Project

1. Go to [vercel.com](https://vercel.com) and sign up/log in with GitHub
2. Click **"Add New..."** → **"Project"**
3. Import your repository: `Artxie3/Pixel_BRIA`

### Step 3: Configure the Project

| Setting | Value |
|---------|-------|
| **Framework Preset** | `Other` |
| **Root Directory** | Click "Edit" → Enter `frontend` |
| **Build Command** | *(leave empty - override to empty)* |
| **Output Directory** | `.` |
| **Install Command** | *(leave empty - override to empty)* |

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait for deployment (usually under 1 minute)
3. You'll get a URL like: `https://pixel-bria.vercel.app`

### Step 5: Test the Full Application

1. Open your Vercel URL
2. Enter a prompt like: "a cute pixel cat"
3. Click **Generate**
4. Verify the image appears from your Railway backend

---

## 🔧 Troubleshooting

**Backend not responding:**
- Check Railway Deploy Logs for Python errors
- Make sure Dockerfile uses `CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]`
- Ensure all environment variables are set

**CORS errors in browser:**
- FastAPI already allows all origins (`*`)
- Make sure backend is running and reachable

**API calls fail:**
- Verify `API_BASE_URL` is correct in `frontend/app.js`
- Make sure there's no trailing slash

**Images not loading:**
- Verify Supabase bucket is public
- Check Supabase dashboard for storage issues

---

## 📁 Project Structure

```
Pixel_BRIA/
├── frontend/                 # ← Deployed to Vercel
│   ├── index.html
│   ├── app.js               # Contains API_BASE_URL
│   ├── main.css
│   └── vercel.json
├── webapp/                   # ← Deployed to Railway
│   ├── server.py            # FastAPI backend
│   ├── supabase_storage.py
│   └── static/              # Local dev frontend
├── pixel_playground.py       # Core BRIA integration
├── png_to_svg.py            # SVG conversion
├── requirements-web.txt     # Python dependencies
├── Dockerfile               # Railway/Container config
└── .env.example             # Example env vars
```

---

## 🔗 Quick Reference

| Service | URL |
|---------|-----|
| **Railway Backend** | `https://bria-pixel-playground-production.up.railway.app` |
| **Vercel Frontend** | `https://pixel-bria.vercel.app` |
| **Supabase Storage** | `https://ryksfgrxanynfrbmyzbv.supabase.co` |
| **Health Check** | `https://bria-pixel-playground-production.up.railway.app/health` |

---

## 🎉 You're Live!

Your BRIA Pixel Playground is now deployed:

- 🖼️ **Frontend**: Hosted on Vercel's global CDN
- ⚙️ **Backend**: Running on Railway
- 💾 **Storage**: Images stored in Supabase cloud

Share your Vercel URL to show off your pixel art generator!
