#!/usr/bin/env python3
"""
AI Browser MVP Backend Startup Script
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for the application"""
    
    # Check if .env file exists
    env_file = project_root / '.env'
    if not env_file.exists():
        print("⚠️  .env file not found. Please create one based on .env.example")
        print("   You can copy .env.example to .env and update the values")
        print()
        
        # Show example .env content
        print("Example .env file content:")
        print("=" * 50)
        env_example = """# API Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Database Configuration
DATABASE_URL=sqlite:///./ai_browser.db

# AI API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_AI_PROVIDER=aws_bedrock

# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=arn:aws:bedrock:us-east-1:account:inference-profile/model-id

# CORS Configuration (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001

# Monitoring Configuration
MONITOR_CHECK_INTERVAL=300
MAX_MONITORS_PER_USER=50

# Scraping Configuration
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
REQUEST_TIMEOUT=30
MAX_CONTENT_LENGTH=1000000

# Security Configuration
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30"""
        print(env_example)
        print("=" * 50)
        
        # Create .env file with defaults
        with open(env_file, 'w') as f:
            f.write(env_example)
        print("✅ Created .env file with default values")
        print("⚠️  Please update API keys in .env file before continuing")
        print()
    
    # Check for required dependencies
    try:
        import uvicorn
        from app.main import app
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return
    
    # Start the server
    print("🚀 Starting Clarifi Backend...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    print("💻 Health Check: http://localhost:8000/health")
    print()
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Browser MVP Backend...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main() 