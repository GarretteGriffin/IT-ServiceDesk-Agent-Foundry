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
        """Initialize all custom tools"""
        logger.info("Initializing IT Service Desk tools...")
        
        # Active Directory tool
        self.ad_tool = ADTool()
        self.tools.extend(self.ad_tool.get_functions())
        
        # PowerShell execution tool
        self.ps_tool = PowerShellTool()
        self.tools.extend(self.ps_tool.get_functions())
        
        # ServiceNow tool
        self.snow_tool = ServiceNowTool()
        self.tools.extend(self.snow_tool.get_functions())
        
        # Microsoft Graph tool
        self.graph_tool = GraphTool()
        self.tools.extend(self.graph_tool.get_functions())
        
        # Intune tool
        self.intune_tool = IntuneTool()
        self.tools.extend(self.intune_tool.get_functions())
        
        # Knowledge search (RAG)
        self.knowledge = KnowledgeSearch()
        self.tools.extend(self.knowledge.get_functions())
        
        logger.info(f"Initialized {len(self.tools)} tools for agent")
    
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
        """Load agent system instructions from file"""
        instructions_path = settings.AGENT_INSTRUCTIONS_FILE
        
        if os.path.exists(instructions_path):
            with open(instructions_path, 'r') as f:
                return f.read()
        
        # Default instructions if file not found
        return """
You are an enterprise IT Service Desk Agent specializing in comprehensive IT operations.

**Capabilities:**
1. **Identity & Access Management**
   - Active Directory user and computer management
   - Azure AD/Entra ID operations
   - Password resets, account unlocks
   - LAPS password retrieval
   - Bitlocker recovery keys
   - License management

2. **Endpoint Management**
   - Microsoft Intune device operations
   - Device enrollment and compliance
   - Remote diagnostics
   - Software deployment

3. **PowerShell Automation**
   - Exchange Online operations
   - Network diagnostics
   - File server management
   - Custom script execution

4. **ServiceNow Integration**
   - Incident and request management
   - Knowledge base search
   - CMDB queries
   - Ticket creation and updates

5. **Security Operations**
   - Security incident response
   - Compliance checks
   - Access reviews

**Guidelines:**
- Always verify user permissions before executing sensitive operations
- Use knowledge search to find solutions from past tickets and documentation
- Create ServiceNow incidents for all significant actions
- Provide clear, step-by-step instructions
- Escalate complex issues appropriately
- Follow security best practices
- Log all operations for audit compliance

**Response Format:**
- Be concise and technical (audience is IT professionals)
- Include command examples when relevant
- Provide ticket numbers for tracking
- Mention any prerequisites or dependencies
- Highlight security considerations
"""
    
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
