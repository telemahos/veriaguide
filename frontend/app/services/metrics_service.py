"""
Metrics Service - Tracks application performance metrics
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from collections import defaultdict
from app.services.cache_service import CacheService
from app.utils.logging_config import get_logger

logger = get_logger("metrics")


class MetricsService:
    """Service for tracking and reporting application metrics"""
    
    # In-memory metrics storage
    _metrics = {
        "requests": defaultdict(list),
        "cache_hits": 0,
        "cache_misses": 0,
        "errors": defaultdict(int),
        "response_times": [],
        "api_calls": defaultdict(list)
    }
    
    _start_time = datetime.now()
    
    @classmethod
    def record_request(cls, path: str, method: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        cls._metrics["requests"][path].append({
            "method": method,
            "status": status_code,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })
        cls._metrics["response_times"].append(duration)
        
        # Keep only last 1000 requests
        if len(cls._metrics["response_times"]) > 1000:
            cls._metrics["response_times"] = cls._metrics["response_times"][-1000:]
    
    @classmethod
    def record_cache_hit(cls):
        """Record cache hit"""
        cls._metrics["cache_hits"] += 1
    
    @classmethod
    def record_cache_miss(cls):
        """Record cache miss"""
        cls._metrics["cache_misses"] += 1
    
    @classmethod
    def record_error(cls, error_type: str):
        """Record error"""
        cls._metrics["errors"][error_type] += 1
    
    @classmethod
    def record_api_call(cls, endpoint: str, duration: float, status: int):
        """Record WordPress API call"""
        cls._metrics["api_calls"][endpoint].append({
            "duration": duration,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
    
    @classmethod
    async def get_metrics(cls) -> Dict[str, Any]:
        """Get current metrics"""
        uptime = datetime.now() - cls._start_time
        
        # Calculate cache stats
        total_cache_requests = cls._metrics["cache_hits"] + cls._metrics["cache_misses"]
        cache_hit_rate = (
            (cls._metrics["cache_hits"] / total_cache_requests * 100)
            if total_cache_requests > 0 else 0
        )
        
        # Calculate response time stats
        response_times = cls._metrics["response_times"]
        avg_response_time = (
            sum(response_times) / len(response_times)
            if response_times else 0
        )
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # Get Redis info
        redis_info = await CacheService.get_cache_info()
        
        # Calculate API stats
        api_stats = {}
        for endpoint, calls in cls._metrics["api_calls"].items():
            if calls:
                durations = [c["duration"] for c in calls]
                api_stats[endpoint] = {
                    "calls": len(calls),
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations)
                }
        
        return {
            "uptime": {
                "seconds": int(uptime.total_seconds()),
                "formatted": str(uptime).split('.')[0]
            },
            "requests": {
                "total": sum(len(v) for v in cls._metrics["requests"].values()),
                "by_path": {
                    path: len(requests)
                    for path, requests in cls._metrics["requests"].items()
                }
            },
            "cache": {
                "hits": cls._metrics["cache_hits"],
                "misses": cls._metrics["cache_misses"],
                "hit_rate": f"{cache_hit_rate:.2f}%",
                "redis": redis_info
            },
            "response_times": {
                "average": f"{avg_response_time:.2f}ms",
                "min": f"{min_response_time:.2f}ms",
                "max": f"{max_response_time:.2f}ms",
                "total_requests": len(response_times)
            },
            "errors": dict(cls._metrics["errors"]),
            "api_calls": api_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    async def get_health_metrics(cls) -> Dict[str, Any]:
        """Get health check metrics"""
        redis_healthy = await CacheService.health_check()
        
        # Calculate error rate
        total_requests = sum(len(v) for v in cls._metrics["requests"].values())
        total_errors = sum(cls._metrics["errors"].values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate cache hit rate
        total_cache = cls._metrics["cache_hits"] + cls._metrics["cache_misses"]
        cache_hit_rate = (
            (cls._metrics["cache_hits"] / total_cache * 100)
            if total_cache > 0 else 0
        )
        
        return {
            "status": "healthy" if redis_healthy and error_rate < 5 else "degraded",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "error_rate": f"{error_rate:.2f}%",
            "cache_hit_rate": f"{cache_hit_rate:.2f}%",
            "total_requests": total_requests,
            "total_errors": total_errors
        }
    
    @classmethod
    def reset_metrics(cls):
        """Reset all metrics (for testing)"""
        cls._metrics = {
            "requests": defaultdict(list),
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": defaultdict(int),
            "response_times": [],
            "api_calls": defaultdict(list)
        }
        cls._start_time = datetime.now()
        logger.info("Metrics reset")
