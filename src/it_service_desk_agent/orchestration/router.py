"""Agent router - no if-else soup, explicit intent registry"""

from typing import Dict, List
import time
from ..core.agent import Agent
from ..core.models import AgentRequest, AgentResponse, AgentError


class AgentRouter:
    """
    Routes requests to agents based on intent
    
    Fail-fast behavior:
    - Duplicate intent registration → ValueError on init
    - Unknown intent → structured error response
    - No keyword matching guesswork
    """
    
    def __init__(self, agents: List[Agent]) -> None:
        """
        Initialize router with agent list
        
        Args:
            agents: List of agents to register
        
        Raises:
            ValueError: If multiple agents claim the same intent
        """
        self._intent_map: Dict[str, Agent] = {}
        
        for agent in agents:
            for intent in agent.supported_intents:
                if intent in self._intent_map:
                    existing = self._intent_map[intent].name
                    raise ValueError(
                        f"Intent '{intent}' claimed by both '{existing}' and '{agent.name}'. "
                        f"Fix agent definitions - intents must be unique."
                    )
                self._intent_map[intent] = agent
        
        # Log registered intents
        print(f"Router initialized with {len(self._intent_map)} intents across {len(agents)} agents")
        for intent, agent in self._intent_map.items():
            print(f"  - {intent} → {agent.name}")
    
    async def route(self, request: AgentRequest) -> AgentResponse:
        """
        Route request to appropriate agent
        
        Args:
            request: Structured request with intent
        
        Returns:
            AgentResponse from the handling agent, or error if intent unknown
        """
        start_time = time.time()
        
        agent = self._intent_map.get(request.intent)
        
        if not agent:
            return AgentResponse(
                success=False,
                error=AgentError(
                    code="UNKNOWN_INTENT",
                    message=f"No agent registered for intent '{request.intent}'",
                    details={
                        "requested_intent": request.intent,
                        "available_intents": list(self._intent_map.keys())
                    }
                )
            )
        
        # Route to agent
        response = await agent.handle(request)
        
        # Add execution metadata
        execution_time = int((time.time() - start_time) * 1000)
        response.agent_name = agent.name
        response.execution_time_ms = execution_time
        
        return response
    
    def get_available_intents(self) -> List[str]:
        """Get list of all registered intents"""
        return list(self._intent_map.keys())
    
    def get_agent_for_intent(self, intent: str) -> str:
        """Get agent name for a given intent"""
        agent = self._intent_map.get(intent)
        return agent.name if agent else "unknown"
