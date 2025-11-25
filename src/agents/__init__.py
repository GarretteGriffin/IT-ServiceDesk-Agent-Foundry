"""
Multi-Agent Architecture for IT Service Desk
Each agent specializes in a specific domain with focused tools and instructions
"""

from .orchestrator import OrchestratorAgent
from .ad_agent import ActiveDirectoryAgent
from .graph_agent import MicrosoftGraphAgent
from .intune_agent import IntuneAgent
from .servicenow_agent import ServiceNowAgent
from .knowledge_agent import KnowledgeBaseAgent

__all__ = [
    "OrchestratorAgent",
    "ActiveDirectoryAgent",
    "MicrosoftGraphAgent",
    "IntuneAgent",
    "ServiceNowAgent",
    "KnowledgeBaseAgent",
]
