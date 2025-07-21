# Railway Deployment Guide for Clarifi

This guide will help you deploy Clarifi on Railway step by step.

## 🚀 Step 1: Deploy Backend

### 1.1 Create New Project
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `Clarifi` repository

### 1.2 Configure Backend Service
1. **Set Root Directory**: `backend`
2. **Service Name**: `clarifi-backend`
3. **Environment**: `Production`

### 1.3 Add Environment Variables
Click on "Variables" tab and add:

```env
DATABASE_URL=sqlite:///./clarifi.db
CLERK_SECRET_KEY=your_clerk_secret_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
HOST=0.0.0.0
PORT=8000
DEBUG=false
ALLOWED_ORIGINS=https://your-frontend-domain.railway.app
```

### 1.4 Deploy Backend
1. Click "Deploy"
2. Wait for build to complete (should take 2-3 minutes)
3. Note the generated URL (e.g., `https://clarifi-backend-production.up.railway.app`)

## 🚀 Step 2: Deploy Frontend

### 2.1 Add Frontend Service
1. In the same Railway project, click "New Service"
2. Select "GitHub Repo" again
3. Choose the same `Clarifi` repository
4. **Set Root Directory**: `frontend`
5. **Service Name**: `clarifi-frontend`

### 2.2 Configure Frontend Environment Variables
Add these variables:

```env
VITE_API_URL=https://your-backend-url.railway.app
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key_here
```

### 2.3 Deploy Frontend
1. Click "Deploy"
2. Wait for build to complete
3. Note the frontend URL

## 🔑 Step 3: Get API Keys

### 3.1 Clerk Authentication
1. Go to [clerk.com](https://clerk.com)
2. Create a new application
3. Get your keys:
   - **Publishable Key**: For frontend
   - **Secret Key**: For backend
4. Add your Railway domains to Clerk's allowed origins

### 3.2 Anthropic API
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Add to backend environment variables

## 🔧 Step 4: Update Environment Variables

### 4.1 Backend Variables
Update these in Railway:
- Replace `your_clerk_secret_key_here` with actual Clerk secret key
- Replace `your_anthropic_api_key_here` with actual Anthropic key
- Update `ALLOWED_ORIGINS` with your frontend URL

### 4.2 Frontend Variables
Update these in Railway:
- Replace `your-backend-url.railway.app` with actual backend URL
- Replace `your_clerk_publishable_key_here` with actual Clerk publishable key

## ✅ Step 5: Verify Deployment

### 5.1 Test Backend
```bash
# Test health endpoint
curl https://your-backend-url.railway.app/health

# Expected response:
{"status": "healthy", "scheduler_running": true}
```

### 5.2 Test Frontend
1. Visit your frontend URL
2. Should see the Clarifi login page
3. Test authentication flow

## 🐛 Troubleshooting

### Build Failures
- **Error**: "Error creating build plan with Railpack"
  - **Solution**: The configuration files I added should fix this
  - Railway will now use the `railway.json` and `Procfile`

### Environment Variables
- **Error**: "Module not found"
  - **Solution**: Check that all required environment variables are set
  - Ensure API keys are correct

### CORS Issues
- **Error**: Frontend can't connect to backend
  - **Solution**: Update `ALLOWED_ORIGINS` in backend variables
  - Add your frontend domain to the list

### Database Issues
- **Error**: SQLite file not found
  - **Solution**: This is normal for Railway - SQLite will be created automatically
  - For production, consider using PostgreSQL

## 📊 Monitoring

### Railway Dashboard
- Check "Metrics" tab for performance
- Monitor "Deployments" for build status
- View logs in "Deployments" → "View logs"

### Health Checks
- Backend: `GET /health`
- Frontend: Should load without errors
- WebSocket: `WS /ws`

## 🔄 Updates

### Automatic Deployments
- Railway automatically redeploys when you push to GitHub
- No manual intervention needed

### Manual Redeploy
1. Go to Railway dashboard
2. Click "Deploy" button
3. Select "Deploy latest commit"

## 🎉 Success!

Once deployed, your Clarifi application will be available at:
- **Frontend**: `https://your-frontend-url.railway.app`
- **Backend API**: `https://your-backend-url.railway.app`
- **API Docs**: `https://your-backend-url.railway.app/docs`

---

**Happy deploying! 🚀** 