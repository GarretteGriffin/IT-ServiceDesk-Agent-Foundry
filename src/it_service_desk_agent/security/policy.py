"""Security policy models - RBAC and approval enforcement"""

from typing import List, Literal
from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high", "critical"]


class UserPrincipal(BaseModel):
    """User identity with roles"""
    id: str = Field(..., description="User identifier")
    roles: List[str] = Field(..., description="Assigned roles (e.g., 'it_helpdesk', 'it_admin')")


class OperationPolicy(BaseModel):
    """
    Policy for a specific operation
    
    Defines:
    - Who can do it (required_roles)
    - How dangerous it is (min_risk_level)
    - Whether it needs approval (requires_approval)
    """
    name: str = Field(..., description="Operation name (e.g., 'ad.password_reset')")
    required_roles: List[str] = Field(..., description="Roles allowed to perform this operation")
    min_risk_level: RiskLevel = Field(..., description="Minimum risk level required")
    requires_approval: bool = Field(False, description="Whether explicit approval is required")


class AuthorizationError(Exception):
    """Raised when authorization check fails"""
    
    def __init__(self, message: str, code: str = "UNAUTHORIZED"):
        self.message = message
        self.code = code
        super().__init__(self.message)
