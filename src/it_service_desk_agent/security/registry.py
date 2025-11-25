"""Policy registry and authorization enforcement"""

from typing import Dict
from .policy import OperationPolicy, UserPrincipal, AuthorizationError, RiskLevel


# Policy registry - defines RBAC rules for all operations
_POLICIES: Dict[str, OperationPolicy] = {
    # Active Directory operations
    "ad.user.lookup": OperationPolicy(
        name="ad.user.lookup",
        required_roles=["it_helpdesk", "it_admin", "viewer"],
        min_risk_level="low",
        requires_approval=False
    ),
    "ad.password.reset": OperationPolicy(
        name="ad.password.reset",
        required_roles=["it_helpdesk", "it_admin"],
        min_risk_level="medium",
        requires_approval=True  # Always require confirmation
    ),
    "ad.account.unlock": OperationPolicy(
        name="ad.account.unlock",
        required_roles=["it_helpdesk", "it_admin"],
        min_risk_level="low",
        requires_approval=False
    ),
    "ad.laps.retrieve": OperationPolicy(
        name="ad.laps.retrieve",
        required_roles=["it_admin"],  # Admins only
        min_risk_level="high",
        requires_approval=True  # HIGHLY SENSITIVE
    ),
    "ad.bitlocker.retrieve": OperationPolicy(
        name="ad.bitlocker.retrieve",
        required_roles=["it_helpdesk", "it_admin"],
        min_risk_level="medium",
        requires_approval=True
    ),
    
    # Microsoft Graph operations
    "graph.user.get": OperationPolicy(
        name="graph.user.get",
        required_roles=["it_helpdesk", "it_admin", "viewer"],
        min_risk_level="low",
        requires_approval=False
    ),
    "graph.license.assign": OperationPolicy(
        name="graph.license.assign",
        required_roles=["it_admin"],
        min_risk_level="medium",
        requires_approval=True
    ),
    "graph.license.remove": OperationPolicy(
        name="graph.license.remove",
        required_roles=["it_admin"],
        min_risk_level="medium",
        requires_approval=True
    ),
    "graph.group.add_member": OperationPolicy(
        name="graph.group.add_member",
        required_roles=["it_admin"],
        min_risk_level="medium",
        requires_approval=True  # Especially for privileged groups
    ),
    
    # ServiceNow operations
    "servicenow.incident.search": OperationPolicy(
        name="servicenow.incident.search",
        required_roles=["it_helpdesk", "it_admin", "viewer"],
        min_risk_level="low",
        requires_approval=False
    ),
    "servicenow.incident.create": OperationPolicy(
        name="servicenow.incident.create",
        required_roles=["it_helpdesk", "it_admin"],
        min_risk_level="low",
        requires_approval=False
    ),
    "servicenow.incident.resolve": OperationPolicy(
        name="servicenow.incident.resolve",
        required_roles=["it_helpdesk", "it_admin"],
        min_risk_level="low",
        requires_approval=False
    ),
    
    # Intune operations
    "intune.device.get": OperationPolicy(
        name="intune.device.get",
        required_roles=["it_helpdesk", "it_admin", "viewer"],
        min_risk_level="low",
        requires_approval=False
    ),
    "intune.device.sync": OperationPolicy(
        name="intune.device.sync",
        required_roles=["it_helpdesk", "it_admin"],
        min_risk_level="low",
        requires_approval=False  # Safe operation
    ),
    "intune.device.restart": OperationPolicy(
        name="intune.device.restart",
        required_roles=["it_helpdesk", "it_admin"],
        min_risk_level="medium",
        requires_approval=True
    ),
    "intune.device.wipe": OperationPolicy(
        name="intune.device.wipe",
        required_roles=["it_admin"],  # Admins only
        min_risk_level="critical",  # DESTRUCTIVE
        requires_approval=True  # ALWAYS require explicit approval
    ),
}


def authorize(
    operation: str,
    user: UserPrincipal,
    risk_level: RiskLevel,
    approved: bool = False
) -> None:
    """
    Enforce authorization for an operation
    
    Checks:
    1. Policy exists for operation
    2. User has required role
    3. Risk level is adequate
    4. Approval is granted (if required)
    
    Args:
        operation: Operation name (e.g., "ad.password.reset")
        user: User making the request
        risk_level: Assessed risk level
        approved: Whether approval has been granted
    
    Raises:
        AuthorizationError: If any check fails
    """
    policy = _POLICIES.get(operation)
    
    if not policy:
        raise AuthorizationError(
            f"No policy defined for operation '{operation}'. "
            f"Add policy to registry before allowing this operation.",
            code="POLICY_NOT_FOUND"
        )
    
    # Check roles
    if not any(role in user.roles for role in policy.required_roles):
        raise AuthorizationError(
            f"User '{user.id}' lacks required roles for '{operation}'. "
            f"Required: {policy.required_roles}, User has: {user.roles}",
            code="INSUFFICIENT_ROLES"
        )
    
    # Check risk level (map to numeric for comparison)
    risk_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    if risk_map[risk_level] < risk_map[policy.min_risk_level]:
        raise AuthorizationError(
            f"Operation '{operation}' requires at least '{policy.min_risk_level}' risk level, "
            f"but request has '{risk_level}'",
            code="INSUFFICIENT_RISK_LEVEL"
        )
    
    # Check approval
    if policy.requires_approval and not approved:
        raise AuthorizationError(
            f"Operation '{operation}' requires explicit approval. "
            f"User must confirm before proceeding.",
            code="APPROVAL_REQUIRED"
        )


def get_policy(operation: str) -> OperationPolicy:
    """Get policy for an operation"""
    policy = _POLICIES.get(operation)
    if not policy:
        raise AuthorizationError(
            f"No policy found for operation '{operation}'",
            code="POLICY_NOT_FOUND"
        )
    return policy


def list_policies() -> Dict[str, OperationPolicy]:
    """Get all registered policies"""
    return _POLICIES.copy()
