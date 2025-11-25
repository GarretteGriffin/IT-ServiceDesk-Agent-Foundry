"""
Thin wrapper around it_service_desk_agent.entrypoint

This file exists for backward compatibility and Azure AI Foundry integration.
All real logic lives in the it_service_desk_agent package.
"""

from it_service_desk_agent.entrypoint import handle_request, handle_request_async

# Re-export for Azure AI Foundry
__all__ = ["handle_request", "handle_request_async"]
