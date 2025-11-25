"""Agent router - no if-else soup, explicit intent registry"""

from typing import Dict, List, Optional
import time
import logging
from ..core.agent import Agent
from ..core.models import AgentRequest, AgentResponse, AgentError

logger = logging.getLogger(__name__)


class AgentRouter:
    """
    Routes requests to agents based on intent
    
    Fail-fast behavior:
    - Duplicate intent registration → ValueError
    - Unknown intent → structured error response
    - No keyword matching guesswork
    """
    
    def __init__(self, agents: Optional[List[Agent]] = None) -> None:
        """
        Initialize router
        
        Args:
            agents: Optional list of agents to register immediately
        
        Raises:
            ValueError: If multiple agents claim the same intent
        """
        self._intent_map: Dict[str, Agent] = {}
        
        if agents:
            for agent in agents:
                self.register_agent(agent)
    
    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent with the router
        
        Args:
            agent: Agent to register
        
        Raises:
            ValueError: If agent's intents conflict with existing registrations
        """
        for intent in agent.supported_intents:
            if intent in self._intent_map:
                existing = self._intent_map[intent].name
                raise ValueError(
                    f"Intent '{intent}' claimed by both '{existing}' and '{agent.name}'. "
                    f"Fix agent definitions - intents must be unique."
                )
            self._intent_map[intent] = agent
        
        logger.info(f"Registered agent '{agent.name}' with {len(agent.supported_intents)} intents")
        for intent in agent.supported_intents:
            logger.debug(f"  - {intent} → {agent.name}")
    
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


def register_default_agents(router: AgentRouter, settings) -> None:
    """
    Register all default agents with the router
    
    This function:
    1. Instantiates integration clients (Graph, ServiceNow, PowerShell)
    2. Instantiates tool layers (AD tools, Graph tools, etc.)
    3. Instantiates concrete agents (IdentityAgent, DeviceAgent, etc.)
    4. Registers all agents with the router
    
    Args:
        router: Router to register agents with
        settings: Application settings (from config.py)
    
    Note:
        This is a placeholder that will be fully implemented after
        agents and tools are created in subsequent phases.
    """
    logger.info("Registering default agents...")
    
    # TODO: Implement agent registration after creating:
    # - Integration clients (PHASE 5)
    # - Tool layer (PHASE 6)
    # - Concrete agents (PHASE 7)
    
    # Example (will be implemented):
    # from ..integrations.powershell import PowerShellExecutor
    # from ..integrations.microsoft_graph import MicrosoftGraphClient
    # from ..integrations.servicenow import ServiceNowClient
    # from ..tools.active_directory import ActiveDirectoryTools
    # from ..tools.graph_user import GraphUserTools
    # from ..agents.identity_agent import IdentityAgent
    #
    # ps = PowerShellExecutor()
    # graph = MicrosoftGraphClient(settings)
    # ad_tools = ActiveDirectoryTools(ps)
    # graph_tools = GraphUserTools(graph)
    # identity_agent = IdentityAgent(ad_tools, graph_tools)
    # router.register_agent(identity_agent)
    
    logger.warning("register_default_agents is a placeholder - agents will be added in PHASE 7")
