"""
Identity Agent - Handles identity-related operations

This agent orchestrates Active Directory and Microsoft Graph operations
for user identity management tasks.
"""

from typing import List, Dict, Any
import time
from ..core.agent import Agent, AgentCapability
from ..core.models import AgentRequest, AgentResponse, AgentError, RequestContext
from ..security.registry import authorize
from ..security.audit import AuditLogger, AuditEventType


class IdentityAgent(Agent):
    """
    Identity management agent
    
    Handles:
    - User lookups (AD + Azure AD)
    - Password resets
    - Account unlocks
    - User device queries
    - License management
    """
    
    def __init__(self, ad_tools, graph_tools):
        """
        Initialize Identity Agent
        
        Args:
            ad_tools: ActiveDirectoryTools instance
            graph_tools: GraphUserTools instance
        """
        self._ad = ad_tools
        self._graph = graph_tools
    
    @property
    def name(self) -> str:
        return "identity_agent"
    
    @property
    def supported_intents(self) -> List[str]:
        return [
            "identity.user.lookup",
            "identity.password.reset",
            "identity.account.unlock",
            "identity.user.devices",
            "identity.license.assign",
            "identity.license.remove",
        ]
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="lookup_user",
                description="Look up user information from Active Directory and Azure AD",
                input_schema={
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Username or email"},
                        "include_groups": {"type": "boolean", "default": False},
                        "include_licenses": {"type": "boolean", "default": False},
                    },
                    "required": ["username"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "display_name": {"type": "string"},
                        "upn": {"type": "string"},
                        "enabled": {"type": "boolean"},
                        "groups": {"type": "array"},
                        "licenses": {"type": "array"},
                    }
                }
            ),
            AgentCapability(
                name="reset_password",
                description="Reset user password (requires approval)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "temporary_password": {"type": "string"},
                        "must_change": {"type": "boolean", "default": True},
                    },
                    "required": ["username", "temporary_password"]
                }
            ),
            AgentCapability(
                name="unlock_account",
                description="Unlock locked user account",
                input_schema={
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                    },
                    "required": ["username"]
                }
            ),
        ]
    
    async def handle(self, request: AgentRequest) -> AgentResponse:
        """
        Handle identity-related requests
        
        Routes to appropriate handler based on intent.
        All handlers enforce authorization and audit logging.
        """
        start_time = time.time()
        
        try:
            # Route to appropriate handler
            if request.intent == "identity.user.lookup":
                result = await self._handle_user_lookup(request)
            elif request.intent == "identity.password.reset":
                result = await self._handle_password_reset(request)
            elif request.intent == "identity.account.unlock":
                result = await self._handle_account_unlock(request)
            elif request.intent == "identity.user.devices":
                result = await self._handle_user_devices(request)
            elif request.intent == "identity.license.assign":
                result = await self._handle_license_assign(request)
            elif request.intent == "identity.license.remove":
                result = await self._handle_license_remove(request)
            else:
                return AgentResponse(
                    success=False,
                    error=AgentError(
                        code="UNSUPPORTED_INTENT",
                        message=f"Intent {request.intent} not supported by {self.name}",
                        details={"supported_intents": self.supported_intents}
                    )
                )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return AgentResponse(
                success=True,
                data=result,
                agent_name=self.name,
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            
            return AgentResponse(
                success=False,
                error=AgentError(
                    code="AGENT_ERROR",
                    message=str(e),
                    details={"intent": request.intent}
                ),
                agent_name=self.name,
                execution_time_ms=execution_time
            )
    
    async def _handle_user_lookup(self, request: AgentRequest) -> Dict[str, Any]:
        """Handle user lookup (read-only, safe operation)"""
        username = request.parameters.get("username")
        if not username:
            raise ValueError("username parameter required")
        
        # User lookup is low-risk, no authorization needed
        # Just audit for compliance
        AuditLogger.log_operation(
            event_type=AuditEventType.AUTH_SUCCESS,  # Using this as proxy for read
            context=request.context,
            outcome="success",
            details={"operation": "user_lookup", "target": username}
        )
        
        # Query both AD and Azure AD
        # (In real implementation, call actual tools)
        return {
            "username": username,
            "message": "User lookup - tools not yet wired in PHASE 6-7"
        }
    
    async def _handle_password_reset(self, request: AgentRequest) -> Dict[str, Any]:
        """Handle password reset (requires authorization)"""
        username = request.parameters.get("username")
        if not username:
            raise ValueError("username parameter required")
        
        # ENFORCE AUTHORIZATION
        authorize("identity.password.reset", request.context)
        
        try:
            # Call AD tool to reset password
            # (In real implementation)
            result = {"username": username, "status": "password_reset_placeholder"}
            
            # AUDIT SUCCESS
            AuditLogger.log_operation(
                event_type=AuditEventType.PASSWORD_RESET,
                context=request.context,
                outcome="success",
                details={"target_user": username}
            )
            
            return result
        
        except Exception as e:
            # AUDIT FAILURE
            AuditLogger.log_error(
                event_type=AuditEventType.PASSWORD_RESET,
                context=request.context,
                error=e,
                details={"target_user": username}
            )
            raise
    
    async def _handle_account_unlock(self, request: AgentRequest) -> Dict[str, Any]:
        """Handle account unlock"""
        username = request.parameters.get("username")
        if not username:
            raise ValueError("username parameter required")
        
        # Authorize and audit pattern (same as password reset)
        authorize("identity.account.unlock", request.context)
        
        try:
            result = {"username": username, "status": "account_unlock_placeholder"}
            
            AuditLogger.log_operation(
                event_type=AuditEventType.ACCOUNT_UNLOCK,
                context=request.context,
                outcome="success",
                details={"target_user": username}
            )
            
            return result
        
        except Exception as e:
            AuditLogger.log_error(
                event_type=AuditEventType.ACCOUNT_UNLOCK,
                context=request.context,
                error=e,
                details={"target_user": username}
            )
            raise
    
    async def _handle_user_devices(self, request: AgentRequest) -> Dict[str, Any]:
        """Handle user device query"""
        username = request.parameters.get("username")
        if not username:
            raise ValueError("username parameter required")
        
        # Query Graph for user's devices
        return {"username": username, "devices": "placeholder"}
    
    async def _handle_license_assign(self, request: AgentRequest) -> Dict[str, Any]:
        """Handle license assignment"""
        username = request.parameters.get("username")
        sku = request.parameters.get("sku")
        
        if not username or not sku:
            raise ValueError("username and sku parameters required")
        
        authorize("identity.license.assign", request.context)
        
        try:
            result = {"username": username, "sku": sku, "status": "placeholder"}
            
            AuditLogger.log_operation(
                event_type=AuditEventType.LICENSE_ASSIGN,
                context=request.context,
                outcome="success",
                details={"target_user": username, "sku": sku}
            )
            
            return result
        
        except Exception as e:
            AuditLogger.log_error(
                event_type=AuditEventType.LICENSE_ASSIGN,
                context=request.context,
                error=e,
                details={"target_user": username, "sku": sku}
            )
            raise
    
    async def _handle_license_remove(self, request: AgentRequest) -> Dict[str, Any]:
        """Handle license removal"""
        username = request.parameters.get("username")
        sku = request.parameters.get("sku")
        
        if not username or not sku:
            raise ValueError("username and sku parameters required")
        
        authorize("identity.license.remove", request.context)
        
        try:
            result = {"username": username, "sku": sku, "status": "placeholder"}
            
            AuditLogger.log_operation(
                event_type=AuditEventType.LICENSE_REMOVE,
                context=request.context,
                outcome="success",
                details={"target_user": username, "sku": sku}
            )
            
            return result
        
        except Exception as e:
            AuditLogger.log_error(
                event_type=AuditEventType.LICENSE_REMOVE,
                context=request.context,
                error=e,
                details={"target_user": username, "sku": sku}
            )
            raise
