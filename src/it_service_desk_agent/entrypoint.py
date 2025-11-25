"""
Azure AI Foundry-compatible entrypoint

This module provides the main handler for requests coming from Azure AI Foundry.
It instantiates the router with all agents and processes requests.
"""

from typing import Dict, Any
from .config import Settings
from .core.models import AgentRequest, AgentResponse
from .orchestration.router import AgentRouter, register_default_agents


# Global instances (initialized once, reused across requests)
_settings: Settings | None = None
_router: AgentRouter | None = None


def _ensure_initialized() -> tuple[Settings, AgentRouter]:
    """Lazy initialization of settings and router"""
    global _settings, _router
    
    if _settings is None:
        _settings = Settings()
    
    if _router is None:
        _router = AgentRouter()
        register_default_agents(_router, _settings)
    
    return _settings, _router


def handle_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Azure AI Foundry-compatible handler
    
    Args:
        payload: JSON-serializable request from Foundry containing:
            - intent: str (e.g., "identity.reset_password")
            - parameters: dict (intent-specific params)
            - context: dict (user_id, source, correlation_id, etc.)
    
    Returns:
        JSON-serializable response containing:
            - success: bool
            - data: dict | None
            - error: dict | None
            - agent_name: str
            - execution_time_ms: int
    
    Example:
        >>> payload = {
        ...     "intent": "identity.get_user",
        ...     "parameters": {"upn": "user@example.com"},
        ...     "context": {
        ...         "user_id": "admin@example.com",
        ...         "source": "teams",
        ...         "correlation_id": "abc-123",
        ...         "risk_level": "low",
        ...         "approval_granted": False
        ...     }
        ... }
        >>> response = handle_request(payload)
        >>> response["success"]
        True
    """
    _settings, router = _ensure_initialized()
    
    # Convert payload to AgentRequest
    request = AgentRequest(**payload)
    
    # Route through the agent system
    response: AgentResponse = router.route(request)
    
    # Convert response to dict for JSON serialization
    return response.model_dump()


async def handle_request_async(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async version of handle_request for async-compatible environments
    
    Args:
        payload: Same as handle_request
    
    Returns:
        Same as handle_request
    """
    _settings, router = _ensure_initialized()
    
    request = AgentRequest(**payload)
    response: AgentResponse = await router.route(request)
    
    return response.model_dump()
