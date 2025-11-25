"""
Ticket Agent - Handles ServiceNow ticket operations

This agent orchestrates ServiceNow incident management operations.
"""

from typing import List, Dict, Any
import time
from ..core.agent import Agent, AgentCapability
from ..core.models import AgentRequest, AgentResponse, AgentError, RequestContext
from ..security.registry import authorize
from ..security.audit import AuditLogger, AuditEventType


class TicketAgent(Agent):
    """
    ServiceNow ticket management agent
    
    Handles:
    - Incident search
    - Incident creation
    - Incident updates
    - Incident resolution
    - Knowledge base search
    """
    
    def __init__(self, servicenow_tools):
        """
        Initialize Ticket Agent
        
        Args:
            servicenow_tools: ServiceNowTools instance
        """
        self._snow = servicenow_tools
    
    @property
    def name(self) -> str:
        return "ticket_agent"
    
    @property
    def supported_intents(self) -> List[str]:
        return [
            "ticket.search",
            "ticket.create",
            "ticket.update",
            "ticket.resolve",
            "ticket.kb_search",
        ]
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="search_incidents",
                description="Search for ServiceNow incidents",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "assigned_to": {"type": "string", "description": "Filter by assignee"},
                        "state": {"type": "string", "description": "Filter by state (new, in_progress, resolved, etc.)"},
                        "priority": {"type": "string", "description": "Filter by priority (critical, high, medium, low)"},
                        "limit": {"type": "integer", "default": 20},
                    }
                }
            ),
            AgentCapability(
                name="create_incident",
                description="Create new ServiceNow incident",
                input_schema={
                    "type": "object",
                    "properties": {
                        "short_description": {"type": "string", "description": "Brief title (min 5 chars)"},
                        "description": {"type": "string", "description": "Detailed description (min 10 chars)"},
                        "priority": {"type": "string", "description": "Priority level (critical, high, medium, low)"},
                        "caller_id": {"type": "string", "description": "User requesting help"},
                        "assignment_group": {"type": "string", "description": "Group to assign to"},
                    },
                    "required": ["short_description", "description"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "incident_number": {"type": "string"},
                        "sys_id": {"type": "string"},
                        "state": {"type": "string"},
                    }
                }
            ),
            AgentCapability(
                name="update_incident",
                description="Update existing incident fields",
                input_schema={
                    "type": "object",
                    "properties": {
                        "incident_number": {"type": "string"},
                        "work_notes": {"type": "string"},
                        "state": {"type": "string"},
                        "priority": {"type": "string"},
                        "assigned_to": {"type": "string"},
                    },
                    "required": ["incident_number"]
                }
            ),
            AgentCapability(
                name="resolve_incident",
                description="Resolve incident with resolution notes",
                input_schema={
                    "type": "object",
                    "properties": {
                        "incident_number": {"type": "string"},
                        "resolution_notes": {"type": "string", "description": "Why/how resolved (min 10 chars)"},
                    },
                    "required": ["incident_number", "resolution_notes"]
                }
            ),
            AgentCapability(
                name="search_knowledge",
                description="Search ServiceNow knowledge base",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["query"]
                }
            ),
        ]
    
    async def handle(self, request: AgentRequest, context: RequestContext) -> AgentResponse:
        """Handle ticket management requests"""
        start_time = time.time()
        
        try:
            intent = request.intent
            params = request.parameters or {}
            
            # Route to appropriate handler
            if intent == "ticket.search":
                result = await self._handle_search_incidents(params, context)
            elif intent == "ticket.create":
                result = await self._handle_create_incident(params, context)
            elif intent == "ticket.update":
                result = await self._handle_update_incident(params, context)
            elif intent == "ticket.resolve":
                result = await self._handle_resolve_incident(params, context)
            elif intent == "ticket.kb_search":
                result = await self._handle_kb_search(params, context)
            else:
                raise AgentError(f"Unsupported intent: {intent}")
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return AgentResponse(
                agent_name=self.name,
                intent=intent,
                result=result,
                latency_ms=latency_ms,
                context=context
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            raise AgentError(f"Ticket operation failed: {str(e)}")
    
    async def _handle_search_incidents(self, params: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """Search incidents"""
        query = params.get("query")
        assigned_to = params.get("assigned_to")
        state = params.get("state")
        priority = params.get("priority")
        limit = params.get("limit", 20)
        
        incidents = await self._snow.search_incidents(
            query=query,
            assigned_to=assigned_to,
            state=state,
            priority=priority,
            limit=limit
        )
        
        # Audit
        AuditLogger.log(
            event_type=AuditEventType.TICKET_QUERY,
            user_id=context.user_id,
            action="search_incidents",
            result="success",
            metadata={
                "count": len(incidents),
                "filters": {k: v for k, v in params.items() if v}
            }
        )
        
        return {"incidents": incidents, "count": len(incidents)}
    
    async def _handle_create_incident(self, params: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """Create new incident"""
        short_description = params.get("short_description")
        description = params.get("description")
        priority = params.get("priority", "medium")
        caller_id = params.get("caller_id", context.user_id)
        assignment_group = params.get("assignment_group")
        
        if not short_description or not description:
            raise AgentError("short_description and description required")
        
        # Require authorization for ticket creation
        authorize("ticket.create", context)
        
        result = await self._snow.create_incident(
            short_description=short_description,
            description=description,
            priority=priority,
            caller_id=caller_id,
            assignment_group=assignment_group
        )
        
        # Audit
        AuditLogger.log(
            event_type=AuditEventType.TICKET_CREATE,
            user_id=context.user_id,
            resource_id=result.get("incident_number"),
            action="create_incident",
            result="success",
            metadata={
                "priority": priority,
                "caller": caller_id
            }
        )
        
        return result
    
    async def _handle_update_incident(self, params: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """Update incident"""
        incident_number = params.get("incident_number")
        if not incident_number:
            raise AgentError("incident_number required")
        
        # Require authorization for updates
        authorize("ticket.update", context)
        
        # Extract update fields
        updates = {k: v for k, v in params.items() if k != "incident_number" and v is not None}
        
        result = await self._snow.update_incident(incident_number, **updates)
        
        # Audit
        AuditLogger.log(
            event_type=AuditEventType.TICKET_UPDATE,
            user_id=context.user_id,
            resource_id=incident_number,
            action="update_incident",
            result="success",
            metadata={"updates": list(updates.keys())}
        )
        
        return result
    
    async def _handle_resolve_incident(self, params: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """Resolve incident"""
        incident_number = params.get("incident_number")
        resolution_notes = params.get("resolution_notes")
        
        if not incident_number or not resolution_notes:
            raise AgentError("incident_number and resolution_notes required")
        
        # Require authorization for resolution
        authorize("ticket.resolve", context)
        
        result = await self._snow.resolve_incident(incident_number, resolution_notes)
        
        # Audit
        AuditLogger.log(
            event_type=AuditEventType.TICKET_RESOLVE,
            user_id=context.user_id,
            resource_id=incident_number,
            action="resolve_incident",
            result="success"
        )
        
        return result
    
    async def _handle_kb_search(self, params: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """Search knowledge base"""
        query = params.get("query")
        limit = params.get("limit", 10)
        
        if not query:
            raise AgentError("query required")
        
        articles = await self._snow.search_knowledge(query, limit)
        
        # Audit
        AuditLogger.log(
            event_type=AuditEventType.KB_SEARCH,
            user_id=context.user_id,
            action="kb_search",
            result="success",
            metadata={"query": query, "count": len(articles)}
        )
        
        return {"articles": articles, "count": len(articles)}
