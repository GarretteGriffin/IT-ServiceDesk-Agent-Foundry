"""Core domain models with strict typing - no vibes-only abstractions"""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class RequestContext(BaseModel):
    """Context flowing through every request - who, where, and risk level"""
    user_id: str = Field(..., description="User making the request")
    source: Literal["teams", "web", "cli", "api"] = Field(..., description="Request origin")
    correlation_id: str = Field(..., description="Unique request ID for tracing")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(..., description="Assessed risk of operation")
    
    # Optional organizational context
    tenant_id: Optional[str] = Field(None, description="Multi-tenant identifier")
    department: Optional[str] = Field(None, description="User's department")
    
    # Optional approval context
    approval_granted: bool = Field(False, description="Whether approval has been granted for dangerous operations")
    approver_id: Optional[str] = Field(None, description="User who granted approval")


class AgentRequest(BaseModel):
    """Structured input to any agent - no free-form nonsense"""
    intent: str = Field(..., description="What the agent should do (e.g., 'ad.password_reset')")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Intent-specific parameters")
    context: RequestContext = Field(..., description="Request context (user, source, risk)")


class AgentError(BaseModel):
    """Structured error - no exceptions leaking to callers"""
    code: str = Field(..., description="Machine-readable error code (e.g., 'UNAUTHORIZED', 'INVALID_INPUT')")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class AgentResponse(BaseModel):
    """Structured output from any agent - success or failure, never undefined"""
    success: bool = Field(..., description="Whether operation succeeded")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data if successful")
    error: Optional[AgentError] = Field(None, description="Error details if failed")
    
    # Audit trail
    agent_name: Optional[str] = Field(None, description="Which agent handled this")
    execution_time_ms: Optional[int] = Field(None, description="How long it took")
