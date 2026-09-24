"""
HTTP Service - Optimized HTTP client with connection pooling
"""
from typing import Any

import httpx

from app.config import HTTP_POOL_CONNECTIONS, HTTP_POOL_MAXSIZE, HTTP_TIMEOUT, WP_API_TIMEOUT


class HTTPService:
    """Optimized HTTP service with connection pooling and timeout management"""
    
    _client = None
    _wp_client = None
    
    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """Get general HTTP client with connection pooling"""
        if cls._client is None:
            limits = httpx.Limits(
                max_keepalive_connections=HTTP_POOL_CONNECTIONS,
                max_connections=HTTP_POOL_MAXSIZE,
                keepalive_expiry=30.0
            )
            
            timeout = httpx.Timeout(
                connect=10.0,
                read=HTTP_TIMEOUT,
                write=10.0,
                pool=5.0
            )
            
            cls._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                http2=False,  # Disable HTTP/2 to avoid h2 dependency
                follow_redirects=True,
                headers={
                    'User-Agent': 'VeriaGuide/1.0 (Tourism Directory)',
                    'Accept': 'application/json, text/html, */*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive'
                }
            )
        
        return cls._client
    
    @classmethod
    async def get_wp_client(cls) -> httpx.AsyncClient:
        """Get WordPress-specific HTTP client with optimized settings"""
        if cls._wp_client is None:
            limits = httpx.Limits(
                max_keepalive_connections=HTTP_POOL_CONNECTIONS,
                max_connections=HTTP_POOL_MAXSIZE,
                keepalive_expiry=60.0  # Longer keepalive for WordPress API
            )
            
            timeout = httpx.Timeout(
                connect=10.0,
                read=WP_API_TIMEOUT,
                write=15.0,
                pool=5.0
            )
            
            cls._wp_client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                http2=False,
                follow_redirects=True,
                headers={
                    'User-Agent': 'VeriaGuide/1.0 WordPress Client',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Cache-Control': 'no-cache'
                }
            )
        
        return cls._wp_client
    
    @classmethod
    async def close_clients(cls):
        """Close all HTTP clients and clean up connections"""
        if cls._client:
            await cls._client.aclose()
            cls._client = None
        
        if cls._wp_client:
            await cls._wp_client.aclose()
            cls._wp_client = None
    
    @classmethod
    async def get(
        cls,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        use_wp_client: bool = False,
        **kwargs
    ) -> httpx.Response:
        """Make GET request with appropriate client"""
        client = await cls.get_wp_client() if use_wp_client else await cls.get_client()
        
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        return await client.get(url, params=params, headers=request_headers, **kwargs)
    
    @classmethod
    async def post(
        cls,
        url: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        use_wp_client: bool = False,
        **kwargs
    ) -> httpx.Response:
        """Make POST request with appropriate client"""
        client = await cls.get_wp_client() if use_wp_client else await cls.get_client()
        
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        return await client.post(
            url, data=data, json=json, headers=request_headers, **kwargs
        )
    
    @classmethod
    async def request(
        cls,
        method: str,
        url: str,
        use_wp_client: bool = False,
        **kwargs
    ) -> httpx.Response:
        """Make request with specified method"""
        client = await cls.get_wp_client() if use_wp_client else await cls.get_client()
        return await client.request(method, url, **kwargs)
    
    @classmethod
    async def get_connection_info(cls) -> dict[str, Any]:
        """Get information about current connections"""
        info = {
            "general_client": None,
            "wp_client": None
        }
        
        if cls._client:
            info["general_client"] = {
                "is_closed": cls._client.is_closed,
                "limits": {
                    "max_keepalive_connections": cls._client._limits.max_keepalive_connections,
                    "max_connections": cls._client._limits.max_connections,
                }
            }
        
        if cls._wp_client:
            info["wp_client"] = {
                "is_closed": cls._wp_client.is_closed,
                "limits": {
                    "max_keepalive_connections": cls._wp_client._limits.max_keepalive_connections,
                    "max_connections": cls._wp_client._limits.max_connections,
                }
            }
        
        return info


# Context manager for HTTP clients
class HTTPClientManager:
    """Context manager for HTTP clients lifecycle"""
    
    async def __aenter__(self):
        return HTTPService
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await HTTPService.close_clients()