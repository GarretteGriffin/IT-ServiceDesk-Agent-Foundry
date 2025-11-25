"""ServiceNow API client - thin wrapper over base HTTP client"""

from typing import Dict, Any, List, Optional
import base64
from .base_http import HttpIntegrationClient


class ServiceNowClient(HttpIntegrationClient):
    """
    ServiceNow REST API client
    
    Uses HTTP basic auth (for now - TODO: OAuth2)
    """
    
    def __init__(
        self,
        instance_url: str,
        username: str,
        password: str
    ):
        """
        Initialize ServiceNow client
        
        Args:
            instance_url: ServiceNow instance URL (e.g., "https://dev12345.service-now.com")
            username: ServiceNow username
            password: ServiceNow password
        """
        # Create basic auth header
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        super().__init__(
            base_url=instance_url,
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
    
    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Override to handle ServiceNow response wrapping"""
        result = await super()._request(method, url, **kwargs)
        
        # ServiceNow wraps responses in 'result'
        if isinstance(result, dict) and "result" in result:
            return result["result"]
        
        return result
    
    # Incident operations
    async def search_incidents(
        self,
        query: Optional[str] = None,
        assigned_to: Optional[str] = None,
        state: Optional[str] = None,
        priority: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search incidents with filters
        
        Args:
            query: Search text in description
            assigned_to: Filter by assigned user
            state: Filter by state (new, in_progress, resolved, etc.)
            priority: Filter by priority (1-5)
            limit: Max results
        
        Returns:
            List of incident records
        """
        # Build filter query
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
        
        params = {
            "sysparm_query": query_string,
            "sysparm_limit": limit,
            "sysparm_fields": "number,short_description,state,priority,assigned_to,opened_at,sys_updated_on"
        }
        
        return await self._request("GET", "/api/now/table/incident", params=params)
    
    async def create_incident(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new incident
        
        Args:
            payload: Incident data (short_description, description, priority, etc.)
        
        Returns:
            Created incident record
        """
        return await self._request("POST", "/api/now/table/incident", json=payload)
    
    async def get_incident(self, incident_sys_id: str) -> Dict[str, Any]:
        """Get incident by sys_id"""
        return await self._request("GET", f"/api/now/table/incident/{incident_sys_id}")
    
    async def update_incident(self, incident_sys_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update incident"""
        return await self._request("PATCH", f"/api/now/table/incident/{incident_sys_id}", json=payload)
    
    async def resolve_incident(self, incident_sys_id: str, resolution_notes: str) -> Dict[str, Any]:
        """Resolve incident"""
        payload = {
            "state": "6",  # Resolved
            "close_notes": resolution_notes
        }
        return await self.update_incident(incident_sys_id, payload)
    
    # Knowledge base operations
    async def search_knowledge(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base articles"""
        params = {
            "sysparm_query": f"textLIKE{query}",
            "sysparm_limit": limit,
            "sysparm_fields": "number,short_description,text,kb_knowledge_base"
        }
        return await self._request("GET", "/api/now/table/kb_knowledge", params=params)
    
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
