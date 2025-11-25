"""
Multi-Agent IT Service Desk System - Micro-Agent Architecture
19-agent system: 1 orchestrator + 18 micro-agents + workflow coordinator
"""

import asyncio
from typing import Optional, Dict, List
from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class MicroAgentITServiceDesk:
    """
    Micro-Agent IT Service Desk system using Azure AI Foundry
    
    Architecture:
    - 1 Master Orchestrator (AI workflow engine)
    - 1 Workflow Coordinator (multi-step execution manager)
    - 18 Micro-Agents (ultra-focused specialists):
      * 6 Identity & Access agents
      * 4 Device Management agents
      * 3 Ticketing & Documentation agents
      * 3 Security & Credentials agents
      * 1 Technician Assistant agent
      * 1 Workflow execution agent (embedded in coordinator)
    
    Agents communicate via Azure AI Foundry's Agent-to-Agent (A2A) Tool
    """
    
    def __init__(self):
        self.orchestrator = None
        self.workflow_coordinator = None
        self.agents: Dict[str, any] = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize all 19 agents in the micro-agent system"""
        logger.info("=" * 80)
        logger.info("INITIALIZING MICRO-AGENT IT SERVICE DESK (19 AGENTS)")
        logger.info("=" * 80)
        
        try:
            initialized_agents = []
            
            # ===================================================================
            # IDENTITY & ACCESS MANAGEMENT (6 agents)
            # ===================================================================
            logger.info("\n🔐 Initializing Identity & Access Management agents...")
            
            if self._is_ad_configured():
                # 1. AD User Lookup Agent
                try:
                    from src.agents.identity import ADUserLookupAgent
                    agent = ADUserLookupAgent()
                    await agent.initialize()
                    self.agents["ADUserLookupAgent"] = agent
                    initialized_agents.append("✓ AD User Lookup Agent (read-only queries)")
                except Exception as e:
                    logger.warning(f"AD User Lookup Agent failed: {e}")
                
                # 2. AD Password Reset Agent
                try:
                    from src.agents.identity import ADPasswordResetAgent
                    agent = ADPasswordResetAgent()
                    await agent.initialize()
                    self.agents["ADPasswordResetAgent"] = agent
                    initialized_agents.append("✓ AD Password Reset Agent (password operations)")
                except Exception as e:
                    logger.warning(f"AD Password Reset Agent failed: {e}")
                
                # 3. AD Computer Management Agent
                try:
                    from src.agents.identity import ADComputerManagementAgent
                    agent = ADComputerManagementAgent()
                    await agent.initialize()
                    self.agents["ADComputerManagementAgent"] = agent
                    initialized_agents.append("✓ AD Computer Management Agent (computer accounts + LAPS)")
                except Exception as e:
                    logger.warning(f"AD Computer Management Agent failed: {e}")
            
            if self._is_graph_configured():
                # 4. Azure AD User Agent
                try:
                    from src.agents.identity import AzureADUserAgent
                    agent = AzureADUserAgent()
                    await agent.initialize()
                    self.agents["AzureADUserAgent"] = agent
                    initialized_agents.append("✓ Azure AD User Agent (cloud identity)")
                except Exception as e:
                    logger.warning(f"Azure AD User Agent failed: {e}")
                
                # 5. License Management Agent
                try:
                    from src.agents.identity import LicenseManagementAgent
                    agent = LicenseManagementAgent()
                    await agent.initialize()
                    self.agents["LicenseManagementAgent"] = agent
                    initialized_agents.append("✓ License Management Agent (Office 365 licenses)")
                except Exception as e:
                    logger.warning(f"License Management Agent failed: {e}")
                
                # 6. Group Membership Agent
                try:
                    from src.agents.identity import GroupMembershipAgent
                    agent = GroupMembershipAgent()
                    await agent.initialize()
                    self.agents["GroupMembershipAgent"] = agent
                    initialized_agents.append("✓ Group Membership Agent (AD/Azure AD groups)")
                except Exception as e:
                    logger.warning(f"Group Membership Agent failed: {e}")
            
            # ===================================================================
            # DEVICE MANAGEMENT (4 agents)
            # ===================================================================
            logger.info("\n💻 Initializing Device Management agents...")
            
            if self._is_graph_configured():
                # 7. Device Inventory Agent
                try:
                    from src.agents.device import DeviceInventoryAgent
                    agent = DeviceInventoryAgent()
                    await agent.initialize()
                    self.agents["DeviceInventoryAgent"] = agent
                    initialized_agents.append("✓ Device Inventory Agent (device info lookup)")
                except Exception as e:
                    logger.warning(f"Device Inventory Agent failed: {e}")
                
                # 8. Compliance Check Agent
                try:
                    from src.agents.device import ComplianceCheckAgent
                    agent = ComplianceCheckAgent()
                    await agent.initialize()
                    self.agents["ComplianceCheckAgent"] = agent
                    initialized_agents.append("✓ Compliance Check Agent (policy compliance)")
                except Exception as e:
                    logger.warning(f"Compliance Check Agent failed: {e}")
                
                # 9. Remote Actions Agent
                try:
                    from src.agents.device import RemoteActionsAgent
                    agent = RemoteActionsAgent()
                    await agent.initialize()
                    self.agents["RemoteActionsAgent"] = agent
                    initialized_agents.append("✓ Remote Actions Agent (lock/wipe/sync/restart)")
                except Exception as e:
                    logger.warning(f"Remote Actions Agent failed: {e}")
                
                # 10. App Deployment Agent
                try:
                    from src.agents.device import AppDeploymentAgent
                    agent = AppDeploymentAgent()
                    await agent.initialize()
                    self.agents["AppDeploymentAgent"] = agent
                    initialized_agents.append("✓ App Deployment Agent (app installation status)")
                except Exception as e:
                    logger.warning(f"App Deployment Agent failed: {e}")
            
            # ===================================================================
            # TICKETING & DOCUMENTATION (3 agents)
            # ===================================================================
            logger.info("\n🎫 Initializing Ticketing & Documentation agents...")
            
            if self._is_servicenow_configured():
                # 11. Incident Creation Agent
                try:
                    from src.agents.ticketing import IncidentCreationAgent
                    agent = IncidentCreationAgent()
                    await agent.initialize()
                    self.agents["IncidentCreationAgent"] = agent
                    initialized_agents.append("✓ Incident Creation Agent (create tickets)")
                except Exception as e:
                    logger.warning(f"Incident Creation Agent failed: {e}")
                
                # 12. Ticket Query Agent
                try:
                    from src.agents.ticketing import TicketQueryAgent
                    agent = TicketQueryAgent()
                    await agent.initialize()
                    self.agents["TicketQueryAgent"] = agent
                    initialized_agents.append("✓ Ticket Query Agent (search/update tickets)")
                except Exception as e:
                    logger.warning(f"Ticket Query Agent failed: {e}")
                
                # 13. Knowledge Base Search Agent
                try:
                    from src.agents.ticketing import KnowledgeBaseSearchAgent
                    agent = KnowledgeBaseSearchAgent()
                    await agent.initialize()
                    self.agents["KnowledgeBaseSearchAgent"] = agent
                    initialized_agents.append("✓ Knowledge Base Search Agent (KB articles)")
                except Exception as e:
                    logger.warning(f"Knowledge Base Search Agent failed: {e}")
            
            # ===================================================================
            # SECURITY & CREDENTIALS (3 agents)
            # ===================================================================
            logger.info("\n🔒 Initializing Security & Credentials agents...")
            
            if self._is_ad_configured():
                # 14. LAPS Retrieval Agent
                try:
                    from src.agents.security import LAPSRetrievalAgent
                    agent = LAPSRetrievalAgent()
                    await agent.initialize()
                    self.agents["LAPSRetrievalAgent"] = agent
                    initialized_agents.append("✓ LAPS Retrieval Agent (local admin passwords - SENSITIVE)")
                except Exception as e:
                    logger.warning(f"LAPS Retrieval Agent failed: {e}")
            
            if self._is_graph_configured():
                # 15. Bitlocker Recovery Agent
                try:
                    from src.agents.security import BitlockerRecoveryAgent
                    agent = BitlockerRecoveryAgent()
                    await agent.initialize()
                    self.agents["BitlockerRecoveryAgent"] = agent
                    initialized_agents.append("✓ Bitlocker Recovery Agent (recovery keys - SENSITIVE)")
                except Exception as e:
                    logger.warning(f"Bitlocker Recovery Agent failed: {e}")
                
                # 16. Sign-In Analysis Agent
                try:
                    from src.agents.security import SignInAnalysisAgent
                    agent = SignInAnalysisAgent()
                    await agent.initialize()
                    self.agents["SignInAnalysisAgent"] = agent
                    initialized_agents.append("✓ Sign-In Analysis Agent (authentication logs)")
                except Exception as e:
                    logger.warning(f"Sign-In Analysis Agent failed: {e}")
            
            # ===================================================================
            # TECHNICIAN SUPPORT (1 agent)
            # ===================================================================
            logger.info("\n👨‍💻 Initializing Technician Support agent...")
            
            if self._is_search_configured():
                # 17. Technician Assistant Agent
                try:
                    from src.agents.technician_assistant_agent import TechnicianAssistantAgent
                    agent = TechnicianAssistantAgent()
                    await agent.initialize()
                    self.agents["TechnicianAssistantAgent"] = agent
                    initialized_agents.append("✓ Technician Assistant Agent (troubleshooting guidance)")
                except Exception as e:
                    logger.warning(f"Technician Assistant Agent failed: {e}")
            
            # ===================================================================
            # VALIDATION
            # ===================================================================
            if not self.agents:
                raise RuntimeError(
                    "No micro-agents initialized! Check .env configuration.\n"
                    "At minimum, configure: AD (for identity) or Graph (for cloud) or ServiceNow (for ticketing)"
                )
            
            # ===================================================================
            # MASTER ORCHESTRATOR (AI Workflow Engine)
            # ===================================================================
            logger.info("\n🧠 Initializing Master Orchestrator...")
            
            # Build specialist connection map for A2A tools
            specialist_connections = {}
            for agent_name, agent in self.agents.items():
                try:
                    connection_id = agent.get_agent_connection_id()
                    specialist_connections[agent_name] = connection_id
                except Exception as e:
                    logger.warning(f"Could not get connection ID for {agent_name}: {e}")
            
            from src.agents.orchestration.master_orchestrator import MasterOrchestrator
            self.orchestrator = MasterOrchestrator(specialist_connections)
            await self.orchestrator.initialize()
            
            # ===================================================================
            # WORKFLOW COORDINATOR (Multi-Agent Execution Manager)
            # ===================================================================
            logger.info("\n⚙️  Initializing Workflow Coordinator...")
            
            from src.agents.orchestration.workflow_coordinator import WorkflowCoordinator
            self.workflow_coordinator = WorkflowCoordinator(self.orchestrator)
            
            self.initialized = True
            
            # ===================================================================
            # INITIALIZATION COMPLETE
            # ===================================================================
            logger.info("\n" + "=" * 80)
            logger.info("✓ MICRO-AGENT SYSTEM READY")
            logger.info("=" * 80)
            logger.info("🧠 Master Orchestrator: AI workflow engine")
            logger.info("⚙️  Workflow Coordinator: Multi-step execution manager")
            logger.info(f"\n📊 Agent Summary: {len(self.agents)} specialized micro-agents")
            logger.info("")
            for agent_info in initialized_agents:
                logger.info(f"  {agent_info}")
            logger.info("")
            logger.info(f"Total System: 1 orchestrator + {len(self.agents)} micro-agents + 1 coordinator = {len(self.agents) + 2} components")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Failed to initialize micro-agent system: {e}", exc_info=True)
            raise
    
    async def run(self, query: str, thread_id: Optional[str] = None) -> str:
        """
        Process user query through micro-agent system
        
        Args:
            query: User's question or request
            thread_id: Optional thread ID for conversation continuity
            
        Returns:
            Final response from orchestrator
        """
        if not self.initialized:
            await self.initialize()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"User Query: {query}")
        logger.info(f"{'='*80}")
        
        return await self.orchestrator.query(query)
    
    async def run_workflow(self, workflow_definition, confirmation_callback=None):
        """
        Execute a pre-defined workflow through workflow coordinator
        
        Args:
            workflow_definition: WorkflowDefinition object
            confirmation_callback: Optional callback for user confirmations
            
        Returns:
            Workflow execution results
        """
        if not self.initialized:
            await self.initialize()
        
        return await self.workflow_coordinator.execute_workflow(
            workflow_definition,
            confirmation_callback
        )
    
    async def cleanup(self):
        """Clean up all agent resources"""
        logger.info("\nCleaning up micro-agent system...")
        
        # Cleanup orchestrator
        if self.orchestrator:
            await self.orchestrator.cleanup()
        
        # Cleanup all micro-agents
        for agent_name, agent in self.agents.items():
            try:
                await agent.cleanup()
            except Exception as e:
                logger.warning(f"Failed to cleanup {agent_name}: {e}")
        
        logger.info("✓ Micro-agent system cleaned up")
    
    # Configuration checks
    def _is_ad_configured(self) -> bool:
        return bool(settings.AD_DOMAIN and settings.AD_SERVER)
    
    def _is_graph_configured(self) -> bool:
        return bool(settings.GRAPH_TENANT_ID and settings.GRAPH_CLIENT_ID)
    
    def _is_servicenow_configured(self) -> bool:
        return bool(settings.SERVICENOW_INSTANCE and 
                   (settings.SERVICENOW_CLIENT_ID or settings.SERVICENOW_USERNAME))
    
    def _is_search_configured(self) -> bool:
        return bool(settings.AZURE_SEARCH_ENDPOINT and settings.AZURE_SEARCH_INDEX_NAME)


# Example usage and demos
async def main():
    """Example usage of Micro-Agent IT Service Desk"""
    
    # Create micro-agent system
    service_desk = MicroAgentITServiceDesk()
    await service_desk.initialize()
    
    # Example queries demonstrating routing to specialized micro-agents
    queries = [
        # Identity queries → specific micro-agents
        "Check if user john.smith@atlasroofing.com exists",  # → ADUserLookupAgent
        "Reset password for jane.doe@atlasroofing.com",  # → ADPasswordResetAgent
        "What Office 365 licenses does sarah.jones have?",  # → LicenseManagementAgent
        
        # Device queries → device micro-agents
        "What devices does john.smith have?",  # → DeviceInventoryAgent
        "Check compliance for device DESK-12345",  # → ComplianceCheckAgent
        "Sync device LAPTOP-67890",  # → RemoteActionsAgent
        
        # Ticketing → ticketing micro-agents
        "Create ticket: Printer not working in conference room",  # → IncidentCreationAgent
        "Check status of ticket INC0012345",  # → TicketQueryAgent
        "How do I reset my password?",  # → KnowledgeBaseSearchAgent
        
        # Security (sensitive) → security micro-agents
        "Get LAPS password for computer DESK-12345",  # → LAPSRetrievalAgent (HIGH RISK)
        "Get Bitlocker key for device showing recovery screen",  # → BitlockerRecoveryAgent
        "Why can't user sign in?",  # → SignInAnalysisAgent
        
        # Complex multi-agent workflows
        "User can't access VPN - troubleshoot",  # → Multiple agents (groups, compliance, sign-in)
        "New employee setup for mike.davis@atlasroofing.com",  # → Workflow (license, groups, ticket)
    ]
    
    print("\n" + "="*80)
    print("MICRO-AGENT IT SERVICE DESK - DEMO")
    print("19-Agent Architecture: Ultra-specialized task-based agents")
    print("="*80 + "\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {query}")
        print(f"{'='*80}")
        
        try:
            response = await service_desk.run(query)
            print(f"\nOrchestrator Response:\n{response}")
        except Exception as e:
            print(f"\nError: {e}")
        
        # Add delay between queries to avoid rate limiting
        await asyncio.sleep(2)
    
    # Demo workflow execution
    print(f"\n{'='*80}")
    print("WORKFLOW DEMO: Password Reset & Verification")
    print(f"{'='*80}")
    
    from src.agents.orchestration.workflow_coordinator import WorkflowTemplates
    
    workflow = WorkflowTemplates.password_reset_and_verify("test.user@atlasroofing.com")
    
    # Mock confirmation callback
    async def mock_confirmation(prompt):
        print(f"\nConfirmation Required:\n{prompt}")
        print("Auto-confirming for demo: yes")
        return True
    
    try:
        result = await service_desk.run_workflow(workflow, mock_confirmation)
        print(f"\nWorkflow Result:\n{result}")
    except Exception as e:
        print(f"\nWorkflow Error: {e}")
    
    # Cleanup
    await service_desk.cleanup()
    print("\n✓ Demo completed\n")


if __name__ == "__main__":
    asyncio.run(main())
