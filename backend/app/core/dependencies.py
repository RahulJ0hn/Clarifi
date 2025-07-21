from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.clerk_auth import get_user_from_token, verify_clerk_token
from app.models.user import User
import logging

# Set up logging
logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if token is provided, otherwise return None"""
    if not credentials:
        logger.debug("No credentials provided")
        return None
    
    token = credentials.credentials
    logger.info(f"🔐 Received Clerk token: {token[:20]}...")
    
    # Verify the token first
    if not verify_clerk_token(token):
        logger.warning("❌ Clerk token verification failed")
        return None
    
    user_data = get_user_from_token(token)
    if not user_data:
        logger.warning("❌ Failed to extract user data from token")
        return None
    
    logger.info(f"✅ Extracted user data: {user_data['user_id']} ({user_data['email']})")
    
    # Find or create user based on Clerk data
    user = db.query(User).filter(User.id == user_data["user_id"]).first()
    if not user:
        logger.info(f"👤 Creating new user: {user_data['user_id']}")
        # Create user if they don't exist
        user = User(
            id=user_data["user_id"],  # Use Clerk user ID as primary key
            email=user_data["email"],
            password_hash="clerk_user",  # Placeholder for Clerk users
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✅ User created successfully: {user.id}")
    else:
        logger.info(f"👤 Found existing user: {user.id}")
    
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user - requires authentication"""
    if not credentials:
        logger.warning("❌ No credentials provided for protected route")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    logger.info(f"🔐 Verifying Clerk token for protected route: {token[:20]}...")
    
    # Verify the token first
    if not verify_clerk_token(token):
        logger.warning("❌ Clerk token verification failed for protected route")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_data = get_user_from_token(token)
    if not user_data:
        logger.warning("❌ Failed to extract user data from token for protected route")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"✅ Extracted user data for protected route: {user_data['user_id']} ({user_data['email']})")
    
    # Find or create user based on Clerk data
    user = db.query(User).filter(User.id == user_data["user_id"]).first()
    if not user:
        logger.info(f"👤 Creating new user for protected route: {user_data['user_id']}")
        # Create user if they don't exist
        user = User(
            id=user_data["user_id"],  # Use Clerk user ID as primary key
            email=user_data["email"],
            password_hash="clerk_user",  # Placeholder for Clerk users
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✅ User created successfully for protected route: {user.id}")
    else:
        logger.info(f"👤 Found existing user for protected route: {user.id}")
    
    return user

def get_current_user_id(
    current_user: User = Depends(get_current_user)
) -> str:
    """Get current user ID for authorization checks"""
    logger.info(f"🔍 Getting user ID for authorization: {current_user.id}")
    return current_user.id

def verify_user_owns_data(
    data_user_id: str,
    current_user_id: str = Depends(get_current_user_id)
) -> bool:
    """Verify that the current user owns the data they're trying to access"""
    if data_user_id != current_user_id:
        logger.warning(f"🚫 Authorization denied: User {current_user_id} tried to access data owned by {data_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own data"
        )
    
    logger.info(f"✅ Authorization granted: User {current_user_id} accessing their own data")
    return True 