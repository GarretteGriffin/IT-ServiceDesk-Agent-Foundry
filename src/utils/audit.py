"""
Audit logging module for sensitive IT operations
Structured logging for compliance and security review
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from src.utils.logging import get_logger

logger = get_logger(__name__)


class OperationType(Enum):
    """Classification of operations by risk level"""
    READ_ONLY = "read_only"              # Safe queries, no state change
    MODIFY_USER = "modify_user"          # User account changes
    MODIFY_DEVICE = "modify_device"      # Device configuration changes
    CREDENTIAL_ACCESS = "credential_access"  # LAPS, Bitlocker, passwords
    DESTRUCTIVE = "destructive"          # Wipes, deletions, resets
    PRIVILEGE_ESCALATION = "privilege_escalation"  # Role/permission changes


class AuditLogger:
    """
    Centralized audit logging for all sensitive IT operations
    
    Provides structured logging with:
    - Operation classification (read/modify/destructive)
    - User context (who requested the operation)
    - Target resource (what was affected)
    - Outcome (success/failure)
    - Justification (why it was done)
    """
    
    @staticmethod
    def log_operation(
        operation_type: OperationType,
        action: str,
        target: str,
        user: Optional[str] = None,
        outcome: str = "success",
        justification: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a sensitive operation for audit trail
        
        Args:
            operation_type: Classification of operation risk
            action: Specific action taken (e.g., "reset_password", "retrieve_laps")
            target: Resource affected (e.g., "user:jsmith", "computer:DESKTOP-001")
            user: Who requested the operation (service principal or user)
            outcome: "success", "failure", "pending"
            justification: Business reason for the operation
            metadata: Additional context (tool used, parameters, etc.)
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation_type": operation_type.value,
            "action": action,
            "target": target,
            "user": user or "system",
            "outcome": outcome,
            "justification": justification,
            "metadata": metadata or {},
        }
        
        # Use structured logging for easy parsing
        log_message = f"AUDIT: {action} on {target} by {user or 'system'} - {outcome}"
        
        if operation_type in [OperationType.CREDENTIAL_ACCESS, OperationType.DESTRUCTIVE, OperationType.PRIVILEGE_ESCALATION]:
            # Critical operations - always log as WARNING for visibility
            logger.warning(
                log_message,
                extra={"audit": audit_entry, "sensitive": True}
            )
        else:
            # Standard operations - INFO level
            logger.info(
                log_message,
                extra={"audit": audit_entry}
            )
    
    @staticmethod
    def log_credential_access(action: str, target: str, user: Optional[str] = None, justification: Optional[str] = None):
        """Convenience method for credential access (LAPS, Bitlocker, passwords)"""
        AuditLogger.log_operation(
            operation_type=OperationType.CREDENTIAL_ACCESS,
            action=action,
            target=target,
            user=user,
            justification=justification or "No justification provided - REVIEW REQUIRED",
        )
    
    @staticmethod
    def log_destructive_action(action: str, target: str, user: Optional[str] = None, justification: Optional[str] = None):
        """Convenience method for destructive operations (wipes, deletions)"""
        AuditLogger.log_operation(
            operation_type=OperationType.DESTRUCTIVE,
            action=action,
            target=target,
            user=user,
            justification=justification or "No justification provided - REVIEW REQUIRED",
        )
    
    @staticmethod
    def log_privilege_change(action: str, target: str, user: Optional[str] = None, justification: Optional[str] = None):
        """Convenience method for privilege escalation (role assignments, group adds)"""
        AuditLogger.log_operation(
            operation_type=OperationType.PRIVILEGE_ESCALATION,
            action=action,
            target=target,
            user=user,
            justification=justification or "No justification provided - REVIEW REQUIRED",
        )
