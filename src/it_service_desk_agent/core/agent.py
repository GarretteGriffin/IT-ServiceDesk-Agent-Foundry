"""Agent protocol - every agent must implement this, no exceptions"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import AgentRequest, AgentResponse


class AgentCapability:
    """
    Describes a tool/capability the agent can use
    
    Used for:
    - Prompt construction (showing available tools)
    - Documentation generation
    - Capability discovery
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any] | None = None
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema or {}
    
    def __repr__(self) -> str:
        return f"AgentCapability(name={self.name!r})"


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
    
    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """
        Structured list of tools/capabilities available to this agent
        
        Used for:
        - Building prompts that describe available tools
        - Documentation generation
        - API schema generation
        
        Return empty list if agent has no discrete capabilities
        (e.g., pure LLM-based agents without tools).
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
