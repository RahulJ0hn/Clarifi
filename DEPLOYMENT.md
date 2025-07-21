# Clarifi Deployment Guide

This guide covers all deployment options for the Clarifi application.

## 🚀 Quick Deploy Options

### Option 1: Railway (Recommended - Easiest)

#### Prerequisites
- GitHub repository connected
- Clerk account for authentication
- Anthropic API key

#### Backend Deployment
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Set the root directory to `backend`
5. Add environment variables:
   ```
   DATABASE_URL=sqlite:///./clarifi.db
   CLERK_SECRET_KEY=your_clerk_secret_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   HOST=0.0.0.0
   PORT=8000
   ```
6. Deploy - Railway will auto-detect Python/FastAPI

#### Frontend Deployment
1. Create a new service in the same Railway project
2. Set root directory to `frontend`
3. Add environment variables:
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
   ```
4. Deploy

### Option 2: Render

#### Backend on Render
1. Go to [render.com](https://render.com)
2. Create "Web Service"
3. Connect GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables (same as Railway)
7. Deploy

#### Frontend on Render
1. Create "Static Site"
2. Build command: `npm run build`
3. Publish directory: `dist`
4. Add environment variables
5. Deploy

### Option 3: Vercel + Railway

#### Frontend on Vercel
1. Go to [vercel.com](https://vercel.com)
2. Import GitHub repository
3. Set root directory to `frontend`
4. Build command: `npm run build`
5. Output directory: `dist`
6. Add environment variables
7. Deploy

#### Backend on Railway
Follow the Railway backend deployment steps above.

## 🐳 Docker Deployment

### Local Docker Compose
```bash
# Clone repository
git clone https://github.com/RahulJ0hn/Clarifi.git
cd Clarifi

# Create .env file
cat > .env << EOF
CLERK_SECRET_KEY=your_clerk_secret_key
ANTHROPIC_API_KEY=your_anthropic_api_key
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
EOF

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### VPS/Server Deployment
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and deploy
git clone https://github.com/RahulJ0hn/Clarifi.git
cd Clarifi
# Create .env file as above
docker-compose up -d
```

## 🔧 Environment Variables

### Backend (.env)
```env
DATABASE_URL=sqlite:///./clarifi.db
CLERK_SECRET_KEY=your_clerk_secret_key
ANTHROPIC_API_KEY=your_anthropic_api_key
HOST=0.0.0.0
PORT=8000
DEBUG=false
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### Frontend (.env)
```env
VITE_API_URL=https://your-backend-domain.com
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

## 🔑 Required API Keys

### Clerk Authentication
1. Go to [clerk.com](https://clerk.com)
2. Create a new application
3. Get your publishable key and secret key
4. Configure allowed origins in Clerk dashboard

### Anthropic API
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Add to environment variables

## 📊 Monitoring & Health Checks

### Backend Health Check
- Endpoint: `GET /health`
- Expected response: `{"status": "healthy"}`

### Frontend Health Check
- Endpoint: `GET /`
- Expected: Served React app

### Docker Health Checks
Both containers have built-in health checks that will restart if unhealthy.

## 🔒 Security Considerations

### Production Checklist
- [ ] Use HTTPS everywhere
- [ ] Set `DEBUG=false` in production
- [ ] Configure CORS properly
- [ ] Use strong secret keys
- [ ] Enable rate limiting
- [ ] Set up monitoring/logging

### SSL/HTTPS
- Railway/Render/Vercel provide automatic SSL
- For VPS: Use Let's Encrypt with nginx

## 🐛 Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check environment variables
   - Verify port availability
   - Check logs: `docker-compose logs backend`

2. **Frontend can't connect to backend**
   - Verify `VITE_API_URL` is correct
   - Check CORS configuration
   - Ensure backend is running

3. **Authentication issues**
   - Verify Clerk keys are correct
   - Check allowed origins in Clerk dashboard
   - Ensure JWT tokens are valid

4. **Database issues**
   - Check database file permissions
   - Verify SQLite file exists
   - Consider using PostgreSQL for production

### Logs
```bash
# Docker logs
docker-compose logs -f

# Backend logs only
docker-compose logs -f backend

# Frontend logs only
docker-compose logs -f frontend
```

## 📈 Scaling Considerations

### For High Traffic
1. **Database**: Switch from SQLite to PostgreSQL
2. **Caching**: Add Redis for session storage
3. **Load Balancing**: Use multiple backend instances
4. **CDN**: Add Cloudflare for static assets

### Performance Optimization
1. **Backend**: Add response caching
2. **Frontend**: Enable gzip compression
3. **Database**: Add connection pooling
4. **Monitoring**: Set up application monitoring

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] API keys secured
- [ ] Database migrations run
- [ ] SSL certificates ready

### Post-Deployment
- [ ] Health checks passing
- [ ] Authentication working
- [ ] API endpoints responding
- [ ] Frontend loading correctly
- [ ] Monitoring alerts configured

## 📞 Support

For deployment issues:
1. Check the troubleshooting section
2. Review application logs
3. Verify environment variables
4. Test locally with Docker Compose
5. Open an issue on GitHub

---

**Happy deploying! 🚀** 