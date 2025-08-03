"""
Cache Service - Handles Redis caching operations
"""
import json
import hashlib
from typing import Any, Optional, Union
import aioredis
from app.config import REDIS_URL, REDIS_CACHE_PREFIX, REDIS_DEFAULT_TTL


class CacheService:
    """Service class for handling Redis cache operations"""
    
    _redis_pool = None
    
    @classmethod
    async def get_redis(cls) -> aioredis.Redis:
        """Get Redis connection pool (singleton pattern)"""
        if cls._redis_pool is None:
            cls._redis_pool = aioredis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
        return cls._redis_pool
    
    @classmethod
    async def close_redis(cls):
        """Close Redis connection"""
        if cls._redis_pool:
            await cls._redis_pool.close()
            cls._redis_pool = None
    
    @staticmethod
    def _generate_cache_key(key: str, params: Optional[dict] = None) -> str:
        """Generate a cache key with optional parameters"""
        if params:
            # Sort params for consistent key generation
            sorted_params = json.dumps(params, sort_keys=True)
            key_hash = hashlib.md5(f"{key}_{sorted_params}".encode()).hexdigest()
            return f"{REDIS_CACHE_PREFIX}{key}_{key_hash}"
        return f"{REDIS_CACHE_PREFIX}{key}"
    
    @classmethod
    async def get(cls, key: str, params: Optional[dict] = None) -> Optional[Any]:
        """Get value from cache"""
        try:
            redis = await cls.get_redis()
            cache_key = cls._generate_cache_key(key, params)
            
            cached_value = await redis.get(cache_key)
            if cached_value:
                return json.loads(cached_value)
            return None
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")
            return None
    
    @classmethod
    async def set(
        cls, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        params: Optional[dict] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        try:
            redis = await cls.get_redis()
            cache_key = cls._generate_cache_key(key, params)
            
            serialized_value = json.dumps(value, default=str)
            ttl = ttl or REDIS_DEFAULT_TTL
            
            await redis.setex(cache_key, ttl, serialized_value)
            return True
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False
    
    @classmethod
    async def delete(cls, key: str, params: Optional[dict] = None) -> bool:
        """Delete value from cache"""
        try:
            redis = await cls.get_redis()
            cache_key = cls._generate_cache_key(key, params)
            
            result = await redis.delete(cache_key)
            return result > 0
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False
    
    @classmethod
    async def delete_pattern(cls, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        try:
            redis = await cls.get_redis()
            cache_pattern = f"{REDIS_CACHE_PREFIX}{pattern}"
            
            keys = await redis.keys(cache_pattern)
            if keys:
                return await redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error for pattern {pattern}: {e}")
            return 0
    
    @classmethod
    async def clear_all(cls) -> bool:
        """Clear all cache entries with our prefix"""
        try:
            redis = await cls.get_redis()
            keys = await redis.keys(f"{REDIS_CACHE_PREFIX}*")
            if keys:
                await redis.delete(*keys)
            return True
        except Exception as e:
            print(f"Cache clear all error: {e}")
            return False
    
    @classmethod
    async def get_cache_info(cls) -> dict:
        """Get cache statistics and info"""
        try:
            redis = await cls.get_redis()
            info = await redis.info()
            keys = await redis.keys(f"{REDIS_CACHE_PREFIX}*")
            
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_keys": len(keys),
                "cache_prefix": REDIS_CACHE_PREFIX,
                "default_ttl": REDIS_DEFAULT_TTL
            }
        except Exception as e:
            print(f"Cache info error: {e}")
            return {"error": str(e)}
    
    @classmethod
    async def health_check(cls) -> bool:
        """Check if Redis is healthy"""
        try:
            redis = await cls.get_redis()
            await redis.ping()
            return True
        except Exception as e:
            print(f"Redis health check failed: {e}")
            return False


# Decorator for caching function results
def cache_result(key: str, ttl: Optional[int] = None, use_params: bool = True):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function parameters if use_params is True
            cache_params = None
            if use_params:
                cache_params = {
                    'args': args[1:] if args else [],  # Skip 'self' if present
                    'kwargs': kwargs
                }
            
            # Try to get from cache first
            cached_result = await CacheService.get(key, cache_params)
            if cached_result is not None:
                print(f"Cache hit for key: {key}")
                return cached_result
            
            # Execute function and cache result
            print(f"Cache miss for key: {key}")
            result = await func(*args, **kwargs)
            
            # Cache the result
            await CacheService.set(key, result, ttl, cache_params)
            return result
        
        return wrapper
    return decorator