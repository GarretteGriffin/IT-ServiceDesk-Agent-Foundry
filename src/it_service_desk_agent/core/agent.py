"""Agent protocol - every agent must implement this, no exceptions"""

from abc import ABC, abstractmethod
from typing import List
from .models import AgentRequest, AgentResponse


class Agent(ABC):
    """
    Agent protocol - strict interface for all agents
    
    Every agent MUST:
    1. Declare its name
    2. Declare which intents it handles
    3. Implement handle() method with proper error handling
    
    No ad-hoc function calls, no bypassing this contract.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for logging and identification"""
        ...
    
    @property
    @abstractmethod
    def supported_intents(self) -> List[str]:
        """
        List of intents this agent can handle
        
        Examples:
        - "ad.user.lookup"
        - "ad.password.reset"
        - "graph.user.get"
        - "servicenow.incident.create"
        
        Router uses this for dispatch. Declare everything you handle.
        """
        ...
    
    @abstractmethod
    async def handle(self, request: AgentRequest) -> AgentResponse:
        """
        Handle a request
        
        MUST:
        - Validate request.parameters
        - Check authorization via security layer
        - Return structured AgentResponse
        - Never raise exceptions (catch and return error response)
        
        Args:
            request: Structured request with intent, parameters, context
        
        Returns:
            AgentResponse with success/failure and data/error
        """
        ...
