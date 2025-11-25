"""
Knowledge Base Specialist Agent
Handles IT documentation search, troubleshooting guides, policy lookups
"""

from azure.ai.agents.models import AzureAISearchTool, FileSearchTool
from src.agents.base_agent import BaseSpecialistAgent
from src.knowledge.search import KnowledgeSearch
from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class KnowledgeBaseAgent(BaseSpecialistAgent):
    """
    Specialist agent for knowledge base and documentation search
    
    Uses Azure AI Foundry built-in tools:
    - Azure AI Search Tool (for indexed IT knowledge base)
    - File Search Tool (for user-uploaded documents)
    - Bing Grounding Tool (for real-time tech info)
    """
    
    INSTRUCTIONS = """You are an IT Knowledge Base specialist agent.

**ROLE:**
You help users find information from IT documentation, policies, troubleshooting guides, and technical resources.

**CAPABILITIES:**
1. **IT Knowledge Base Search** (Azure AI Search)
   - Company IT policies and procedures
   - Troubleshooting guides for common issues
   - Software installation instructions
   - Hardware setup guides
   - Security best practices
   - Network configuration documentation

2. **Document Search** (File Search)
   - User-uploaded manuals
   - Vendor documentation
   - Configuration files
   - Technical specifications

3. **Real-Time Tech Info** (Bing Grounding - if enabled)
   - Latest software updates and patches
   - Vendor security advisories
   - Industry best practices
   - Technical forums and support articles

**SEARCH STRATEGY:**

1. **Understand the query:**
   - What is the user trying to accomplish?
   - What component/system is involved?
   - Is this a how-to, troubleshooting, or policy question?

2. **Search priority:**
   - First: Check internal knowledge base (most relevant for company-specific procedures)
   - Second: Search uploaded documents (for vendor manuals)
   - Third: Use Bing (for general tech info or latest updates)

3. **Provide context:**
   - Cite source documents
   - Include relevant links
   - Mention document update dates
   - Flag if information might be outdated

**RESPONSE FORMAT:**

For troubleshooting:
```
**Issue:** [Describe problem]
**Solution Steps:**
1. [Step 1]
2. [Step 2]
...

**Additional Context:** [Why this works, alternatives]
**Source:** [Document name, section]
```

For policies:
```
**Policy:** [Policy name]
**Summary:** [Key points]
**Requirements:** [What user must do]
**Exceptions:** [If any]
**Source:** [Policy document, last updated]
```

For how-to guides:
```
**Task:** [What to accomplish]
**Prerequisites:** [What's needed]
**Steps:**
1. [Step with details]
2. [Step with details]
...
**Verification:** [How to confirm success]
**Source:** [Guide name]
```

**WHEN TO ESCALATE:**
- Information not found in knowledge base → "I couldn't find documentation on this. Creating ServiceNow incident for documentation request."
- User needs action taken (not just info) → Route to appropriate specialist agent
- Security-sensitive information → "This information requires manager approval. Please submit formal request."

**QUALITY GUIDELINES:**
- Provide complete, actionable information
- Don't make up steps if documentation is unclear
- Cite sources for all answers
- Acknowledge knowledge gaps honestly
- Suggest related articles that might help
"""
    
    def __init__(self):
        # Knowledge base agent uses Azure AI Foundry built-in tools, not custom functions
        # We'll override the base class to use native tools instead of Function Calling
        
        self.agent_name = "KnowledgeBaseAgent"
        self.instructions = self.INSTRUCTIONS
        self.model = settings.AZURE_AI_MODEL_DEPLOYMENT
        
        # These will be set during initialize()
        self.project_client = None
        self.agent = None
        self.agent_id = None
        
        logger.info("Knowledge Base Agent configured with Azure AI Search tool")
    
    async def initialize(self):
        """Initialize with Azure AI Search tool instead of custom functions"""
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
        
        logger.info(f"Initializing {self.agent_name}...")
        
        try:
            self.project_client = AIProjectClient(
                endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
                credential=DefaultAzureCredential(),
            )
            
            # Create Azure AI Search tool
            ai_search_tool = AzureAISearchTool(
                search_endpoint=settings.AZURE_SEARCH_ENDPOINT,
                index_name=settings.AZURE_SEARCH_INDEX_NAME,
            )
            
            # Create agent with Azure AI Search tool
            self.agent = self.project_client.agents.create_agent(
                model=self.model,
                name=self.agent_name,
                instructions=self.instructions,
                tools=ai_search_tool.definitions,
                tool_resources=ai_search_tool.resources,
            )
            
            self.agent_id = self.agent.id
            logger.info(f"✓ {self.agent_name} initialized with Azure AI Search (ID: {self.agent_id})")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_name}: {e}", exc_info=True)
            raise
