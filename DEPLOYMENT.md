# 🚀 Deployment Guide: BRIA Pixel Playground

Deploy your **BRIA Pixel Playground** to production using **Render** (backend) and **Vercel** (frontend).

## 📋 Prerequisites

1. **GitHub Repository**: https://github.com/Artxie3/Pixel_BRIA
2. **Accounts**:
   - [Render](https://render.com) - Free tier
   - [Vercel](https://vercel.com) - Free tier
3. **API Keys** (you already have):
   - BRIA API Token
   - Supabase URL and Key

---

## 🖥️ Part 1: Deploy Backend to Render

### Step 1: Push Your Code to GitHub

First, ensure your code is pushed to your GitHub repository:

```bash
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

### Step 2: Create Render Account & Connect GitHub

1. Go to [render.com](https://render.com) and sign up/log in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account if not already connected
4. Select your repository: `Artxie3/Pixel_BRIA`

### Step 3: Configure the Web Service

Fill in these settings:

| Setting | Value |
|---------|-------|
| **Name** | `bria-pixel-playground` |
| **Region** | Choose closest to your users |
| **Branch** | `main` |
| **Root Directory** | *(leave empty)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements-web.txt` |
| **Start Command** | `cd webapp && uvicorn server:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | **Free** |

### Step 4: Add Environment Variables

In the **Environment** section, add these variables:

| Key | Value |
|-----|-------|
| `BRIA_API_TOKEN` | Your BRIA API token |
| `SUPABASE_URL` | `https://ryksfgrxanynfrbmyzbv.supabase.co` |
| `SUPABASE_KEY` | Your Supabase anon key |
| `PYTHONUNBUFFERED` | `1` |

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Wait for the build to complete (5-10 minutes)
3. Once deployed, you'll get a URL like: `https://bria-pixel-playground.onrender.com`

### Step 6: Test the Backend

Open your Render URL in a browser and add `/api/health`:
```
https://bria-pixel-playground.onrender.com/api/health
```

You should see:
```json
{"status":"ok","init_error":null,"storage":"supabase"}
```

> ⚠️ **Note**: Free tier services spin down after 15 minutes of inactivity. The first request after idle may take 30-60 seconds.

---

## 🌐 Part 2: Deploy Frontend to Vercel

### Step 1: Update Frontend API URL

**IMPORTANT**: Before deploying, update the API URL in `frontend/app.js`:

```javascript
// Line 7 in frontend/app.js
const API_BASE_URL = "https://bria-pixel-playground.onrender.com";
```

Replace with your actual Render URL, then commit:

```bash
git add frontend/app.js
git commit -m "Set production API URL"
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
4. Verify the image appears from your Render backend

---

## 🔧 Troubleshooting

### Backend Issues (Render)

**Build fails:**
- Check the build logs in Render dashboard
- Ensure `requirements-web.txt` has all dependencies

**API returns 500 error:**
- Check that all environment variables are set correctly
- View logs in Render dashboard → "Logs" tab

**Slow first response:**
- Normal for free tier - service needs to spin up after idle
- Consider upgrading to paid tier for always-on

### Frontend Issues (Vercel)

**CORS errors in browser:**
- The backend already allows all origins (`*`)
- Check browser console for the exact error

**Images not loading:**
- Verify Supabase bucket is public
- Check Supabase dashboard for storage issues

**API calls fail:**
- Verify `API_BASE_URL` is correct in `frontend/app.js`
- Make sure there's no trailing slash

---

## 📁 Project Structure

```
Pixel_BRIA/
├── frontend/                 # ← Deployed to Vercel
│   ├── index.html
│   ├── app.js               # Contains API_BASE_URL
│   ├── main.css
│   └── vercel.json
├── webapp/                   # ← Deployed to Render
│   ├── server.py            # FastAPI backend
│   ├── supabase_storage.py
│   └── static/              # Local dev frontend
├── pixel_playground.py       # Core BRIA integration
├── png_to_svg.py            # SVG conversion
├── requirements-web.txt     # Python dependencies
└── render.yaml              # Render configuration (optional)
```

---

## 🔗 Quick Reference

| Service | URL |
|---------|-----|
| **Render Backend** | `https://bria-pixel-playground.onrender.com` |
| **Vercel Frontend** | `https://your-project.vercel.app` |
| **Supabase Storage** | `https://ryksfgrxanynfrbmyzbv.supabase.co` |
| **Health Check** | `https://bria-pixel-playground.onrender.com/api/health` |

---

## 🎉 You're Live!

Your BRIA Pixel Playground is now deployed:

- 🖼️ **Frontend**: Hosted on Vercel's global CDN
- ⚙️ **Backend**: Running on Render's free tier
- 💾 **Storage**: Images stored in Supabase cloud

Share your Vercel URL to show off your pixel art generator!
