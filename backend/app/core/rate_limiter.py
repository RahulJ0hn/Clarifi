from fastapi import HTTPException, Request, status
from typing import Dict, Tuple
import time
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.cleanup_interval = 3600  # Clean up old entries every hour
        self.last_cleanup = time.time()
    
    def _cleanup_old_requests(self):
        """Remove old request timestamps to prevent memory leaks"""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            cutoff_time = current_time - 3600  # Keep only last hour
            
            for client_id in list(self.requests.keys()):
                self.requests[client_id] = [
                    req_time for req_time in self.requests[client_id] 
                    if req_time > cutoff_time
                ]
                
                # Remove empty entries
                if not self.requests[client_id]:
                    del self.requests[client_id]
            
            self.last_cleanup = current_time
            logger.debug(f"Rate limiter cleanup completed. Active clients: {len(self.requests)}")
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Use user ID if authenticated, otherwise use IP
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user_{user_id}"
        else:
            # Use IP address for unauthenticated requests
            client_ip = request.client.host if request.client else "unknown"
            return f"ip_{client_ip}"
    
    def check_rate_limit(self, request: Request, limit_per_minute: int = None, limit_per_hour: int = None) -> bool:
        """
        Check if request is within rate limits
        Returns True if allowed, False if rate limited
        """
        try:
            self._cleanup_old_requests()
            
            client_id = self._get_client_id(request)
            current_time = time.time()
            
            # Initialize client requests if not exists
            if client_id not in self.requests:
                self.requests[client_id] = []
            
            # Add current request
            self.requests[client_id].append(current_time)
            
            # Use default limits if not specified
            if limit_per_minute is None:
                limit_per_minute = settings.RATE_LIMIT_PER_MINUTE
            if limit_per_hour is None:
                limit_per_hour = settings.RATE_LIMIT_PER_HOUR
            
            # Check minute limit
            minute_ago = current_time - 60
            requests_last_minute = len([
                req_time for req_time in self.requests[client_id] 
                if req_time > minute_ago
            ])
            
            if requests_last_minute > limit_per_minute:
                logger.warning(f"Rate limit exceeded for {client_id}: {requests_last_minute} requests in last minute")
                return False
            
            # Check hour limit
            hour_ago = current_time - 3600
            requests_last_hour = len([
                req_time for req_time in self.requests[client_id] 
                if req_time > hour_ago
            ])
            
            if requests_last_hour > limit_per_hour:
                logger.warning(f"Rate limit exceeded for {client_id}: {requests_last_hour} requests in last hour")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            # Allow request on error to prevent blocking legitimate users
            return True
    
    def get_rate_limit_info(self, request: Request) -> Dict[str, int]:
        """Get current rate limit information for client"""
        try:
            client_id = self._get_client_id(request)
            current_time = time.time()
            
            if client_id not in self.requests:
                return {
                    "requests_last_minute": 0,
                    "requests_last_hour": 0,
                    "limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
                    "limit_per_hour": settings.RATE_LIMIT_PER_HOUR
                }
            
            minute_ago = current_time - 60
            hour_ago = current_time - 3600
            
            requests_last_minute = len([
                req_time for req_time in self.requests[client_id] 
                if req_time > minute_ago
            ])
            
            requests_last_hour = len([
                req_time for req_time in self.requests[client_id] 
                if req_time > hour_ago
            ])
            
            return {
                "requests_last_minute": requests_last_minute,
                "requests_last_hour": requests_last_hour,
                "limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
                "limit_per_hour": settings.RATE_LIMIT_PER_HOUR
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {
                "requests_last_minute": 0,
                "requests_last_hour": 0,
                "limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
                "limit_per_hour": settings.RATE_LIMIT_PER_HOUR
            }

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Middleware to apply rate limiting to requests"""
    try:
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Check rate limit
        if not rate_limiter.check_rate_limit(request):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60"
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        # Get rate limit info for headers
        rate_info = rate_limiter.get_rate_limit_info(request)
        
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit_per_minute"])
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, rate_info["limit_per_minute"] - rate_info["requests_last_minute"])
        )
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in rate limit middleware: {e}")
        # Allow request on error
        return await call_next(request) 