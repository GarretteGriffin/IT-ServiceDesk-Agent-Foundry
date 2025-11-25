"""
ServiceNow Integration Tool
Comprehensive ServiceNow operations for incidents, requests, knowledge base, and CMDB
"""

from typing import Annotated, List, Dict, Any, Optional
import asyncio
from datetime import datetime

from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class ServiceNowTool:
    """
    ServiceNow integration tool for ITSM operations
    
    Capabilities:
    - Incident management (search, create, update, resolve)
    - Request management (catalog items, approvals)
    - Knowledge base search
    - CMDB queries (configuration items)
    - Change management
    - User and group lookup
    """
    
    def __init__(self):
        self.instance = settings.SERVICENOW_INSTANCE
        self.client_id = settings.SERVICENOW_CLIENT_ID
        logger.info(f"Initialized ServiceNow tool for instance: {self.instance}")
    
    def get_functions(self) -> List[callable]:
        """Return list of tool functions for agent"""
        return [
            self.search_incidents,
            self.create_incident,
            self.update_incident,
            self.resolve_incident,
            self.search_knowledge,
            self.get_cmdb_ci,
            self.search_users,
            self.create_request,
        ]
    
    async def search_incidents(
        self,
        query: Annotated[Optional[str], "Search query for incident description"] = None,
        assigned_to: Annotated[Optional[str], "Filter by assigned user"] = None,
        state: Annotated[Optional[str], "Filter by state: new, in_progress, on_hold, resolved, closed"] = None,
        priority: Annotated[Optional[int], "Filter by priority: 1-5"] = None,
        limit: Annotated[int, "Maximum number of results"] = 10,
    ) -> str:
        """
        Search ServiceNow incidents with filters.
        
        Returns matching incidents with number, description, state, priority, and assigned user.
        """
        logger.info(f"Searching ServiceNow incidents (query: {query}, state: {state})")
        
        try:
            # Build filters
            filters = []
            if query:
                filters.append(f"short_descriptionLIKE{query}")
            if assigned_to:
                filters.append(f"assigned_to.name={assigned_to}")
            if state:
                filters.append(f"state={self._state_to_value(state)}")
            if priority:
                filters.append(f"priority={priority}")
            
            query_string = "^".join(filters) if filters else ""
            
            # API call placeholder
            result = await self._api_call(
                "GET",
                f"/api/now/table/incident",
                params={
                    "sysparm_query": query_string,
                    "sysparm_limit": limit,
                    "sysparm_fields": "number,short_description,state,priority,assigned_to,opened_at,sys_updated_on"
                }
            )
            
            # Format results
            if not result:
                return "No incidents found matching criteria"
            
            incidents = []
            for inc in result:
                incidents.append(
                    f"• {inc['number']} - {inc['short_description']}\n"
                    f"  State: {inc['state']} | Priority: {inc['priority']} | "
                    f"  Assigned: {inc.get('assigned_to', 'Unassigned')}"
                )
            
            return f"Found {len(incidents)} incident(s):\n\n" + "\n\n".join(incidents)
            
        except Exception as e:
            logger.error(f"Error searching incidents: {e}")
            return f"Failed to search incidents: {str(e)}"
    
    async def create_incident(
        self,
        short_description: Annotated[str, "Brief description of the incident"],
        description: Annotated[str, "Detailed description"],
        urgency: Annotated[int, "Urgency: 1 (High), 2 (Medium), 3 (Low)"] = 2,
        category: Annotated[Optional[str], "Category: inquiry, software, hardware, network, database"] = None,
        assignment_group: Annotated[Optional[str], "Assignment group name"] = None,
    ) -> str:
        """
        Create a new ServiceNow incident.
        
        Returns the incident number and details.
        """
        logger.info(f"Creating incident: {short_description}")
        
        try:
            data = {
                "short_description": short_description,
                "description": description,
                "urgency": urgency,
                "impact": urgency,  # Match impact to urgency
            }
            
            if category:
                data["category"] = category
            if assignment_group:
                data["assignment_group"] = assignment_group
            
            result = await self._api_call(
                "POST",
                "/api/now/table/incident",
                data=data
            )
            
            inc_number = result.get("number", "UNKNOWN")
            sys_id = result.get("sys_id", "")
            
            # Audit log
            logger.info(f"Created incident {inc_number}")
            
            return (
                f"✓ Incident created successfully\n\n"
                f"Incident Number: {inc_number}\n"
                f"Description: {short_description}\n"
                f"Urgency: {urgency}\n"
                f"Category: {category or 'Not specified'}\n"
                f"Assignment Group: {assignment_group or 'Not assigned'}\n\n"
                f"URL: https://{self.instance}/nav_to.do?uri=incident.do?sys_id={sys_id}"
            )
            
        except Exception as e:
            logger.error(f"Error creating incident: {e}")
            return f"Failed to create incident: {str(e)}"
    
    async def update_incident(
        self,
        incident_number: Annotated[str, "Incident number (e.g., INC0012345)"],
        work_notes: Annotated[Optional[str], "Work notes to add"] = None,
        state: Annotated[Optional[str], "New state: new, in_progress, on_hold, resolved, closed"] = None,
        assigned_to: Annotated[Optional[str], "Assign to user"] = None,
    ) -> str:
        """
        Update an existing ServiceNow incident.
        
        Can add work notes, change state, or reassign.
        """
        logger.info(f"Updating incident: {incident_number}")
        
        try:
            data = {}
            
            if work_notes:
                data["work_notes"] = work_notes
            if state:
                data["state"] = self._state_to_value(state)
            if assigned_to:
                data["assigned_to"] = assigned_to
            
            result = await self._api_call(
                "PATCH",
                f"/api/now/table/incident/{incident_number}",
                data=data
            )
            
            return (
                f"✓ Incident {incident_number} updated successfully\n"
                f"Work notes added: {bool(work_notes)}\n"
                f"State changed: {state or 'No change'}\n"
                f"Assigned to: {assigned_to or 'No change'}"
            )
            
        except Exception as e:
            logger.error(f"Error updating incident: {e}")
            return f"Failed to update incident: {str(e)}"
    
    async def resolve_incident(
        self,
        incident_number: Annotated[str, "Incident number to resolve"],
        resolution_notes: Annotated[str, "Resolution notes explaining how issue was fixed"],
        close_code: Annotated[str, "Close code: solved, workaround, duplicate, not_reproducible"] = "solved",
    ) -> str:
        """
        Resolve a ServiceNow incident with resolution notes.
        """
        logger.info(f"Resolving incident: {incident_number}")
        
        try:
            data = {
                "state": "6",  # Resolved
                "close_notes": resolution_notes,
                "close_code": close_code,
                "resolved_at": datetime.utcnow().isoformat(),
            }
            
            result = await self._api_call(
                "PATCH",
                f"/api/now/table/incident/{incident_number}",
                data=data
            )
            
            return (
                f"✓ Incident {incident_number} resolved\n"
                f"Close Code: {close_code}\n"
                f"Resolution: {resolution_notes}"
            )
            
        except Exception as e:
            logger.error(f"Error resolving incident: {e}")
            return f"Failed to resolve incident: {str(e)}"
    
    async def search_knowledge(
        self,
        search_text: Annotated[str, "Search query for knowledge articles"],
        limit: Annotated[int, "Maximum number of results"] = 5,
    ) -> str:
        """
        Search ServiceNow knowledge base for articles.
        
        Returns relevant KB articles with title, excerpt, and URL.
        """
        logger.info(f"Searching knowledge base: {search_text}")
        
        try:
            result = await self._api_call(
                "GET",
                "/api/now/table/kb_knowledge",
                params={
                    "sysparm_query": f"short_descriptionLIKE{search_text}^ORtextLIKE{search_text}",
                    "sysparm_limit": limit,
                    "sysparm_fields": "number,short_description,text,sys_view_count"
                }
            )
            
            if not result:
                return f"No knowledge articles found for: {search_text}"
            
            articles = []
            for article in result:
                excerpt = article.get("text", "")[:200] + "..." if len(article.get("text", "")) > 200 else article.get("text", "")
                articles.append(
                    f"📄 {article['number']} - {article['short_description']}\n"
                    f"   Views: {article.get('sys_view_count', 0)}\n"
                    f"   {excerpt}\n"
                    f"   URL: https://{self.instance}/kb_view.do?sys_kb_id={article.get('sys_id', '')}"
                )
            
            return f"Found {len(articles)} knowledge article(s):\n\n" + "\n\n".join(articles)
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return f"Failed to search knowledge base: {str(e)}"
    
    async def get_cmdb_ci(
        self,
        ci_name: Annotated[str, "Configuration Item name or serial number"],
        ci_class: Annotated[Optional[str], "CI class: cmdb_ci_computer, cmdb_ci_server, cmdb_ci_network_adapter"] = None,
    ) -> str:
        """
        Get Configuration Item (CI) details from CMDB.
        
        Returns CI information including name, class, status, location, and relationships.
        """
        logger.info(f"Looking up CMDB CI: {ci_name}")
        
        try:
            table = ci_class or "cmdb_ci"
            
            result = await self._api_call(
                "GET",
                f"/api/now/table/{table}",
                params={
                    "sysparm_query": f"nameLIKE{ci_name}^ORserial_numberLIKE{ci_name}",
                    "sysparm_limit": "1",
                    "sysparm_fields": "name,sys_class_name,operational_status,location,ip_address,serial_number,asset_tag,managed_by"
                }
            )
            
            if not result:
                return f"No CI found matching: {ci_name}"
            
            ci = result[0]
            
            return (
                f"Configuration Item Details:\n\n"
                f"Name: {ci.get('name', 'N/A')}\n"
                f"Class: {ci.get('sys_class_name', 'N/A')}\n"
                f"Status: {ci.get('operational_status', 'N/A')}\n"
                f"Location: {ci.get('location', 'N/A')}\n"
                f"IP Address: {ci.get('ip_address', 'N/A')}\n"
                f"Serial Number: {ci.get('serial_number', 'N/A')}\n"
                f"Asset Tag: {ci.get('asset_tag', 'N/A')}\n"
                f"Managed By: {ci.get('managed_by', 'N/A')}"
            )
            
        except Exception as e:
            logger.error(f"Error getting CMDB CI: {e}")
            return f"Failed to get CMDB CI: {str(e)}"
    
    async def search_users(
        self,
        search_term: Annotated[str, "Search by name or email"],
        limit: Annotated[int, "Maximum results"] = 5,
    ) -> str:
        """Search for users in ServiceNow."""
        logger.info(f"Searching users: {search_term}")
        
        try:
            result = await self._api_call(
                "GET",
                "/api/now/table/sys_user",
                params={
                    "sysparm_query": f"nameLIKE{search_term}^ORemailLIKE{search_term}",
                    "sysparm_limit": limit,
                    "sysparm_fields": "name,email,title,department,active"
                }
            )
            
            if not result:
                return f"No users found matching: {search_term}"
            
            users = []
            for user in result:
                status = "Active" if user.get("active") == "true" else "Inactive"
                users.append(
                    f"👤 {user.get('name', 'N/A')}\n"
                    f"   Email: {user.get('email', 'N/A')}\n"
                    f"   Title: {user.get('title', 'N/A')}\n"
                    f"   Department: {user.get('department', 'N/A')}\n"
                    f"   Status: {status}"
                )
            
            return f"Found {len(users)} user(s):\n\n" + "\n\n".join(users)
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return f"Failed to search users: {str(e)}"
    
    async def create_request(
        self,
        short_description: Annotated[str, "Brief description of the request"],
        requested_for: Annotated[str, "User requesting (email or name)"],
        category: Annotated[str, "Category: hardware, software, access, service"],
        description: Annotated[Optional[str], "Detailed description"] = None,
    ) -> str:
        """Create a service request in ServiceNow."""
        logger.info(f"Creating request: {short_description}")
        
        try:
            data = {
                "short_description": short_description,
                "description": description or short_description,
                "requested_for": requested_for,
                "category": category,
            }
            
            result = await self._api_call(
                "POST",
                "/api/now/table/sc_request",
                data=data
            )
            
            req_number = result.get("number", "UNKNOWN")
            
            return (
                f"✓ Request created successfully\n\n"
                f"Request Number: {req_number}\n"
                f"Description: {short_description}\n"
                f"Requested For: {requested_for}\n"
                f"Category: {category}"
            )
            
        except Exception as e:
            logger.error(f"Error creating request: {e}")
            return f"Failed to create request: {str(e)}"
    
    def _state_to_value(self, state: str) -> str:
        """Convert state name to ServiceNow value"""
        state_map = {
            "new": "1",
            "in_progress": "2",
            "on_hold": "3",
            "resolved": "6",
            "closed": "7",
        }
        return state_map.get(state.lower(), state)
    
    async def _api_call(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Any:
        """
        Make ServiceNow REST API call with real httpx client
        """
        import httpx
        import base64
        
        try:
            # Build URL
            url = f"https://{self.instance}.service-now.com{endpoint}"
            
            # Basic auth or OAuth
            if hasattr(settings, 'SERVICENOW_USERNAME') and settings.SERVICENOW_USERNAME:
                # Basic auth
                credentials = f"{settings.SERVICENOW_USERNAME}:{settings.SERVICENOW_PASSWORD}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers = {
                    "Authorization": f"Basic {encoded}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            else:
                # OAuth2 (client credentials)
                raise NotImplementedError("OAuth2 for ServiceNow not yet implemented - use basic auth")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                result = response.json()
                
                # ServiceNow wraps responses in 'result'
                if isinstance(result, dict) and "result" in result:
                    return result["result"]
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"ServiceNow API HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"ServiceNow API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"ServiceNow API call failed: {e}")
            raise
