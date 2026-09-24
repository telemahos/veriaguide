"""
Health Service - Application and dependency health checks
"""
from datetime import datetime
from typing import Any

from app.config import WP_API_URL
from app.services.cache_service import CacheService
from app.services.http_service import HTTPService
from app.utils.logging_config import get_logger

logger = get_logger("health")


class HealthService:
    """Service for health checks of application and dependencies"""
    
    @staticmethod
    async def check_wordpress() -> dict[str, Any]:
        """Check WordPress API connectivity"""
        try:
            # Try to fetch WordPress API root
            response = await HTTPService.get(
                f"{WP_API_URL.split('/wp-json')[0]}/wp-json/",
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "url": WP_API_URL,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
                }
            else:
                return {
                    "status": "unhealthy",
                    "url": WP_API_URL,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            logger.error(f"WordPress health check failed: {e}")
            return {
                "status": "unhealthy",
                "url": WP_API_URL,
                "error": str(e)
            }
    
    @staticmethod
    async def check_redis() -> dict[str, Any]:
        """Check Redis connectivity"""
        try:
            is_healthy = await CacheService.health_check()
            
            if is_healthy:
                info = await CacheService.get_cache_info()
                return {
                    "status": "healthy",
                    "redis_version": str(info.get("redis_version", "unknown")),
                    "memory_used": str(info.get("used_memory", "unknown")),
                    "connected_clients": int(info.get("connected_clients", 0)) if info.get("connected_clients") else 0,
                    "total_keys": int(info.get("total_keys", 0)) if info.get("total_keys") else 0
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Redis ping failed"
                }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @staticmethod
    async def check_database() -> dict[str, Any]:
        """Check database connectivity via WordPress"""
        try:
            # Try to fetch WordPress users endpoint (requires DB)
            response = await HTTPService.get(
                f"{WP_API_URL}/users",
                timeout=5
            )
            
            if response.status_code in [200, 401]:  # 401 is OK (auth required)
                return {
                    "status": "healthy",
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @staticmethod
    async def full_health_check() -> dict[str, Any]:
        """Perform full health check of all dependencies"""
        logger.info("Performing full health check...")
        
        # Check all services concurrently
        
        wordpress_check = await HealthService.check_wordpress()
        redis_check = await HealthService.check_redis()
        database_check = await HealthService.check_database()
        
        # Determine overall status
        all_healthy = all([
            wordpress_check.get("status") == "healthy",
            redis_check.get("status") == "healthy",
            database_check.get("status") == "healthy"
        ])
        
        overall_status = "healthy" if all_healthy else "degraded"
        
        # Count unhealthy services
        unhealthy_count = sum([
            1 for check in [wordpress_check, redis_check, database_check]
            if check.get("status") != "healthy"
        ])
        
        result = {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "wordpress": wordpress_check,
                "redis": redis_check,
                "database": database_check
            },
            "summary": {
                "healthy_services": 3 - unhealthy_count,
                "unhealthy_services": unhealthy_count,
                "all_healthy": all_healthy
            }
        }
        
        if all_healthy:
            logger.info("✅ All services healthy")
        else:
            logger.warning(f"⚠️ {unhealthy_count} service(s) unhealthy")
        
        return result
    
    @staticmethod
    async def get_detailed_status() -> dict[str, Any]:
        """Get detailed application status"""
        health = await HealthService.full_health_check()
        
        return {
            "application": {
                "status": health["status"],
                "timestamp": health["timestamp"]
            },
            "dependencies": health["services"],
            "summary": health["summary"]
        }
