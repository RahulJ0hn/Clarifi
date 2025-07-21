# Clarifi - Intelligent Web Monitoring & Summarization

Clarifi is an AI-powered web application that combines intelligent webpage summarization, content monitoring, and real-time notifications with a modern React frontend and FastAPI backend.

## 🚀 Features

### ✅ **Core Features**

1. **AI-Powered Summarization**
   - Intelligent content extraction from any website
   - Multi-provider AI support (Claude, GPT, Bedrock)
   - Question-answering about webpage content
   - Summary history and management

2. **Smart Website Monitoring**
   - Create monitors to track changes on websites
   - Multiple monitor types (content, price, specific elements)
   - Custom CSS selectors for targeted monitoring
   - Configurable check intervals
   - Real-time status updates

3. **Real-time Notifications**
   - WebSocket-powered live notifications
   - Monitor change alerts with AI analysis
   - Notification management (mark as read, delete)
   - Filtering and statistics

4. **Modern Dashboard**
   - Real-time statistics and metrics
   - Recent activity tracking
   - Performance monitoring
   - Responsive design for all devices

## 🛠 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Lightweight database
- **APScheduler** - Background task scheduling
- **WebSocket** - Real-time communication
- **httpx** - HTTP client for web scraping
- **BeautifulSoup** - HTML parsing
- **Anthropic/OpenAI** - AI summarization
- **Clerk** - Authentication system

### Frontend
- **React** - Modern UI framework
- **Tailwind CSS** - Utility-first CSS
- **Lucide React** - Icon library
- **React Router** - Client-side routing
- **React Hot Toast** - Toast notifications
- **WebSocket** - Real-time updates
- **Zustand** - State management
- **Clerk React** - Authentication

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## 🚀 Quick Start

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python run.py
```

The backend will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at:
- **Application**: http://localhost:3000

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# API Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Database Configuration
DATABASE_URL=sqlite:///./clarifi.db

# AI API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Clerk Authentication
CLERK_SECRET_KEY=your_clerk_secret_key_here

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Monitoring Configuration
MONITOR_CHECK_INTERVAL=300
MAX_MONITORS_PER_USER=50
```

### Frontend Environment

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key_here
```

## 📖 Usage Guide

### 1. Authentication
- Sign up/login using Clerk authentication
- Secure JWT token-based authentication
- Protected routes and API endpoints

### 2. Webpage Summarization
1. Navigate to the **Dashboard**
2. Enter a URL in the "Website URL" field
3. Optionally ask a specific question about the page
4. Click "Summarize"
5. View the AI-generated summary

### 3. Creating Monitors
1. Go to the **Monitors** page
2. Click "Create Monitor"
3. Fill in the details:
   - **Name**: Descriptive name for the monitor
   - **URL**: Website to monitor
   - **Monitor Type**: Content, Price, or Specific Element
   - **CSS Selector**: (Optional) Target specific elements
   - **Check Interval**: How often to check (in seconds)
   - **Notifications**: Enable/disable alerts
4. Click "Create Monitor"

### 4. Managing Notifications
1. Visit the **Notifications** page
2. View all notifications with filtering options
3. Mark notifications as read
4. Delete unwanted notifications
5. View notification statistics

## 🐳 Docker Deployment

### Backend
```bash
cd backend
docker build -t clarifi-backend .
docker run -d -p 8000:8000 clarifi-backend
```

### Frontend
```bash
cd frontend
docker build -t clarifi-frontend .
docker run -d -p 3000:80 clarifi-frontend
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./clarifi.db
      - CLERK_SECRET_KEY=${CLERK_SECRET_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
```

## 📊 API Endpoints

### Authentication
- `POST /auth/verify` - Verify JWT token
- `GET /auth/user` - Get current user

### Summarization
- `POST /api/summarize` - Summarize a webpage
- `GET /api/summaries` - Get summary history
- `GET /api/summaries/{id}` - Get specific summary
- `DELETE /api/summaries/{id}` - Delete summary

### Monitoring
- `POST /api/monitors` - Create a monitor
- `GET /api/monitors` - List all monitors
- `PUT /api/monitors/{id}` - Update monitor
- `DELETE /api/monitors/{id}` - Delete monitor
- `POST /api/monitors/{id}/check` - Check monitor now
- `POST /api/monitors/{id}/toggle` - Toggle monitor status

### Notifications
- `GET /api/notifications` - List notifications
- `GET /api/notifications/recent` - Get recent notifications
- `POST /api/notifications/mark-read` - Mark as read
- `DELETE /api/notifications/{id}` - Delete notification
- `GET /api/notifications/stats` - Notification statistics

### System
- `GET /health` - Health check
- `GET /` - API information
- `WS /ws` - WebSocket endpoint

## 🏗 Project Structure

```
clarifi/
├── backend/
│   ├── app/
│   │   ├── core/          # Configuration and database
│   │   ├── models/        # Database models
│   │   ├── routers/       # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── hooks/         # Custom hooks
│   │   └── store/         # State management
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
└── README.md
```

## 🐛 Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check if virtual environment is activated
   - Verify all dependencies are installed
   - Check if port 8000 is available

2. **Frontend won't start**
   - Ensure Node.js is installed
   - Run `npm install` in frontend directory
   - Check if port 3000 is available

3. **Authentication issues**
   - Verify Clerk API keys are set correctly
   - Check CORS configuration
   - Ensure JWT tokens are valid

4. **Summarization fails**
   - Verify AI API keys are set in `.env`
   - Check internet connection
   - Ensure target website is accessible

5. **Monitors not working**
   - Check if scheduler is running
   - Verify monitor configuration
   - Check logs for errors

## 🔒 Security

- **Authentication**: Clerk JWT-based authentication
- **CORS**: Configured for development and production
- **API Keys**: Stored in environment variables
- **Input Validation**: Pydantic schemas
- **Rate Limiting**: Implemented on API endpoints

## 📈 Performance

- **Summarization**: ~5-10 seconds per request
- **Monitoring**: Configurable intervals (default: 5 minutes)
- **Database**: SQLite for development, PostgreSQL for production
- **Caching**: In-memory caching for frequent requests
- **Responsive Design**: Mobile-first approach

## 🚀 Deployment Options

### Cloud Platforms

1. **Railway** - Easy deployment for both frontend and backend
2. **Render** - Great for FastAPI applications
3. **Vercel** - Optimized for React applications
4. **Netlify** - Excellent for static sites
5. **Heroku** - Traditional platform with good support

### VPS/Server

1. **Docker** - Containerized deployment
2. **Nginx** - Reverse proxy and static file serving
3. **Gunicorn** - WSGI server for Python
4. **PM2** - Process manager for Node.js

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub

---

**Happy browsing with AI! 🚀** 