"""
Multi-Agent IT Service Desk System
Coordinates orchestrator and specialist agents for enterprise IT operations
"""

import asyncio
from typing import Optional

from src.agents.orchestrator import OrchestratorAgent
from src.agents.ad_agent import ActiveDirectoryAgent
from src.agents.graph_agent import MicrosoftGraphAgent
from src.agents.intune_agent import IntuneAgent
from src.agents.servicenow_agent import ServiceNowAgent
from src.agents.knowledge_agent import KnowledgeBaseAgent
from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class MultiAgentITServiceDesk:
    """
    Multi-agent IT Service Desk system using Azure AI Foundry
    
    Architecture:
    - 1 Orchestrator Agent (routes requests)
    - 5 Specialist Agents (domain experts)
    
    Agents use Azure AI Foundry's Agent-to-Agent (A2A) tool for coordination
    """
    
    def __init__(self):
        self.orchestrator: Optional[OrchestratorAgent] = None
        self.specialists = []
        self.initialized = False
    
    async def initialize(self):
        """Initialize all agents in the multi-agent system"""
        logger.info("="*80)
        logger.info("INITIALIZING MULTI-AGENT IT SERVICE DESK")
        logger.info("="*80)
        
        try:
            # Initialize specialist agents
            specialist_configs = []
            
            # Active Directory Agent
            if self._is_ad_configured():
                try:
                    ad_agent = ActiveDirectoryAgent()
                    await ad_agent.initialize()
                    self.specialists.append(ad_agent)
                    specialist_configs.append("✓ Active Directory Agent")
                except Exception as e:
                    logger.warning(f"AD Agent initialization failed: {e}")
            
            # Microsoft Graph Agent
            if self._is_graph_configured():
                try:
                    graph_agent = MicrosoftGraphAgent()
                    await graph_agent.initialize()
                    self.specialists.append(graph_agent)
                    specialist_configs.append("✓ Microsoft Graph Agent")
                except Exception as e:
                    logger.warning(f"Graph Agent initialization failed: {e}")
            
            # Intune Agent (requires Graph)
            if self._is_graph_configured():
                try:
                    intune_agent = IntuneAgent()
                    await intune_agent.initialize()
                    self.specialists.append(intune_agent)
                    specialist_configs.append("✓ Intune Agent")
                except Exception as e:
                    logger.warning(f"Intune Agent initialization failed: {e}")
            
            # ServiceNow Agent
            if self._is_servicenow_configured():
                try:
                    snow_agent = ServiceNowAgent()
                    await snow_agent.initialize()
                    self.specialists.append(snow_agent)
                    specialist_configs.append("✓ ServiceNow Agent")
                except Exception as e:
                    logger.warning(f"ServiceNow Agent initialization failed: {e}")
            
            # Knowledge Base Agent
            if self._is_search_configured():
                try:
                    kb_agent = KnowledgeBaseAgent()
                    await kb_agent.initialize()
                    self.specialists.append(kb_agent)
                    specialist_configs.append("✓ Knowledge Base Agent")
                except Exception as e:
                    logger.warning(f"Knowledge Base Agent initialization failed: {e}")
            
            if not self.specialists:
                raise RuntimeError(
                    "No specialist agents initialized! Check .env configuration.\n"
                    "At minimum, configure one of: AD, Graph, ServiceNow, or Azure AI Search"
                )
            
            # Initialize orchestrator with specialist connections
            self.orchestrator = OrchestratorAgent()
            await self.orchestrator.initialize(self.specialists)
            
            self.initialized = True
            
            logger.info("="*80)
            logger.info("MULTI-AGENT SYSTEM READY")
            logger.info("="*80)
            logger.info("Orchestrator: Tier 1 routing agent")
            for config in specialist_configs:
                logger.info(config)
            logger.info(f"Total agents: 1 orchestrator + {len(self.specialists)} specialists")
            logger.info("="*80)
            
        except Exception as e:
            logger.error(f"Failed to initialize multi-agent system: {e}", exc_info=True)
            raise
    
    async def run(self, query: str, thread_id: Optional[str] = None) -> str:
        """
        Process user query through multi-agent system
        
        Args:
            query: User's question or request
            thread_id: Optional thread ID for conversation continuity
            
        Returns:
            Final response from orchestrator
        """
        if not self.initialized:
            await self.initialize()
        
        return await self.orchestrator.process_request(query, thread_id)
    
    async def cleanup(self):
        """Clean up all agent resources"""
        logger.info("Cleaning up multi-agent system...")
        
        # Cleanup orchestrator
        if self.orchestrator:
            await self.orchestrator.cleanup()
        
        # Cleanup specialists
        for specialist in self.specialists:
            await specialist.cleanup()
        
        logger.info("✓ Multi-agent system cleaned up")
    
    # Configuration checks (same as monolithic agent)
    def _is_ad_configured(self) -> bool:
        return bool(settings.AD_DOMAIN and settings.AD_SERVER)
    
    def _is_graph_configured(self) -> bool:
        return bool(settings.GRAPH_TENANT_ID and settings.GRAPH_CLIENT_ID)
    
    def _is_servicenow_configured(self) -> bool:
        return bool(settings.SERVICENOW_INSTANCE and 
                   (settings.SERVICENOW_CLIENT_ID or settings.SERVICENOW_USERNAME))
    
    def _is_search_configured(self) -> bool:
        return bool(settings.AZURE_SEARCH_ENDPOINT and settings.AZURE_SEARCH_INDEX_NAME)


# Example usage
async def main():
    """Example usage of Multi-Agent IT Service Desk"""
    
    # Create multi-agent system
    service_desk = MultiAgentITServiceDesk()
    await service_desk.initialize()
    
    # Example queries demonstrating routing to different specialists
    queries = [
        # Simple greeting (orchestrator handles)
        "Hello, I need help with my account",
        
        # AD Agent
        "Reset password for user john.smith@atlasroofing.com",
        
        # Graph Agent  
        "Check if user sarah.jones has an Office 365 license",
        
        # Intune Agent
        "Check compliance status for laptop DESK-12345",
        
        # ServiceNow Agent
        "Create an incident for printer not working in conference room",
        
        # Knowledge Base Agent
        "How do I connect to the company VPN?",
        
        # Multi-agent workflow
        "New employee Mike Davis needs to be set up - create AD account, assign Office 365 license, and create onboarding ticket",
    ]
    
    print("\n" + "="*80)
    print("MULTI-AGENT IT SERVICE DESK - DEMO")
    print("="*80 + "\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {query}")
        print(f"{'='*80}")
        
        try:
            response = await service_desk.run(query)
            print(f"\nResponse:\n{response}")
        except Exception as e:
            print(f"\nError: {e}")
        
        print()
    
    # Cleanup
    await service_desk.cleanup()
    print("\n✓ Demo completed\n")


if __name__ == "__main__":
    asyncio.run(main())
