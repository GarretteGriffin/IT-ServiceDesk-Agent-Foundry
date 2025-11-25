"""
ServiceNow Tools - Safe operations built on ServiceNow integration

This tool layer:
- Validates inputs
- Wraps ServiceNowClient with domain logic
- Provides user-friendly abstractions for tickets
"""

from typing import Dict, Any, List, Optional
from ..integrations.servicenow import ServiceNowClient


class ServiceNowTools:
    """
    ServiceNow ITSM operations
    
    All operations validate inputs and normalize outputs.
    """
    
    def __init__(self, snow_client: ServiceNowClient):
        """
        Initialize ServiceNow tools
        
        Args:
            snow_client: ServiceNowClient instance
        """
        self._snow = snow_client
    
    async def search_incidents(
        self,
        query: Optional[str] = None,
        assigned_to: Optional[str] = None,
        state: Optional[str] = None,
        priority: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for incidents
        
        Args:
            query: Search text
            assigned_to: Filter by assigned user
            state: Filter by state (new, in_progress, resolved, closed)
            priority: Priority (1=Critical, 2=High, 3=Medium, 4=Low, 5=Planning)
            limit: Max results
        
        Returns:
            List of incident summaries
        """
        incidents = await self._snow.search_incidents(
            query=query,
            assigned_to=assigned_to,
            state=state,
            priority=priority,
            limit=limit
        )
        
        # Normalize output
        return [
            {
                "number": inc.get("number"),
                "short_description": inc.get("short_description"),
                "state": self._normalize_state(inc.get("state")),
                "priority": self._normalize_priority(inc.get("priority")),
                "assigned_to": inc.get("assigned_to", {}).get("display_value") if isinstance(inc.get("assigned_to"), dict) else inc.get("assigned_to"),
                "opened_at": inc.get("opened_at"),
                "updated_at": inc.get("sys_updated_on")
            }
            for inc in incidents
        ]
    
    async def create_incident(
        self,
        short_description: str,
        description: str,
        priority: int = 3,
        caller_id: Optional[str] = None,
        assignment_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new incident
        
        Args:
            short_description: Brief title (required)
            description: Detailed description (required)
            priority: Priority (1-5, default 3=Medium)
            caller_id: User who reported issue
            assignment_group: Group to assign to
        
        Returns:
            Created incident details
        """
        if not short_description or len(short_description.strip()) < 5:
            raise ValueError("Short description must be at least 5 characters")
        
        if not description or len(description.strip()) < 10:
            raise ValueError("Description must be at least 10 characters")
        
        if priority not in range(1, 6):
            raise ValueError("Priority must be 1-5")
        
        payload = {
            "short_description": short_description.strip(),
            "description": description.strip(),
            "priority": str(priority),
            "caller_id": caller_id,
            "assignment_group": assignment_group
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        incident = await self._snow.create_incident(payload)
        
        return {
            "number": incident.get("number"),
            "sys_id": incident.get("sys_id"),
            "short_description": incident.get("short_description"),
            "state": self._normalize_state(incident.get("state")),
            "priority": self._normalize_priority(incident.get("priority")),
            "message": f"Incident {incident.get('number')} created successfully"
        }
    
    async def get_incident(self, incident_number: str) -> Dict[str, Any]:
        """
        Get incident details by number
        
        Args:
            incident_number: Incident number (e.g., INC0010001)
        
        Returns:
            Full incident details
        """
        # ServiceNow API uses sys_id, need to search by number first
        results = await self._snow.search_incidents(query=incident_number, limit=1)
        
        if not results:
            raise ValueError(f"Incident not found: {incident_number}")
        
        incident = results[0]
        
        return {
            "number": incident.get("number"),
            "sys_id": incident.get("sys_id"),
            "short_description": incident.get("short_description"),
            "description": incident.get("description"),
            "state": self._normalize_state(incident.get("state")),
            "priority": self._normalize_priority(incident.get("priority")),
            "assigned_to": incident.get("assigned_to"),
            "opened_at": incident.get("opened_at"),
            "updated_at": incident.get("sys_updated_on"),
            "caller_id": incident.get("caller_id")
        }
    
    async def update_incident(
        self,
        incident_number: str,
        **updates
    ) -> Dict[str, Any]:
        """
        Update incident
        
        Args:
            incident_number: Incident number
            **updates: Fields to update (state, priority, assigned_to, etc.)
        
        Returns:
            Updated incident details
        """
        # Get sys_id from number
        incident = await self.get_incident(incident_number)
        sys_id = incident["sys_id"]
        
        result = await self._snow.update_incident(sys_id, updates)
        
        return {
            "number": result.get("number"),
            "message": f"Incident {incident_number} updated successfully",
            "updated_fields": list(updates.keys())
        }
    
    async def resolve_incident(
        self,
        incident_number: str,
        resolution_notes: str
    ) -> Dict[str, Any]:
        """
        Resolve incident
        
        Args:
            incident_number: Incident number
            resolution_notes: Resolution description
        
        Returns:
            Success confirmation
        """
        if not resolution_notes or len(resolution_notes.strip()) < 10:
            raise ValueError("Resolution notes must be at least 10 characters")
        
        # Get sys_id
        incident = await self.get_incident(incident_number)
        sys_id = incident["sys_id"]
        
        result = await self._snow.resolve_incident(sys_id, resolution_notes.strip())
        
        return {
            "number": incident_number,
            "state": "Resolved",
            "message": f"Incident {incident_number} resolved successfully"
        }
    
    async def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search knowledge base
        
        Args:
            query: Search query
            limit: Max results
        
        Returns:
            List of KB articles
        """
        articles = await self._snow.search_knowledge(query, limit)
        
        return [
            {
                "number": article.get("number"),
                "short_description": article.get("short_description"),
                "text": article.get("text", "")[:200] + "...",  # Truncate
                "url": article.get("url")
            }
            for article in articles
        ]
    
    def _normalize_state(self, state: str) -> str:
        """Convert state number to friendly name"""
        states = {
            "1": "New",
            "2": "In Progress",
            "3": "On Hold",
            "6": "Resolved",
            "7": "Closed",
            "8": "Canceled"
        }
        return states.get(str(state), f"State {state}")
    
    def _normalize_priority(self, priority: str) -> str:
        """Convert priority number to friendly name"""
        priorities = {
            "1": "Critical",
            "2": "High",
            "3": "Medium",
            "4": "Low",
            "5": "Planning"
        }
        return priorities.get(str(priority), f"Priority {priority}")
