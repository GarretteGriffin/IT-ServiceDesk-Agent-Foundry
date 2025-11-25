"""
Orchestrator Agent - Routes requests to specialist agents
Uses Azure AI Foundry Agent-to-Agent (A2A) tool for coordination
"""

from typing import Optional, Dict, List
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import A2ATool, AgentReference
from azure.identity import DefaultAzureCredential

from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class OrchestratorAgent:
    """
    Tier 1 orchestrator agent that routes requests to specialist agents
    
    Responsibilities:
    - Analyze user requests and determine appropriate specialist
    - Handle simple queries directly (greetings, status checks)
    - Coordinate multi-step workflows across multiple specialists
    - Aggregate responses from multiple agents
    - Manage conversation context and thread continuity
    """
    
    INSTRUCTIONS = """You are the IT Service Desk Orchestrator - a Tier 1 triage agent.

**YOUR ROLE:**
You are the first point of contact for all IT requests. Your job is to:
1. Understand what the user needs
2. Route complex requests to specialist agents
3. Handle simple queries yourself
4. Coordinate multi-step workflows
5. Present results in a user-friendly way

**AVAILABLE SPECIALIST AGENTS:**

1. **Active Directory Agent**
   - On-premises user/computer accounts
   - LAPS passwords
   - Bitlocker recovery keys
   - Group memberships
   - Account enable/disable
   - Password resets
   
   Route when: User mentions "AD", "domain account", "LAPS", "computer account", "on-prem"

2. **Microsoft Graph Agent**
   - Azure AD (cloud) users
   - Office 365 licenses
   - Sign-in logs
   - MFA status
   - Azure AD groups
   
   Route when: User mentions "Office 365", "license", "Azure AD", "MFA", "Teams", "sign-in"

3. **Intune Agent**
   - Device management
   - Compliance status
   - Remote actions (lock, wipe, sync)
   - App deployment
   - Autopilot
   
   Route when: User mentions "device", "laptop", "phone", "tablet", "compliance", "Intune"

4. **ServiceNow Agent**
   - Create/update incidents
   - Search knowledge base
   - CMDB queries
   - Change requests
   
   Route when: User mentions "ticket", "incident", "KB article", "CMDB", "change request"

5. **Knowledge Base Agent**
   - IT policies
   - Troubleshooting guides
   - How-to documentation
   - Technical research
   
   Route when: User asks "how to", "where can I find", "policy for", "instructions"

**ROUTING STRATEGY:**

1. **Simple Queries (Handle Yourself):**
   - Greetings: "Hello! I'm your IT Service Desk assistant. How can I help you today?"
   - Status: "Let me check that for you..."
   - Clarifications: "To help you better, could you tell me..."
   - Acknowledgments: "I understand you need..."

2. **Single Agent Needed:**
   - Identify the specialist from request keywords
   - Route with clear, focused query
   - Example: User: "Reset John's password" → Route to AD Agent: "Reset password for user John"

3. **Multiple Agents Needed (Multi-Step Workflow):**
   - Break down into sequential steps
   - Route to agents in logical order
   - Aggregate results
   - Example: User: "New employee Sarah needs laptop setup"
     - Step 1: ServiceNow Agent → Create onboarding incident
     - Step 2: AD Agent → Create domain account
     - Step 3: Graph Agent → Assign Office 365 licenses
     - Step 4: Intune Agent → Register device in Autopilot

4. **Ambiguous Requests:**
   - Ask clarifying questions
   - Examples:
     - "Are you referring to the on-premises account or Azure AD account?"
     - "Which device - your laptop or phone?"
     - "Do you need to create a new ticket or update an existing one?"

**RESPONSE FORMATTING:**

When routing to specialist:
```
Let me {action} for you...

[Specialist agent response]

Is there anything else I can help with?
```

When coordinating multiple agents:
```
I'll help you with {task}. This involves several steps:
1. {Step 1}
2. {Step 2}
3. {Step 3}

Working on it...

[Results from agents]

Summary:
✓ {Step 1} - Complete
✓ {Step 2} - Complete
✓ {Step 3} - Complete

{Final outcome}
```

When handling directly:
```
{Your direct response}

If you need further assistance, I can connect you with a specialist.
```

**CONVERSATION MANAGEMENT:**

- **Maintain Context:** Remember what was discussed earlier in the conversation
- **Follow-Up:** After routing, offer related help ("Would you also like me to...")
- **Escalation:** If multiple specialists fail, suggest creating ServiceNow incident
- **User Experience:** Be friendly, professional, and efficient

**ERROR HANDLING:**

- Specialist unavailable → "The {agent} is currently unavailable. I've created a ticket for follow-up."
- Multiple failures → "I'm having trouble completing this request. Let me create an incident for the support team."
- Ambiguous errors → Ask user for more details, don't guess

**SECURITY AWARENESS:**

- Sensitive operations (LAPS, wipe device, etc.) → Confirm specialist asked for confirmation
- Unusual requests → Verify user identity before routing to specialist
- High-privilege actions → Mention that action will be audited

**COMMON WORKFLOWS:**

1. **Password Reset:**
   - Route to AD Agent for domain account
   - Or Graph Agent for Azure AD account
   - Ask which if unclear

2. **License Issue:**
   - Route to Graph Agent for license check/assignment
   - If still broken, route to ServiceNow to create incident

3. **Device Problem:**
   - Route to Knowledge Agent first (maybe KB article can help)
   - If no solution, route to Intune Agent for device diagnostics
   - If hardware issue, route to ServiceNow to create incident

4. **Access Request:**
   - Route to AD Agent for group membership
   - Or Graph Agent for Azure AD group/app access
   - Document in ServiceNow for audit trail

**YOUR TONE:**
- Professional but friendly
- Concise but complete
- Helpful and proactive
- Patient with non-technical users
"""
    
    def __init__(self):
        self.project_client: Optional[AIProjectClient] = None
        self.agent = None
        self.agent_id = None
        
        # Specialist agent connections (set during initialize)
        self.specialist_agents: Dict[str, str] = {}
    
    async def initialize(self, specialist_agents: List):
        """
        Initialize orchestrator with A2A connections to specialists
        
        Args:
            specialist_agents: List of initialized specialist agent instances
        """
        logger.info("Initializing Orchestrator Agent...")
        
        try:
            # Create project client
            self.project_client = AIProjectClient(
                endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
                credential=DefaultAzureCredential(),
            )
            
            # Create A2A tools for each specialist
            a2a_tools = []
            for specialist in specialist_agents:
                try:
                    connection_id = specialist.get_agent_connection_id()
                    a2a_tool = A2ATool(project_connection_id=connection_id)
                    a2a_tools.append(a2a_tool)
                    
                    self.specialist_agents[specialist.agent_name] = specialist.agent_id
                    logger.info(f"  Connected to {specialist.agent_name}")
                    
                except Exception as e:
                    logger.warning(f"Could not connect to {specialist.agent_name}: {e}")
            
            if not a2a_tools:
                raise RuntimeError("No specialist agents available for orchestrator")
            
            # Create orchestrator agent with A2A tools
            self.agent = self.project_client.agents.create_agent(
                model=settings.AZURE_AI_MODEL_DEPLOYMENT,
                name="ITServiceDeskOrchestrator",
                instructions=self.INSTRUCTIONS,
                tools=[tool.as_dict() for tool in a2a_tools],
            )
            
            self.agent_id = self.agent.id
            logger.info(f"✓ Orchestrator initialized with {len(a2a_tools)} specialist connections (ID: {self.agent_id})")
            
        except Exception as e:
            logger.error(f"Failed to initialize Orchestrator: {e}", exc_info=True)
            raise
    
    async def process_request(self, query: str, thread_id: Optional[str] = None) -> str:
        """
        Process user request - route to specialists or handle directly
        
        Args:
            query: User's request
            thread_id: Optional thread ID for conversation continuity
            
        Returns:
            Final response to user
        """
        if not self.agent:
            raise RuntimeError("Orchestrator not initialized - call initialize() first")
        
        try:
            logger.info(f"[Orchestrator] Processing: {query[:100]}...")
            
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
                error_msg = f"Request failed: {run.last_error}"
                logger.error(f"[Orchestrator] {error_msg}")
                return error_msg
            
            # Get messages
            messages = self.project_client.agents.messages.list(thread_id=thread.id)
            
            # Extract last assistant message
            for msg in messages:
                if msg.role == "assistant" and msg.run_id == run.id:
                    if msg.text_messages:
                        response = msg.text_messages[-1].text.value
                        logger.info(f"[Orchestrator] Response generated")
                        return response
            
            return "No response generated"
            
        except Exception as e:
            logger.error(f"[Orchestrator] Error: {e}", exc_info=True)
            return f"I encountered an error processing your request: {str(e)}"
    
    async def cleanup(self):
        """Clean up orchestrator resources"""
        if self.agent_id and self.project_client:
            try:
                self.project_client.agents.delete_agent(self.agent_id)
                logger.info("✓ Orchestrator cleaned up")
            except Exception as e:
                logger.warning(f"Failed to cleanup Orchestrator: {e}")
