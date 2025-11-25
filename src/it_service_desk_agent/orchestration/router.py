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
    """
    logger.info("Registering default agents...")
    
    # Import integration clients
    from ..integrations.powershell import PowerShellExecutor
    from ..integrations.microsoft_graph import MicrosoftGraphClient
    from ..integrations.servicenow import ServiceNowClient
    
    # Import tool layers
    from ..tools.active_directory import ActiveDirectoryTools
    from ..tools.graph_user import GraphUserTools
    from ..tools.servicenow_tools import ServiceNowTools
    from ..tools.intune_tools import IntuneDeviceTools
    
    # Import concrete agents
    from ..agents.identity_agent import IdentityAgent
    from ..agents.device_agent import DeviceAgent
    from ..agents.ticket_agent import TicketAgent
    
    # Instantiate integration clients
    ps_executor = PowerShellExecutor(base_script_path=settings.ps_script_path)
    
    graph_client = MicrosoftGraphClient(
        tenant_id=settings.graph_tenant_id,
        client_id=settings.graph_client_id,
        client_secret=settings.graph_client_secret,
        base_url=settings.graph_base_url
    )
    
    snow_client = ServiceNowClient(
        instance_url=settings.snow_instance_url,
        username=settings.snow_username,
        password=settings.snow_password
    )
    
    # Instantiate tool layers
    ad_tools = ActiveDirectoryTools(ps_executor, domain=settings.ad_domain)
    graph_tools = GraphUserTools(graph_client)
    snow_tools = ServiceNowTools(snow_client)
    intune_tools = IntuneDeviceTools(graph_client)
    
    # Instantiate and register all agents
    identity_agent = IdentityAgent(ad_tools, graph_tools)
    router.register_agent(identity_agent)
    
    device_agent = DeviceAgent(intune_tools)
    router.register_agent(device_agent)
    
    ticket_agent = TicketAgent(snow_tools)
    router.register_agent(ticket_agent)
    
    logger.info(f"Registered {len(router.get_available_intents())} intents across 3 agents")
