"""Unit tests for security layer - NO external calls"""

import pytest
from it_service_desk_agent.security.policy import UserPrincipal, OperationPolicy, AuthorizationError
from it_service_desk_agent.security.registry import authorize, get_policy, list_policies


def test_authorize_success_with_correct_role():
    """User with correct role should be authorized"""
    user = UserPrincipal(id="user1", roles=["it_helpdesk"])
    
    # Should not raise
    authorize(
        operation="ad.user.lookup",
        user=user,
        risk_level="low",
        approved=False
    )


def test_authorize_fails_without_required_role():
    """User without required role should be rejected"""
    user = UserPrincipal(id="user1", roles=["viewer"])
    
    with pytest.raises(AuthorizationError) as exc_info:
        authorize(
            operation="ad.password.reset",  # Requires it_helpdesk or it_admin
            user=user,
            risk_level="medium",
            approved=True
        )
    
    assert exc_info.value.code == "INSUFFICIENT_ROLES"
    assert "user1" in exc_info.value.message
    assert "it_helpdesk" in exc_info.value.message


def test_authorize_fails_without_approval():
    """Operation requiring approval should fail without it"""
    user = UserPrincipal(id="admin1", roles=["it_admin"])
    
    with pytest.raises(AuthorizationError) as exc_info:
        authorize(
            operation="ad.password.reset",  # Requires approval
            user=user,
            risk_level="medium",
            approved=False  # No approval
        )
    
    assert exc_info.value.code == "APPROVAL_REQUIRED"
    assert "approval" in exc_info.value.message.lower()


def test_authorize_succeeds_with_approval():
    """Operation requiring approval should succeed with it"""
    user = UserPrincipal(id="admin1", roles=["it_admin"])
    
    # Should not raise
    authorize(
        operation="ad.password.reset",
        user=user,
        risk_level="medium",
        approved=True  # Approval granted
    )


def test_authorize_fails_with_insufficient_risk_level():
    """Operation with low risk level should fail for high-risk operation"""
    user = UserPrincipal(id="admin1", roles=["it_admin"])
    
    with pytest.raises(AuthorizationError) as exc_info:
        authorize(
            operation="ad.laps.retrieve",  # Requires 'high' risk level
            user=user,
            risk_level="low",  # Too low
            approved=True
        )
    
    assert exc_info.value.code == "INSUFFICIENT_RISK_LEVEL"


def test_authorize_fails_for_unknown_operation():
    """Authorization should fail for operations without policies"""
    user = UserPrincipal(id="admin1", roles=["it_admin"])
    
    with pytest.raises(AuthorizationError) as exc_info:
        authorize(
            operation="nonexistent.operation",
            user=user,
            risk_level="low",
            approved=False
        )
    
    assert exc_info.value.code == "POLICY_NOT_FOUND"


def test_critical_operations_require_admin_and_approval():
    """Critical operations like device wipe require admin role and approval"""
    # Non-admin with approval should fail
    non_admin = UserPrincipal(id="tech1", roles=["it_helpdesk"])
    
    with pytest.raises(AuthorizationError):
        authorize(
            operation="intune.device.wipe",
            user=non_admin,
            risk_level="critical",
            approved=True
        )
    
    # Admin without approval should fail
    admin = UserPrincipal(id="admin1", roles=["it_admin"])
    
    with pytest.raises(AuthorizationError):
        authorize(
            operation="intune.device.wipe",
            user=admin,
            risk_level="critical",
            approved=False
        )
    
    # Admin with approval should succeed
    authorize(
        operation="intune.device.wipe",
        user=admin,
        risk_level="critical",
        approved=True
    )


def test_get_policy_returns_policy():
    """get_policy should return policy for known operation"""
    policy = get_policy("ad.password.reset")
    
    assert policy.name == "ad.password.reset"
    assert policy.requires_approval is True
    assert "it_helpdesk" in policy.required_roles or "it_admin" in policy.required_roles


def test_get_policy_raises_for_unknown():
    """get_policy should raise for unknown operation"""
    with pytest.raises(AuthorizationError) as exc_info:
        get_policy("unknown.operation")
    
    assert exc_info.value.code == "POLICY_NOT_FOUND"


def test_list_policies_returns_all():
    """list_policies should return all registered policies"""
    policies = list_policies()
    
    assert isinstance(policies, dict)
    assert len(policies) > 0
    assert "ad.password.reset" in policies
    assert "intune.device.wipe" in policies
    assert "graph.user.get" in policies
