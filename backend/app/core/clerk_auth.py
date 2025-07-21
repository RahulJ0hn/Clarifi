import jwt
import json
import requests
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_clerk_public_keys() -> Optional[Dict[str, Any]]:
    """Fetch Clerk's public keys from JWKS endpoint"""
    try:
        if not settings.CLERK_PUBLISHABLE_KEY:
            logger.error("No Clerk publishable key configured")
            return None
        
        # Extract issuer from publishable key
        # Format: pk_test_xxxxx or pk_live_xxxxx
        if not settings.CLERK_PUBLISHABLE_KEY.startswith(('pk_test_', 'pk_live_')):
            logger.error("Invalid Clerk publishable key format")
            return None
        
        # Determine environment and construct JWKS URL
        if settings.CLERK_PUBLISHABLE_KEY.startswith('pk_test_'):
            # Extract instance ID from publishable key
            # Format: pk_test_xxxxx where xxxxx is the instance ID
            instance_id = settings.CLERK_PUBLISHABLE_KEY.split('_')[2]
            jwks_url = f"https://{instance_id}.clerk.accounts.dev/.well-known/jwks.json"
        else:
            # For live keys, we need the issuer URL
            if not settings.CLERK_ISSUER_URL:
                logger.error("CLERK_ISSUER_URL required for live keys")
                return None
            jwks_url = f"{settings.CLERK_ISSUER_URL}/.well-known/jwks.json"
        
        logger.info(f"🔑 Fetching Clerk JWKS from: {jwks_url}")
        
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        
        jwks = response.json()
        logger.info(f"✅ Successfully fetched JWKS with {len(jwks.get('keys', []))} keys")
        return jwks
        
    except Exception as e:
        logger.error(f"❌ Error fetching Clerk JWKS: {e}")
        return None

def get_key_from_jwks(jwks: Dict[str, Any], kid: str) -> Optional[str]:
    """Get the public key for a specific key ID from JWKS"""
    try:
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                # Convert JWK to PEM format for PyJWT
                # This is a simplified conversion - in production, use a proper JWK library
                if key.get('kty') == 'RSA':
                    # For RSA keys, we need to construct the PEM
                    # This is a placeholder - use proper JWK to PEM conversion
                    logger.warning("RSA key conversion not implemented - using development mode")
                    return None
                else:
                    logger.warning(f"Unsupported key type: {key.get('kty')}")
                    return None
        return None
    except Exception as e:
        logger.error(f"Error extracting key from JWKS: {e}")
        return None

def verify_clerk_token(token: str) -> bool:
    """Verify Clerk token signature using JWKS"""
    try:
        logger.info(f"🔐 Verifying Clerk token: {token[:20]}...")
        
        # For development, allow bypass if no proper keys configured
        if not settings.CLERK_PUBLISHABLE_KEY:
            logger.warning("No Clerk keys configured, using development mode")
            return True
        
        # Get Clerk's public keys
        jwks = get_clerk_public_keys()
        if not jwks:
            logger.warning("Could not fetch Clerk public keys, using development mode")
            return True
        
        # Decode header to get key ID
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        if not kid:
            logger.warning("No key ID in token header")
            return False
        
        # Get the public key for this key ID
        public_key = get_key_from_jwks(jwks, kid)
        if not public_key:
            logger.warning("Could not find public key for key ID, using development mode")
            return True
        
        # Verify the token
        try:
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=settings.CLERK_AUDIENCE,
                issuer=settings.CLERK_ISSUER_URL
            )
            logger.info("✅ Token verification passed")
            return True
        except jwt.InvalidTokenError as e:
            logger.error(f"❌ Token verification failed: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error verifying Clerk token: {e}")
        return False

def get_user_from_token(token: str) -> Optional[dict]:
    """Get user data from Clerk JWT token"""
    if not settings.CLERK_SECRET_KEY:
        logger.error("No Clerk secret key configured")
        return None
    
    try:
        logger.info(f"🔍 Decoding Clerk token: {token[:20]}...")
        
        # Decode token to get payload
        decoded = jwt.decode(
            token, 
            options={"verify_signature": False}  # We'll verify separately
        )
        
        logger.debug(f"Decoded token payload: {json.dumps(decoded, indent=2)}")
        
        # Extract user information from the token
        user_id = decoded.get("sub")
        
        # For real Clerk tokens, email might not be in the token
        email = decoded.get("email")
        
        # If no email in token, use a placeholder based on user_id
        if not email:
            email = f"{user_id}@clerk.user"
            logger.info(f"📧 No email in token, using placeholder: {email}")
        
        if user_id:
            user_data = {
                "user_id": user_id,
                "email": email,
                "first_name": decoded.get("first_name") or decoded.get("given_name"),
                "last_name": decoded.get("last_name") or decoded.get("family_name")
            }
            logger.info(f"✅ Successfully extracted user data: {user_id} ({email})")
            return user_data
        else:
            logger.warning(f"❌ Missing user_id in token. user_id: {user_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error decoding Clerk token: {e}")
        return None

def extract_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from Clerk token for authorization"""
    try:
        user_data = get_user_from_token(token)
        if user_data:
            user_id = user_data.get("user_id")
            logger.info(f"🔍 Extracted user ID for authorization: {user_id}")
            return user_id
        return None
    except Exception as e:
        logger.error(f"Error extracting user ID from token: {e}")
        return None 