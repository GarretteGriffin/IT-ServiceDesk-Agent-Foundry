"""Base HTTP client - no copy-paste httpx code across integrations"""

from typing import Any, Dict, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class HttpIntegrationClient:
    """
    Base HTTP client for all REST API integrations
    
    Provides:
    - Consistent error handling
    - Request/response logging
    - Timeout configuration
    - No retry logic yet (TODO: add tenacity)
    
    Subclass this for Graph, ServiceNow, Intune, etc.
    """
    
    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize HTTP client
        
        Args:
            base_url: Base URL for API (e.g., "https://graph.microsoft.com")
            headers: Default headers to include in all requests
            timeout: Request timeout in seconds
        """
        self._base_url = base_url
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers or {},
            timeout=timeout,
        )
        logger.info(f"Initialized HTTP client for {base_url}")
    
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with error handling
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            url: Relative URL path
            **kwargs: Additional arguments for httpx (json, params, etc.)
        
        Returns:
            JSON response as dict
        
        Raises:
            RuntimeError: If HTTP error occurs
        """
        logger.info(f"{method} {url}")
        
        try:
            resp = await self._client.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            logger.exception(f"HTTP client error on {method} {url}")
            raise RuntimeError(f"HTTP client error: {exc!r}") from exc
        
        if not resp.is_success:
            logger.error(
                f"HTTP error on {method} {url}: {resp.status_code} - {resp.text}"
            )
            raise RuntimeError(
                f"HTTP {resp.status_code} error from {url}: {resp.text}"
            )
        
        # Handle empty responses (204 No Content, etc.)
        if resp.status_code == 204 or not resp.content:
            return {}
        
        try:
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response from {url}: {e}")
            return {"raw_response": resp.text}
    
    async def close(self):
        """Close HTTP client"""
        await self._client.aclose()
        logger.info(f"Closed HTTP client for {self._base_url}")
