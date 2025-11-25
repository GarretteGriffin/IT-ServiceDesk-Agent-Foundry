"""
Device Agent - Handles device management operations

This agent orchestrates Intune device management operations.
"""

from typing import List, Dict, Any
import time
from ..core.agent import Agent, AgentCapability
from ..core.models import AgentRequest, AgentResponse, AgentError, RequestContext
from ..security.registry import authorize
from ..security.audit import AuditLogger, AuditEventType


class DeviceAgent(Agent):
    """
    Device management agent
    
    Handles:
    - Device lookups
    - Device sync operations
    - Remote device actions (restart, wipe)
    """
    
    def __init__(self, intune_tools):
        """
        Initialize Device Agent
        
        Args:
            intune_tools: IntuneDeviceTools instance
        """
        self._intune = intune_tools
    
    @property
    def name(self) -> str:
        return "device_agent"
    
    @property
    def supported_intents(self) -> List[str]:
        return [
            "device.get",
            "device.list",
            "device.sync",
            "device.restart",
            "device.wipe",
        ]
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="get_device",
                description="Get details for a specific device",
                input_schema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "Device ID or name"},
                    },
                    "required": ["device_id"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "device_name": {"type": "string"},
                        "os": {"type": "string"},
                        "user": {"type": "string"},
                        "compliance_state": {"type": "string"},
                        "last_sync": {"type": "string"},
                    }
                }
            ),
            AgentCapability(
                name="list_devices",
                description="List devices with optional filtering",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_upn": {"type": "string", "description": "Filter by user"},
                        "os_type": {"type": "string", "description": "Filter by OS (Windows, iOS, Android)"},
                        "compliance_state": {"type": "string", "description": "Filter by compliance (compliant, noncompliant)"},
                        "limit": {"type": "integer", "default": 50},
                    }
                }
            ),
            AgentCapability(
                name="sync_device",
                description="Trigger Intune sync for device",
                input_schema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                    },
                    "required": ["device_id"]
                }
            ),
            AgentCapability(
                name="restart_device",
                description="Remotely restart device (requires approval)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                    },
                    "required": ["device_id"]
                }
            ),
            AgentCapability(
                name="wipe_device",
                description="DESTRUCTIVE: Wipe device (requires explicit approval)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                    },
                    "required": ["device_id"]
                }
            ),
        ]
    
    async def handle(self, request: AgentRequest, context: RequestContext) -> AgentResponse:
        """Handle device management requests"""
        start_time = time.time()
        
        try:
            intent = request.intent
            params = request.parameters or {}
            
            # Route to appropriate handler
            if intent == "device.get":
                result = await self._handle_get_device(params, context)
            elif intent == "device.list":
                result = await self._handle_list_devices(params, context)
            elif intent == "device.sync":
                result = await self._handle_sync_device(params, context)
            elif intent == "device.restart":
                result = await self._handle_restart_device(params, context)
            elif intent == "device.wipe":
                result = await self._handle_wipe_device(params, context)
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
            raise AgentError(f"Device operation failed: {str(e)}")
    
    async def _handle_get_device(self, params: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """Get device details"""
        device_id = params.get("device_id")
        if not device_id:
            raise AgentError("device_id required")
        
        result = await self._intune.get_device(device_id)
        
        # Audit
        AuditLogger.log(
            event_type=AuditEventType.DEVICE_QUERY,
            user_id=context.user_id,
            resource_id=device_id,
            action="get_device",
            result="success",
            metadata={"device_name": result.get("device_name")}
        )
        
        return result
    
    async def _handle_list_devices(self, params: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """List devices with filtering"""
        user_upn = params.get("user_upn")
        os_type = params.get("os_type")
        compliance_state = params.get("compliance_state")
        limit = params.get("limit", 50)
        
        devices = await self._intune.list_devices(
            user_upn=user_upn,
            os_type=os_type,
            compliance_state=compliance_state,
            limit=limit
        )
        
        # Audit
        AuditLogger.log(
            event_type=AuditEventType.DEVICE_QUERY,
            user_id=context.user_id,
            action="list_devices",
            result="success",
            metadata={
                "count": len(devices),
                "filters": {k: v for k, v in params.items() if v}
            }
        )
        
        return {"devices": devices, "count": len(devices)}
    
    async def _handle_sync_device(self, params: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """Trigger device sync"""
        device_id = params.get("device_id")
        if not device_id:
            raise AgentError("device_id required")
        
        # No authorization needed for sync (safe operation)
        result = await self._intune.sync_device(device_id)
        
        # Audit
        AuditLogger.log(
            event_type=AuditEventType.DEVICE_SYNC,
            user_id=context.user_id,
            resource_id=device_id,
            action="sync_device",
            result="success"
        )
        
        return result
    
    async def _handle_restart_device(self, params: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """Restart device remotely"""
        device_id = params.get("device_id")
        if not device_id:
            raise AgentError("device_id required")
        
        # Require authorization for restart
        authorize("device.restart", context)
        
        result = await self._intune.restart_device(device_id)
        
        # Audit
        AuditLogger.log(
            event_type=AuditEventType.DEVICE_RESTART,
            user_id=context.user_id,
            resource_id=device_id,
            action="restart_device",
            result="success",
            requires_approval=True
        )
        
        return result
    
    async def _handle_wipe_device(self, params: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """DESTRUCTIVE: Wipe device"""
        device_id = params.get("device_id")
        if not device_id:
            raise AgentError("device_id required")
        
        # Require authorization for DESTRUCTIVE operation
        authorize("device.wipe", context)
        
        result = await self._intune.wipe_device(device_id)
        
        # Audit with high severity
        AuditLogger.log(
            event_type=AuditEventType.DEVICE_WIPE,
            user_id=context.user_id,
            resource_id=device_id,
            action="wipe_device",
            result="success",
            requires_approval=True,
            metadata={"severity": "CRITICAL"}
        )
        
        return result
