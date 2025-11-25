"""
Audit logging for security-sensitive operations

All dangerous operations (password resets, device wipes, LAPS access, etc.)
MUST be logged through this module for compliance and forensics.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from ..core.models import RequestContext

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of auditable events"""
    # Authentication & Authorization
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    AUTH_DENIED = "auth.denied"
    
    # Identity operations
    PASSWORD_RESET = "identity.password_reset"
    ACCOUNT_UNLOCK = "identity.account_unlock"
    USER_CREATE = "identity.user_create"
    USER_DELETE = "identity.user_delete"
    
    # Privileged access
    LAPS_RETRIEVE = "privileged.laps_retrieve"
    BITLOCKER_RETRIEVE = "privileged.bitlocker_retrieve"
    ADMIN_RIGHTS_GRANT = "privileged.admin_grant"
    
    # Device operations
    DEVICE_WIPE = "device.wipe"
    DEVICE_RETIRE = "device.retire"
    DEVICE_SYNC = "device.sync"
    DEVICE_RESTART = "device.restart"
    
    # License & access
    LICENSE_ASSIGN = "access.license_assign"
    LICENSE_REMOVE = "access.license_remove"
    GROUP_ADD = "access.group_add"
    GROUP_REMOVE = "access.group_remove"
    
    # Ticketing
    INCIDENT_CREATE = "ticket.incident_create"
    INCIDENT_RESOLVE = "ticket.incident_resolve"
    INCIDENT_UPDATE = "ticket.incident_update"


class AuditLogger:
    """
    Centralized audit logger for all security-sensitive operations
    
    Usage:
        AuditLogger.log_operation(
            event_type=AuditEventType.PASSWORD_RESET,
            context=request_context,
            outcome="success",
            details={"target_user": "user@example.com"}
        )
    """
    
    @staticmethod
    def log_operation(
        event_type: AuditEventType,
        context: RequestContext,
        outcome: str,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log a security-sensitive operation
        
        Args:
            event_type: Type of event (from AuditEventType enum)
            context: Request context (who, when, where)
            outcome: "success", "failure", "denied", "partial"
            details: Operation-specific details (what was changed)
            error_message: Error message if outcome is failure
        """
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "outcome": outcome,
            
            # Who
            "user_id": context.user_id,
            "tenant_id": context.tenant_id,
            "department": context.department,
            
            # Where
            "source": context.source,
            "correlation_id": context.correlation_id,
            
            # Risk context
            "risk_level": context.risk_level,
            "approval_granted": context.approval_granted,
            "approver_id": context.approver_id,
            
            # What
            "details": details or {},
            "error_message": error_message,
        }
        
        # Log at appropriate level based on outcome
        log_level = logging.INFO if outcome == "success" else logging.WARNING
        logger.log(
            log_level,
            f"AUDIT: {event_type.value} | {outcome} | user={context.user_id} | correlation={context.correlation_id}",
            extra={"audit_record": audit_record}
        )
        
        # In production, also send to:
        # - Azure Monitor / Log Analytics
        # - SIEM (Sentinel, Splunk, etc.)
        # - Compliance database
        # - TODO: Implement actual audit sink here
    
    @staticmethod
    def log_error(
        event_type: AuditEventType,
        context: RequestContext,
        error: Exception,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Convenience method for logging operation failures
        
        Args:
            event_type: Type of event that failed
            context: Request context
            error: Exception that occurred
            details: Additional context
        """
        AuditLogger.log_operation(
            event_type=event_type,
            context=context,
            outcome="failure",
            details=details,
            error_message=str(error)
        )
