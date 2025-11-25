"""
IT Service Desk Agent - Core package

Minimal public API for Azure AI Foundry integration.
"""

from .config import Settings
from .core.models import AgentRequest, AgentResponse
from .orchestration.router import AgentRouter

__all__ = [
    "Settings",
    "AgentRequest",
    "AgentResponse",
    "AgentRouter",
]
