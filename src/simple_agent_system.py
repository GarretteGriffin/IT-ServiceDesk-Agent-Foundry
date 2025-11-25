"""
Real Agent Implementation - No Architecture Astronautics
4 agents that actually work with real API calls
"""

from typing import List, Dict, Any, Optional
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Agent, AgentThread
from azure.identity import DefaultAzureCredential

from src.tools.active_directory import ADTool
from src.tools.microsoft_graph import GraphTool
from src.tools.servicenow import ServiceNowTool
from src.tools.intune import IntuneTool
from src.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ITServiceDesk:
    """
    Simple IT Service Desk with 4 real agents
    
    Agents:
    1. AD Agent - Active Directory operations via PowerShell
    2. Graph Agent - Microsoft Graph API (Azure AD, licenses, groups)
    3. ServiceNow Agent - Ticketing and ITSM
    4. Intune Agent - Device management via Graph API
    
    No orchestrator complexity. Simple routing based on keywords.
    """
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.project_client = AIProjectClient(
            endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
            credential=self.credential
        )
        
        # Initialize tools
        self.ad_tool = ADTool()
        self.graph_tool = GraphTool()
        self.servicenow_tool = ServiceNowTool()
        self.intune_tool = IntuneTool()
        
        # Agents (initialized on first use)
        self.ad_agent: Optional[Agent] = None
        self.graph_agent: Optional[Agent] = None
        self.servicenow_agent: Optional[Agent] = None
        self.intune_agent: Optional[Agent] = None
        
        logger.info("IT Service Desk initialized")
    
    async def initialize(self):
        """Create the 4 agents"""
        logger.info("Creating agents...")
        
        # AD Agent - On-premises Active Directory operations
        self.ad_agent = await self.project_client.agents.create_agent(
            model=settings.AZURE_AI_MODEL_DEPLOYMENT,
            name="Active Directory Agent",
            instructions="""You are an Active Directory specialist.
            
Use the provided tools to:
- Look up user information
- Reset passwords (ALWAYS confirm with user first)
- Unlock accounts
- Get computer information
- Retrieve LAPS passwords (HIGHLY SENSITIVE - require ticket number)
- Get BitLocker recovery keys (SENSITIVE - require justification)

Security:
- Password resets require confirmation
- LAPS requires a valid ServiceNow ticket number
- BitLocker requires justification
- Always log actions for audit

Response format:
- Be concise and technical
- Include relevant details (UPN, display name, status)
- If action requires approval, clearly state why""",
            tools=self.ad_tool.get_functions()
        )
        logger.info(f"Created AD Agent: {self.ad_agent.id}")
        
        # Graph Agent - Azure AD, Microsoft 365, licenses
        self.graph_agent = await self.project_client.agents.create_agent(
            model=settings.AZURE_AI_MODEL_DEPLOYMENT,
            name="Microsoft Graph Agent",
            instructions="""You are a Microsoft 365 and Azure AD specialist.

Use the provided tools to:
- Look up Azure AD user details
- Assign/remove licenses
- Check group memberships
- Add users to groups
- Query sign-in logs
- Check MFA status

Security:
- License changes require confirmation
- Group additions require confirmation for privileged groups
- Always verify user identity before making changes

Response format:
- Clear, structured information
- Show license SKUs in readable format (e.g., "Microsoft 365 E3" not "SPE_E3")
- Include relevant context""",
            tools=self.graph_tool.get_functions()
        )
        logger.info(f"Created Graph Agent: {self.graph_agent.id}")
        
        # ServiceNow Agent - Ticketing and ITSM
        self.servicenow_agent = await self.project_client.agents.create_agent(
            model=settings.AZURE_AI_MODEL_DEPLOYMENT,
            name="ServiceNow Agent",
            instructions="""You are a ServiceNow ITSM specialist.

Use the provided tools to:
- Search for incidents
- Create new incidents
- Update incident status
- Resolve incidents
- Search knowledge base
- Look up configuration items

Best practices:
- Clear, descriptive incident titles
- Include all relevant details in description
- Set correct priority based on impact
- Search KB before creating tickets (self-service)
- Always provide incident number after creation

Response format:
- Show incident numbers prominently
- Include current state and assigned person
- Suggest KB articles when relevant""",
            tools=self.servicenow_tool.get_functions()
        )
        logger.info(f"Created ServiceNow Agent: {self.servicenow_agent.id}")
        
        # Intune Agent - Device management
        self.intune_agent = await self.project_client.agents.create_agent(
            model=settings.AZURE_AI_MODEL_DEPLOYMENT,
            name="Intune Device Management Agent",
            instructions="""You are an Intune device management specialist.

Use the provided tools to:
- Look up device information
- Check compliance status
- Sync devices
- Restart devices (requires confirmation)
- Wipe devices (CRITICAL - requires explicit confirmation)
- Check installed applications

Security:
- Device sync is safe
- Restart requires confirmation
- Wipe is DESTRUCTIVE - requires explicit user confirmation with full device details

Response format:
- Clear device identification (name, serial number, user)
- Compliance status prominently displayed
- For actions, confirm what will happen""",
            tools=self.intune_tool.get_functions()
        )
        logger.info(f"Created Intune Agent: {self.intune_agent.id}")
        
        logger.info("All agents created successfully")
    
    async def query(self, user_query: str) -> str:
        """
        Route query to appropriate agent based on simple keyword matching
        No fancy orchestration - just direct routing
        """
        logger.info(f"Processing query: {user_query}")
        
        query_lower = user_query.lower()
        
        # Simple keyword-based routing
        agent = None
        agent_name = ""
        
        # AD keywords
        if any(kw in query_lower for kw in ['password', 'unlock', 'laps', 'bitlocker', 'computer account', 'ad user']):
            agent = self.ad_agent
            agent_name = "Active Directory"
        
        # Graph keywords
        elif any(kw in query_lower for kw in ['license', 'azure ad', 'entra', 'group member', 'sign-in', 'mfa']):
            agent = self.graph_agent
            agent_name = "Microsoft Graph"
        
        # ServiceNow keywords
        elif any(kw in query_lower for kw in ['ticket', 'incident', 'servicenow', 'knowledge base', 'kb article']):
            agent = self.servicenow_agent
            agent_name = "ServiceNow"
        
        # Intune keywords
        elif any(kw in query_lower for kw in ['device', 'intune', 'compliance', 'wipe', 'sync', 'restart', 'mobile']):
            agent = self.intune_agent
            agent_name = "Intune"
        
        # Default to Graph for user lookups
        else:
            agent = self.graph_agent
            agent_name = "Microsoft Graph (default)"
        
        if not agent:
            return "Error: No agents initialized. Call initialize() first."
        
        logger.info(f"Routing to {agent_name} agent")
        
        try:
            # Create thread and run
            thread = await self.project_client.agents.create_thread()
            await self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=user_query
            )
            
            run = await self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            # Get response
            messages = await self.project_client.agents.list_messages(thread_id=thread.id)
            response = messages.data[0].content[0].text.value if messages.data else "No response"
            
            # Clean up
            await self.project_client.agents.delete_thread(thread.id)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error: {str(e)}"
    
    async def cleanup(self):
        """Delete agents"""
        logger.info("Cleaning up agents...")
        
        for agent in [self.ad_agent, self.graph_agent, self.servicenow_agent, self.intune_agent]:
            if agent:
                try:
                    await self.project_client.agents.delete_agent(agent.id)
                    logger.info(f"Deleted agent: {agent.id}")
                except Exception as e:
                    logger.error(f"Error deleting agent: {e}")
        
        logger.info("Cleanup complete")


async def main():
    """Test the real service desk"""
    service_desk = ITServiceDesk()
    await service_desk.initialize()
    
    try:
        # Test queries
        queries = [
            "Look up user john.smith@atlasroofing.com",
            "Reset password for jane.doe@atlasroofing.com",
            "What licenses does john.smith have?",
            "Create an incident for printer not working",
            "Check compliance for device LAPTOP-12345",
        ]
        
        for query in queries:
            print(f"\n{'='*80}")
            print(f"Query: {query}")
            print(f"{'='*80}")
            response = await service_desk.query(query)
            print(response)
    
    finally:
        await service_desk.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
