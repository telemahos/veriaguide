"""
Redis-based Rate Limiting Service for VeriaGuide
Supports distributed rate limiting across multiple workers
"""
import time
from typing import Any

from app.services.cache_service import CacheService
from app.utils.logging_config import get_logger

logger = get_logger("rate_limit")


class RateLimitService:
    """Redis-based rate limiting service for distributed systems"""
    
    @staticmethod
    async def check_rate_limit(
        key: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> dict[str, Any]:
        """
        Check if a request is within rate limit
        
        Args:
            key: Unique identifier (e.g., IP address, user ID)
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
            
        Returns:
            {
                "allowed": bool,
                "remaining": int,
                "reset_at": int (unix timestamp),
                "retry_after": int (seconds)
            }
        """
        try:
            redis = await CacheService.get_redis()
            
            # Create rate limit key
            rate_limit_key = f"rate_limit:{key}"
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Remove old requests outside the window
            await redis.zremrangebyscore(rate_limit_key, 0, window_start)
            
            # Count requests in current window
            request_count = await redis.zcard(rate_limit_key)
            
            # Check if limit exceeded
            if request_count >= max_requests:
                # Get the oldest request timestamp
                oldest_request = await redis.zrange(rate_limit_key, 0, 0, withscores=True)
                if oldest_request:
                    oldest_time = int(oldest_request[0][1])
                    reset_at = oldest_time + window_seconds
                    retry_after = max(0, reset_at - current_time)
                else:
                    reset_at = current_time + window_seconds
                    retry_after = window_seconds
                
                logger.warning(f"Rate limit exceeded for key: {key}")
                
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_at": reset_at,
                    "retry_after": retry_after
                }
            
            # Add current request
            await redis.zadd(rate_limit_key, {str(current_time): current_time})
            
            # Set expiration on the key
            await redis.expire(rate_limit_key, window_seconds + 1)
            
            remaining = max_requests - request_count - 1
            reset_at = current_time + window_seconds
            
            return {
                "allowed": True,
                "remaining": remaining,
                "reset_at": reset_at,
                "retry_after": 0
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow the request (fail open)
            return {
                "allowed": True,
                "remaining": max_requests,
                "reset_at": int(time.time()) + window_seconds,
                "retry_after": 0
            }
    
    @staticmethod
    async def reset_rate_limit(key: str) -> bool:
        """Reset rate limit for a specific key"""
        try:
            redis = await CacheService.get_redis()
            rate_limit_key = f"rate_limit:{key}"
            await redis.delete(rate_limit_key)
            logger.info(f"Rate limit reset for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False
    
    @staticmethod
    async def get_rate_limit_status(key: str, window_seconds: int = 60) -> dict[str, Any]:
        """Get current rate limit status for a key"""
        try:
            redis = await CacheService.get_redis()
            rate_limit_key = f"rate_limit:{key}"
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Remove old requests
            await redis.zremrangebyscore(rate_limit_key, 0, window_start)
            
            # Get request count
            request_count = await redis.zcard(rate_limit_key)
            
            # Get TTL
            ttl = await redis.ttl(rate_limit_key)
            
            return {
                "key": key,
                "request_count": request_count,
                "ttl": ttl if ttl > 0 else 0,
                "window_seconds": window_seconds
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {
                "key": key,
                "request_count": 0,
                "ttl": 0,
                "window_seconds": window_seconds,
                "error": str(e)
            }
    
    @staticmethod
    async def cleanup_expired_limits() -> int:
        """Clean up expired rate limit keys (maintenance task)"""
        try:
            redis = await CacheService.get_redis()
            
            # Find all rate limit keys
            pattern = "rate_limit:*"
            keys = await redis.keys(pattern)
            
            deleted_count = 0
            for key in keys:
                # Check if key has expired
                ttl = await redis.ttl(key)
                if ttl == -2:  # Key doesn't exist
                    deleted_count += 1
                elif ttl == -1:  # Key exists but has no expiration
                    # Set expiration to 1 hour
                    await redis.expire(key, 3600)
            
            logger.info(f"Cleaned up {deleted_count} expired rate limit keys")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup rate limits: {e}")
            return 0
