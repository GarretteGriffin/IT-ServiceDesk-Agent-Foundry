"""
Knowledge Search with RAG (Retrieval-Augmented Generation)
Azure AI Search integration for intelligent knowledge grounding
"""

from typing import Annotated, List, Dict, Any, Optional
import asyncio
from datetime import datetime

from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class KnowledgeSearch:
    """
    Knowledge base search with Azure AI Search
    
    Capabilities:
    - Semantic search across multiple knowledge sources
    - Document indexing and management
    - Hybrid search (keyword + vector)
    - Source citation and relevance scoring
    - Multi-source integration (ServiceNow KB, SharePoint, internal docs)
    """
    
    def __init__(self):
        self.search_endpoint = settings.AZURE_AI_SEARCH_ENDPOINT
        self.index_name = settings.AZURE_AI_SEARCH_INDEX_NAME
        logger.info(f"Initialized Knowledge Search with index: {self.index_name}")
    
    def get_functions(self) -> List[callable]:
        """Return list of tool functions for agent"""
        return [
            self.search_knowledge,
            self.search_by_topic,
            self.find_similar_issues,
            self.get_document,
        ]
    
    async def search_knowledge(
        self,
        query: Annotated[str, "Search query for knowledge articles"],
        sources: Annotated[Optional[List[str]], "Filter by sources: servicenow, sharepoint, confluence, internal"] = None,
        max_results: Annotated[int, "Maximum results to return"] = 5,
    ) -> str:
        """
        Search knowledge base with semantic understanding.
        
        Returns relevant articles with excerpts, sources, and confidence scores.
        """
        logger.info(f"Searching knowledge base: {query}")
        
        try:
            # Build search parameters
            search_params = {
                "search": query,
                "queryType": "semantic",
                "semanticConfiguration": "default",
                "top": max_results,
                "select": "title,content,source,url,created,confidence",
            }
            
            # Add source filter
            if sources:
                filter_parts = [f"source eq '{source}'" for source in sources]
                search_params["filter"] = " or ".join(filter_parts)
            
            # Execute search
            results = await self._search_call(search_params)
            
            if not results:
                return f"No knowledge articles found for: {query}"
            
            output = [f"Knowledge Base Search Results ({len(results)}):\n"]
            
            for i, result in enumerate(results, 1):
                # Extract content excerpt
                content = result.get("content", "")
                excerpt = content[:300] + "..." if len(content) > 300 else content
                
                # Confidence score
                confidence = result.get("@search.score", 0)
                confidence_bar = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
                
                output.append(
                    f"{i}. {result['title']}\n"
                    f"   Source: {result.get('source', 'Unknown')} {confidence_bar}\n"
                    f"   {excerpt}\n"
                    f"   URL: {result.get('url', 'N/A')}\n"
                )
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return f"Failed to search knowledge base: {str(e)}"
    
    async def search_by_topic(
        self,
        topic: Annotated[str, "Topic category: password_reset, software_install, network_issue, email_problem, hardware_failure"],
        limit: Annotated[int, "Maximum results"] = 5,
    ) -> str:
        """Search for knowledge articles by predefined topic category."""
        logger.info(f"Searching by topic: {topic}")
        
        try:
            # Map topics to search queries
            topic_queries = {
                "password_reset": "password reset unlock account credentials",
                "software_install": "software installation deployment application",
                "network_issue": "network connectivity VPN wifi ethernet",
                "email_problem": "email outlook exchange mailbox",
                "hardware_failure": "hardware device broken repair replacement",
            }
            
            query = topic_queries.get(topic, topic)
            
            search_params = {
                "search": query,
                "queryType": "semantic",
                "semanticConfiguration": "default",
                "top": limit,
                "select": "title,content,source,url,viewCount,helpfulCount",
                "orderby": "helpfulCount desc",
            }
            
            results = await self._search_call(search_params)
            
            if not results:
                return f"No articles found for topic: {topic}"
            
            output = [f"Knowledge Articles for '{topic}' ({len(results)}):\n"]
            
            for i, result in enumerate(results, 1):
                helpful_count = result.get("helpfulCount", 0)
                view_count = result.get("viewCount", 0)
                
                output.append(
                    f"{i}. {result['title']}\n"
                    f"   👍 {helpful_count} helpful | 👁 {view_count} views\n"
                    f"   Source: {result.get('source', 'Unknown')}\n"
                    f"   URL: {result.get('url', 'N/A')}\n"
                )
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error searching by topic: {e}")
            return f"Failed to search by topic: {str(e)}"
    
    async def find_similar_issues(
        self,
        description: Annotated[str, "Issue description to find similar cases"],
        max_results: Annotated[int, "Maximum similar cases to return"] = 5,
    ) -> str:
        """
        Find similar resolved issues using vector similarity search.
        
        Helps identify solutions from past incidents with similar symptoms.
        """
        logger.info(f"Finding similar issues: {description}")
        
        try:
            # Use vector search for semantic similarity
            search_params = {
                "search": description,
                "queryType": "semantic",
                "semanticConfiguration": "default",
                "top": max_results,
                "select": "title,content,resolution,source,resolvedDate,similarity",
                "filter": "status eq 'resolved'",
            }
            
            results = await self._search_call(search_params)
            
            if not results:
                return f"No similar resolved issues found"
            
            output = [f"Similar Resolved Issues ({len(results)}):\n"]
            
            for i, result in enumerate(results, 1):
                resolution = result.get("resolution", "")
                resolution_excerpt = resolution[:200] + "..." if len(resolution) > 200 else resolution
                
                similarity = result.get("@search.score", 0)
                similarity_pct = int(similarity * 100)
                
                output.append(
                    f"{i}. {result['title']} ({similarity_pct}% similar)\n"
                    f"   Resolution: {resolution_excerpt}\n"
                    f"   Resolved: {result.get('resolvedDate', 'Unknown')}\n"
                    f"   Source: {result.get('source', 'Unknown')}\n"
                )
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error finding similar issues: {e}")
            return f"Failed to find similar issues: {str(e)}"
    
    async def get_document(
        self,
        document_id: Annotated[str, "Document ID or URL"],
    ) -> str:
        """Get full content of a specific knowledge document."""
        logger.info(f"Getting document: {document_id}")
        
        try:
            # Search by document ID or URL
            search_params = {
                "search": f'id:"{document_id}" OR url:"{document_id}"',
                "queryType": "full",
                "top": 1,
                "select": "title,content,source,url,created,updated,author",
            }
            
            results = await self._search_call(search_params)
            
            if not results:
                return f"Document not found: {document_id}"
            
            doc = results[0]
            
            output = [
                f"📄 {doc['title']}",
                f"\nMetadata:",
                f"  Source: {doc.get('source', 'Unknown')}",
                f"  Author: {doc.get('author', 'Unknown')}",
                f"  Created: {doc.get('created', 'Unknown')}",
                f"  Updated: {doc.get('updated', 'Unknown')}",
                f"  URL: {doc.get('url', 'N/A')}",
                f"\nContent:",
                f"{doc.get('content', 'No content available')}",
            ]
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return f"Failed to get document: {str(e)}"
    
    async def _search_call(self, params: Dict[str, Any]) -> List[Dict]:
        """
        Execute Azure AI Search query
        
        In production:
        1. Use azure-search-documents SDK
        2. Implement semantic ranking
        3. Vector search with embeddings
        4. Hybrid search (keyword + vector)
        5. Faceted search and filters
        6. Result highlighting
        7. Query spell correction
        8. Caching for common queries
        """
        # Placeholder - in production use actual Azure AI Search
        await asyncio.sleep(0.1)
        
        # Simulate search results
        query = params.get("search", "")
        
        return [
            {
                "id": "doc1",
                "title": "How to Reset User Password in Active Directory",
                "content": "To reset a user password in Active Directory, follow these steps: 1. Open Active Directory Users and Computers. 2. Navigate to the user account. 3. Right-click and select 'Reset Password'. 4. Enter the new password and confirm. 5. Optionally check 'User must change password at next logon'.",
                "source": "servicenow",
                "url": "https://kb.company.com/KB0012345",
                "created": "2025-01-15",
                "updated": "2025-11-01",
                "author": "IT Support Team",
                "@search.score": 0.92,
                "viewCount": 1543,
                "helpfulCount": 287,
                "status": "resolved",
                "resolution": "User password was successfully reset using the standard AD procedure.",
                "resolvedDate": "2025-11-20",
            },
            {
                "id": "doc2",
                "title": "Troubleshooting Account Lockouts",
                "content": "When a user account is locked out, first identify the source of invalid login attempts. Check the Domain Controller security logs for Event ID 4740. Unlock the account using 'Unlock-ADAccount' PowerShell cmdlet or Active Directory Users and Computers. Investigate if the lockout is due to saved credentials, mobile devices, or scheduled tasks.",
                "source": "internal",
                "url": "https://docs.company.com/account-lockouts",
                "created": "2025-02-10",
                "updated": "2025-10-15",
                "author": "Security Team",
                "@search.score": 0.85,
                "viewCount": 892,
                "helpfulCount": 156,
                "status": "resolved",
                "resolution": "Account was unlocked and root cause identified as outdated cached credentials on mobile device.",
                "resolvedDate": "2025-11-18",
            },
        ]
