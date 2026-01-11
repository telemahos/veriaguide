"""
Cache Warming Service - Preloads popular content into cache
"""
import asyncio
from typing import List, Dict, Any
from app.config import POST_TYPES
from app.services.cache_service import CacheService
from app.api.wordpress import get_all_posts_for_type, get_all_locations
from app.utils.logging_config import get_logger

logger = get_logger("cache_warming")


class CacheWarmingService:
    """Service for warming up the cache with popular content"""
    
    # Define popular/priority content to warm
    PRIORITY_POST_TYPES = [
        "museum",
        "archaeological_site",
        "religious_site",
        "restaurant",
        "cafe",
        "accommodation"
    ]
    
    @classmethod
    async def warm_all_caches(cls) -> Dict[str, Any]:
        """
        Warm all important caches on application startup
        Returns statistics about the warming process
        """
        logger.info("🔥 Starting cache warming process...")
        start_time = asyncio.get_event_loop().time()
        
        stats = {
            "success": True,
            "warmed_caches": [],
            "failed_caches": [],
            "total_items": 0,
            "duration_seconds": 0
        }
        
        try:
            # Warm post type caches concurrently
            await cls._warm_post_types(stats)
            
            # Warm map locations cache
            await cls._warm_map_locations(stats)
            
            # Calculate duration
            end_time = asyncio.get_event_loop().time()
            stats["duration_seconds"] = round(end_time - start_time, 2)
            
            logger.info(
                f"✅ Cache warming completed successfully! "
                f"Warmed {len(stats['warmed_caches'])} caches "
                f"with {stats['total_items']} items "
                f"in {stats['duration_seconds']}s"
            )
            
        except Exception as e:
            logger.error(f"❌ Cache warming failed: {str(e)}")
            stats["success"] = False
            stats["error"] = str(e)
        
        return stats
    
    @classmethod
    async def _warm_post_types(cls, stats: Dict[str, Any]) -> None:
        """Warm caches for all priority post types"""
        logger.info(f"Warming {len(cls.PRIORITY_POST_TYPES)} post type caches...")
        
        # Create tasks for concurrent warming
        tasks = []
        for post_type in cls.PRIORITY_POST_TYPES:
            tasks.append(cls._warm_single_post_type(post_type, stats))
        
        # Execute all tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
    
    @classmethod
    async def _warm_single_post_type(
        cls, 
        post_type: str, 
        stats: Dict[str, Any]
    ) -> None:
        """Warm cache for a single post type"""
        try:
            logger.debug(f"Warming cache for post type: {post_type}")
            
            # Fetch all posts (this will cache them via the API layer)
            posts = await get_all_posts_for_type(post_type)
            
            if posts:
                stats["warmed_caches"].append(post_type)
                stats["total_items"] += len(posts)
                logger.info(f"✓ Warmed {post_type}: {len(posts)} items")
            else:
                logger.warning(f"⚠ No items found for {post_type}")
                
        except Exception as e:
            logger.error(f"✗ Failed to warm {post_type}: {str(e)}")
            stats["failed_caches"].append({
                "type": post_type,
                "error": str(e)
            })
    
    @classmethod
    async def _warm_map_locations(cls, stats: Dict[str, Any]) -> None:
        """Warm cache for map locations"""
        try:
            logger.debug("Warming map locations cache...")
            
            # Fetch all locations (this will cache them)
            locations = await get_all_locations()
            
            if locations:
                stats["warmed_caches"].append("map_locations")
                stats["total_items"] += len(locations)
                logger.info(f"✓ Warmed map locations: {len(locations)} items")
            else:
                logger.warning("⚠ No map locations found")
                
        except Exception as e:
            logger.error(f"✗ Failed to warm map locations: {str(e)}")
            stats["failed_caches"].append({
                "type": "map_locations",
                "error": str(e)
            })
    
    @classmethod
    async def warm_specific_category(cls, post_type: str) -> Dict[str, Any]:
        """
        Warm cache for a specific category
        Useful for manual cache refresh after content updates
        """
        logger.info(f"Warming cache for specific category: {post_type}")
        
        stats = {
            "success": True,
            "post_type": post_type,
            "items_count": 0,
            "error": None
        }
        
        try:
            posts = await get_all_posts_for_type(post_type)
            stats["items_count"] = len(posts) if posts else 0
            logger.info(f"✓ Warmed {post_type}: {stats['items_count']} items")
            
        except Exception as e:
            logger.error(f"✗ Failed to warm {post_type}: {str(e)}")
            stats["success"] = False
            stats["error"] = str(e)
        
        return stats
    
    @classmethod
    async def invalidate_and_rewarm(cls, post_type: str) -> Dict[str, Any]:
        """
        Invalidate cache for a post type and immediately rewarm it
        Useful after content updates in WordPress
        """
        logger.info(f"Invalidating and rewarming cache for: {post_type}")
        
        try:
            # Invalidate existing cache
            pattern = f"wp_api_{post_type}*"
            deleted_count = await CacheService.delete_pattern(pattern)
            logger.info(f"Invalidated {deleted_count} cache entries for {post_type}")
            
            # Rewarm the cache
            result = await cls.warm_specific_category(post_type)
            result["invalidated_keys"] = deleted_count
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to invalidate and rewarm {post_type}: {str(e)}")
            return {
                "success": False,
                "post_type": post_type,
                "error": str(e)
            }
    
    @classmethod
    async def get_cache_warming_status(cls) -> Dict[str, Any]:
        """
        Get current status of cache warming
        Returns information about what's cached and what's not
        """
        status = {
            "cached_post_types": [],
            "missing_post_types": [],
            "total_cached_items": 0
        }
        
        try:
            redis = await CacheService.get_redis()
            
            # Check each post type
            for post_type in cls.PRIORITY_POST_TYPES:
                pattern = f"veriaguide:wp_api_{post_type}*"
                keys = await redis.keys(pattern)
                
                if keys:
                    status["cached_post_types"].append({
                        "type": post_type,
                        "cache_keys": len(keys)
                    })
                    status["total_cached_items"] += len(keys)
                else:
                    status["missing_post_types"].append(post_type)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get cache warming status: {str(e)}")
            return {
                "error": str(e)
            }
