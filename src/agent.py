"""
IT Service Desk Agent - Azure AI Foundry Implementation
Main agent class with custom tools for enterprise IT operations
"""

import asyncio
import os
from typing import Any, AsyncGenerator, Optional

from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

from src.tools.active_directory import ADTool
from src.tools.powershell import PowerShellTool
from src.tools.servicenow import ServiceNowTool
from src.tools.microsoft_graph import GraphTool
from src.tools.intune import IntuneTool
from src.knowledge.search import KnowledgeSearch
from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class ITServiceDeskAgent:
    """
    Enterprise IT Service Desk Agent powered by Azure AI Foundry
    
    Features:
    - Active Directory management (users, computers, LAPS, Bitlocker)
    - PowerShell script execution (Exchange, networking, file servers)
    - ServiceNow integration (incidents, requests, KB)
    - Microsoft Graph (Azure AD, Intune, licensing)
    - Knowledge grounding with Azure AI Search (RAG)
    """
    
    def __init__(self):
        self.agent: Optional[ChatAgent] = None
        self.tools = []
        self._setup_tools()
        
    def _setup_tools(self):
        """Initialize tools based on available configuration - fail gracefully if credentials missing"""
        logger.info("Initializing IT Service Desk tools...")
        
        self.available_capabilities = []
        
        # Active Directory tool - only if configured
        if self._is_ad_configured():
            try:
                self.ad_tool = ADTool()
                self.tools.extend(self.ad_tool.get_functions())
                self.available_capabilities.append("Active Directory management")
                logger.info("✓ Active Directory tool enabled")
            except Exception as e:
                logger.warning(f"Active Directory tool disabled: {e}")
        
        # PowerShell execution tool - only if Azure Automation configured
        if self._is_automation_configured():
            try:
                self.ps_tool = PowerShellTool()
                self.tools.extend(self.ps_tool.get_functions())
                self.available_capabilities.append("PowerShell execution")
                logger.info("✓ PowerShell tool enabled")
            except Exception as e:
                logger.warning(f"PowerShell tool disabled: {e}")
        
        # ServiceNow tool - only if credentials exist
        if self._is_servicenow_configured():
            try:
                self.snow_tool = ServiceNowTool()
                self.tools.extend(self.snow_tool.get_functions())
                self.available_capabilities.append("ServiceNow ITSM operations")
                logger.info("✓ ServiceNow tool enabled")
            except Exception as e:
                logger.warning(f"ServiceNow tool disabled: {e}")
        
        # Microsoft Graph tool - only if credentials exist
        if self._is_graph_configured():
            try:
                self.graph_tool = GraphTool()
                self.tools.extend(self.graph_tool.get_functions())
                self.available_capabilities.append("Microsoft Graph (Azure AD, licensing)")
                logger.info("✓ Microsoft Graph tool enabled")
            except Exception as e:
                logger.warning(f"Microsoft Graph tool disabled: {e}")
        
        # Intune tool - requires Graph
        if self._is_graph_configured():
            try:
                self.intune_tool = IntuneTool()
                self.tools.extend(self.intune_tool.get_functions())
                self.available_capabilities.append("Intune device management")
                logger.info("✓ Intune tool enabled")
            except Exception as e:
                logger.warning(f"Intune tool disabled: {e}")
        
        # Knowledge search (RAG) - only if AI Search configured
        if self._is_search_configured():
            try:
                self.knowledge = KnowledgeSearch()
                self.tools.extend(self.knowledge.get_functions())
                self.available_capabilities.append("Knowledge base search (RAG)")
                logger.info("✓ Knowledge Search tool enabled")
            except Exception as e:
                logger.warning(f"Knowledge Search tool disabled: {e}")
        
        if not self.tools:
            logger.error("CRITICAL: No tools initialized! Check .env configuration.")
            raise RuntimeError("No tools available - agent cannot function without at least one tool configured")
        
        logger.info(f"Initialized {len(self.tools)} functions across {len(self.available_capabilities)} capabilities")
    
    def _is_ad_configured(self) -> bool:
        """Check if Active Directory credentials are configured"""
        return bool(settings.AD_DOMAIN and settings.AD_SERVER)
    
    def _is_automation_configured(self) -> bool:
        """Check if Azure Automation is configured for PowerShell execution"""
        return bool(settings.AZURE_AUTOMATION_ACCOUNT_NAME and settings.AZURE_AUTOMATION_RESOURCE_GROUP)
    
    def _is_servicenow_configured(self) -> bool:
        """Check if ServiceNow credentials are configured"""
        return bool(settings.SERVICENOW_INSTANCE and 
                   (settings.SERVICENOW_CLIENT_ID or settings.SERVICENOW_USERNAME))
    
    def _is_graph_configured(self) -> bool:
        """Check if Microsoft Graph credentials are configured"""
        return bool(settings.GRAPH_TENANT_ID and settings.GRAPH_CLIENT_ID)
    
    def _is_search_configured(self) -> bool:
        """Check if Azure AI Search is configured"""
        return bool(settings.AZURE_AI_SEARCH_ENDPOINT and settings.AZURE_AI_SEARCH_INDEX_NAME)
    
    async def initialize(self):
        """Initialize the agent with Azure AI Foundry"""
        logger.info("Initializing Azure AI Foundry agent...")
        
        try:
            # Load agent instructions
            instructions = self._load_instructions()
            
            # Create Azure AI Agent Client
            chat_client = AzureAIAgentClient(
                project_endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
                model_deployment_name=settings.AZURE_AI_MODEL_DEPLOYMENT,
                async_credential=DefaultAzureCredential(),
                agent_name=settings.AGENT_NAME,
            )
            
            # Create ChatAgent with tools
            self.agent = ChatAgent(
                chat_client=chat_client,
                instructions=instructions,
                tools=self.tools,
                temperature=settings.DEFAULT_TEMPERATURE,
            )
            
            logger.info("Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}", exc_info=True)
            raise
    
    def _load_instructions(self) -> str:
        """Load agent system instructions dynamically based on available capabilities"""
        instructions_path = settings.AGENT_INSTRUCTIONS_FILE
        
        if os.path.exists(instructions_path):
            with open(instructions_path, 'r') as f:
                base_instructions = f.read()
        else:
            base_instructions = """You are an IT Service Desk Agent that assists with enterprise IT operations.

**CRITICAL CONSTRAINTS:**
- You can ONLY perform operations using the tools explicitly provided to you
- If a tool is not available, you MUST tell the user that capability is not configured
- NEVER claim you can do something without using an available tool function
- ALWAYS verify the tool exists before telling a user you can help with a request"""
        
        # Append dynamic capability list
        capability_section = "\n\n**AVAILABLE CAPABILITIES (tools configured for this deployment):**\n"
        if self.available_capabilities:
            for cap in self.available_capabilities:
                capability_section += f"- {cap}\n"
        else:
            capability_section += "- NONE - agent is not fully configured\n"
        
        capability_section += "\n**If a user requests something not in the above list, respond:**\n"
        capability_section += "'That capability is not configured in this deployment. Available tools: [list above capabilities]'\n"
        
        capability_section += "\n**SECURITY GUIDELINES:**\n"
        capability_section += "- NEVER execute sensitive operations (password resets, LAPS retrieval, device wipes) without explicit user confirmation\n"
        capability_section += "- For sensitive operations, state: 'This operation [describe risk]. Confirm: yes/no?'\n"
        capability_section += "- All sensitive operations are audited - include justification\n"
        capability_section += "- Read-only queries (get info, search) are safe and do not require confirmation\n"
        
        return base_instructions + capability_section
    
    async def run(self, query: str, thread_id: Optional[str] = None) -> str:
        """
        Run agent with a user query
        
        Args:
            query: User's question or request
            thread_id: Optional thread ID for conversation continuity
            
        Returns:
            Agent's response
        """
        if not self.agent:
            await self.initialize()
        
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Get or create thread
            thread = None
            if thread_id:
                # In production, load thread from database
                thread = self.agent.get_thread(thread_id)
            else:
                thread = self.agent.get_new_thread()
            
            # Run agent
            result = await self.agent.run(query, thread=thread)
            
            logger.info(f"Agent response generated (thread: {thread.id})")
            
            return result.text
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return f"I encountered an error processing your request: {str(e)}"
    
    async def run_stream(self, query: str, thread_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Run agent with streaming response
        
        Args:
            query: User's question or request
            thread_id: Optional thread ID for conversation continuity
            
        Yields:
            Agent response chunks
        """
        if not self.agent:
            await self.initialize()
        
        try:
            logger.info(f"Processing query (streaming): {query[:100]}...")
            
            # Get or create thread
            thread = None
            if thread_id:
                thread = self.agent.get_thread(thread_id)
            else:
                thread = self.agent.get_new_thread()
            
            # Stream agent response
            async for chunk in self.agent.run_stream(query, thread=thread):
                if chunk.text:
                    yield chunk.text
            
            logger.info(f"Agent streaming completed (thread: {thread.id})")
            
        except Exception as e:
            logger.error(f"Error in streaming query: {e}", exc_info=True)
            yield f"Error: {str(e)}"
    
    async def close(self):
        """Clean up resources"""
        if self.agent:
            await self.agent.__aexit__(None, None, None)
        logger.info("Agent closed")


# Example usage
async def main():
    """Example usage of IT Service Desk Agent"""
    agent = ITServiceDeskAgent()
    await agent.initialize()
    
    # Example queries
    queries = [
        "What's the LAPS password for computer DESKTOP-001?",
        "Reset password for user jsmith@atlasroofing.com",
        "Check if server SERVER01 is online and get its IP address",
        "Search ServiceNow for solutions about VPN connection issues",
        "Get license information for user jdoe@atlasroofing.com",
    ]
    
    for query in queries:
        print(f"\n{'='*80}")
        print(f"User: {query}")
        print(f"{'='*80}")
        print("Agent: ", end="", flush=True)
        
        async for chunk in agent.run_stream(query):
            print(chunk, end="", flush=True)
        
        print("\n")
    
    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
