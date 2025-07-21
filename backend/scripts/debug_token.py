#!/usr/bin/env python3
"""
Debug script to test token verification
"""

import requests
import json
import jwt
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def create_test_token():
    """Create a test token similar to what Clerk would send"""
    payload = {
        "sub": "user_test_debug",
        "email": "test@debug.com",
        "given_name": "Test",
        "family_name": "Debug",
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iss": "https://clerk.your-app.com",
        "aud": "your-app",
        "azp": "your-app"
    }
    
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return token

def test_token_verification():
    print("🧪 Testing Token Verification...")
    print("=" * 60)
    
    # Create test token
    token = create_test_token()
    print(f"🔑 Test token created: {token[:50]}...")
    
    # Decode token to see payload
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        print("📋 Token payload:")
        print(f"   sub (user_id): {decoded.get('sub')}")
        print(f"   email: {decoded.get('email')}")
        print(f"   exp: {decoded.get('exp')}")
    except Exception as e:
        print(f"❌ Error decoding token: {e}")
    
    # Test API call
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n🌐 Testing API call with token...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/me/data-check", headers=headers)
        print(f"📥 Response status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print("✅ API call successful!")
            print(f"   User data: {data}")
        else:
            error_text = response.text
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Error: {error_text}")
    except Exception as e:
        print(f"❌ API call error: {e}")

if __name__ == "__main__":
    test_token_verification() 