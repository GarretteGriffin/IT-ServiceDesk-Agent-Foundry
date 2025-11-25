"""
Base specialist agent class with common functionality
"""

import os
from typing import List, Optional
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import FunctionTool, ToolSet

from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class BaseSpecialistAgent:
    """
    Base class for specialist agents in multi-agent architecture
    
    Each specialist agent:
    - Focuses on a specific domain (AD, Graph, Intune, etc.)
    - Uses Azure AI Foundry Function Calling for custom operations
    - Includes audit logging and input validation
    - Returns structured responses to orchestrator
    """
    
    def __init__(
        self,
        agent_name: str,
        instructions: str,
        functions: List[callable],
        model: str = None
    ):
        self.agent_name = agent_name
        self.instructions = instructions
        self.functions = functions
        self.model = model or settings.AZURE_AI_MODEL_DEPLOYMENT
        
        self.project_client: Optional[AIProjectClient] = None
        self.agent = None
        self.agent_id = None
        
    async def initialize(self):
        """Initialize the specialist agent with Azure AI Foundry"""
        logger.info(f"Initializing {self.agent_name}...")
        
        try:
            # Create project client
            self.project_client = AIProjectClient(
                endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
                credential=DefaultAzureCredential(),
            )
            
            # Create function tool from user functions
            function_tool = FunctionTool(functions=set(self.functions))
            toolset = ToolSet()
            toolset.add(function_tool)
            
            # Create agent
            self.agent = self.project_client.agents.create_agent(
                model=self.model,
                name=self.agent_name,
                instructions=self.instructions,
                toolset=toolset,
            )
            
            self.agent_id = self.agent.id
            logger.info(f"✓ {self.agent_name} initialized (ID: {self.agent_id})")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_name}: {e}", exc_info=True)
            raise
    
    async def process_request(self, query: str, thread_id: Optional[str] = None) -> str:
        """
        Process a request from the orchestrator
        
        Args:
            query: User's request specific to this agent's domain
            thread_id: Optional thread ID for conversation continuity
            
        Returns:
            Agent's response
        """
        if not self.agent:
            await self.initialize()
        
        try:
            logger.info(f"[{self.agent_name}] Processing: {query[:100]}...")
            
            # Create or get thread
            if thread_id:
                thread = self.project_client.agents.threads.retrieve(thread_id)
            else:
                thread = self.project_client.agents.threads.create()
            
            # Create message
            message = self.project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=query,
            )
            
            # Create and process run
            run = self.project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=self.agent_id,
            )
            
            # Check run status
            if run.status == "failed":
                error_msg = f"Run failed: {run.last_error}"
                logger.error(f"[{self.agent_name}] {error_msg}")
                return error_msg
            
            # Get messages
            messages = self.project_client.agents.messages.list(thread_id=thread.id)
            
            # Extract last assistant message
            for msg in messages:
                if msg.role == "assistant" and msg.run_id == run.id:
                    if msg.text_messages:
                        response = msg.text_messages[-1].text.value
                        logger.info(f"[{self.agent_name}] Response generated")
                        return response
            
            return "No response generated"
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error: {e}", exc_info=True)
            return f"Error processing request: {str(e)}"
    
    async def cleanup(self):
        """Clean up agent resources"""
        if self.agent_id and self.project_client:
            try:
                self.project_client.agents.delete_agent(self.agent_id)
                logger.info(f"✓ {self.agent_name} cleaned up")
            except Exception as e:
                logger.warning(f"Failed to cleanup {self.agent_name}: {e}")
    
    def get_agent_connection_id(self) -> str:
        """
        Get the connection ID for A2A tool integration
        Returns the agent's resource ID for orchestrator routing
        """
        if not self.agent_id:
            raise RuntimeError(f"{self.agent_name} not initialized - call initialize() first")
        
        # Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.MachineLearningServices/workspaces/{project}/agents/{agent_id}
        return (
            f"/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
            f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"
            f"/providers/Microsoft.MachineLearningServices/workspaces/{settings.AZURE_AI_PROJECT_NAME}"
            f"/agents/{self.agent_id}"
        )
