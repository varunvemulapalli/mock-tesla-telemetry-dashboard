# Deployment Guide

This guide covers multiple options to deploy your Tesla Energy Dashboard online.

## Option 1: Railway (Recommended - Easiest)

Railway supports Docker and makes deployment simple.

### Steps:

1. **Sign up at [railway.app](https://railway.app)** (free tier available)

2. **Create a new project** and connect your GitHub repository

3. **Deploy Backend:**
   - Click "New Service" → "GitHub Repo"
   - Select your repo
   - Railway will detect `docker-compose.yml` or you can use the backend Dockerfile
   - Add environment variables:
     ```
     OPENAI_API_KEY=your_key_here
     API_HOST=0.0.0.0
     API_PORT=8000
     SIMULATOR_ENABLED=true
     ```
   - Railway will auto-generate a URL like `https://your-backend.up.railway.app`

4. **Deploy Frontend:**
   - Create another service for frontend
   - Use the frontend Dockerfile
   - Add environment variables:
     ```
     REACT_APP_API_URL=https://your-backend.up.railway.app
     REACT_APP_WS_URL=wss://your-backend.up.railway.app
     ```
   - Note: For WebSockets, you may need to configure Railway's proxy

5. **Get your public URL** - Railway provides HTTPS URLs automatically

---

## Option 2: Render (Free Tier Available)

### Steps:

1. **Sign up at [render.com](https://render.com)**

2. **Deploy Backend:**
   - Go to Dashboard → "New" → "Web Service"
   - Connect your GitHub repo
   - Settings:
     - **Name:** `tesla-energy-backend`
     - **Environment:** Docker
     - **Dockerfile Path:** `backend/Dockerfile`
     - **Port:** 8000
   - Add environment variables:
     ```
     OPENAI_API_KEY=your_key_here
     API_HOST=0.0.0.0
     API_PORT=8000
     SIMULATOR_ENABLED=true
     ```
   - Render will give you a URL like `https://tesla-energy-backend.onrender.com`

3. **Deploy Frontend:**
   - "New" → "Static Site"
   - Connect your GitHub repo
   - Settings:
     - **Build Command:** `cd frontend && npm install && npm run build`
     - **Publish Directory:** `frontend/build`
   - Add environment variables:
     ```
     REACT_APP_API_URL=https://tesla-energy-backend.onrender.com
     REACT_APP_WS_URL=wss://tesla-energy-backend.onrender.com
     ```

---

## Option 3: Vercel (Frontend) + Railway/Render (Backend)

### Frontend on Vercel:

1. **Sign up at [vercel.com](https://vercel.com)**

2. **Import your GitHub repository**

3. **Configure:**
   - **Framework Preset:** Create React App
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `build`
   - **Environment Variables:**
     ```
     REACT_APP_API_URL=https://your-backend-url.com
     REACT_APP_WS_URL=wss://your-backend-url.com
     ```

4. **Deploy** - Vercel provides a URL automatically

### Backend on Railway/Render:
Follow Option 1 or 2 for backend deployment.

---

## Option 4: Fly.io (Docker Native)

### Steps:

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Deploy Backend:**
   ```bash
   cd backend
   fly launch
   # Follow prompts, then:
   fly secrets set OPENAI_API_KEY=your_key_here
   fly deploy
   ```

4. **Deploy Frontend:**
   ```bash
   cd frontend
   fly launch
   fly secrets set REACT_APP_API_URL=https://your-backend.fly.dev
   fly deploy
   ```

---

## Important Notes:

### WebSocket Configuration:
- Most platforms require WebSocket support configuration
- For Railway: WebSockets work automatically
- For Render: May need to enable WebSocket support in settings
- For Vercel: WebSockets require a backend proxy (consider using Railway/Render for backend)

### Environment Variables:
Make sure to set these in your deployment platform:
- **Backend:** `OPENAI_API_KEY` (required for GPT features)
- **Frontend:** `REACT_APP_API_URL` and `REACT_APP_WS_URL` (point to your backend URL)

### CORS Configuration:
Your backend already has CORS configured in `backend/app/main.py`. If you deploy frontend and backend to different domains, ensure the backend's `CORS_ORIGINS` includes your frontend URL.

### Updating CORS (if needed):
Edit `backend/app/main.py`:
```python
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
# Add your production frontend URL
```

---

## Quick Start Recommendation:

**For fastest deployment:**
1. Use **Railway** for both frontend and backend (supports Docker, easy setup)
2. Or use **Vercel** (frontend) + **Railway** (backend) for best performance

**For free hosting:**
1. Use **Render** (free tier available, but may spin down after inactivity)

---

## Testing Your Deployment:

1. Visit your frontend URL
2. Check browser console for any CORS or connection errors
3. Verify WebSocket connection works (should see real-time updates)
4. Test control buttons to ensure backend communication works

---

## Troubleshooting:

- **WebSocket not connecting:** Check that your backend URL uses `wss://` (secure) for HTTPS sites
- **CORS errors:** Update backend CORS_ORIGINS environment variable
- **API not found:** Verify REACT_APP_API_URL points to your backend URL
- **Build fails:** Check that all environment variables are set correctly

