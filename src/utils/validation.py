"""
Input validation and sanitization for agent tools
Prevents injection attacks and validates parameters
"""

import re
from typing import Any, Optional
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class InputValidator:
    """
    Centralized input validation for all agent tools
    
    Validates and sanitizes user inputs to prevent:
    - Command injection
    - Path traversal
    - SQL injection
    - LDAP injection
    - Script injection
    """
    
    # Dangerous patterns that should never appear in inputs
    DANGEROUS_PATTERNS = [
        r'[;&|`$]',  # Command injection characters
        r'\.\./|\.\.\\',  # Path traversal
        r'<script',  # Script injection
        r'DROP\s+TABLE',  # SQL injection
        r'DELETE\s+FROM',  # SQL injection
        r'\$\(',  # Command substitution
        r'Invoke-Expression',  # PowerShell injection
        r'iex\s',  # PowerShell injection short form
    ]
    
    # Valid patterns for common inputs
    USERNAME_PATTERN = r'^[a-zA-Z0-9._-]+@?[a-zA-Z0-9._-]*$'
    COMPUTER_NAME_PATTERN = r'^[a-zA-Z0-9][a-zA-Z0-9\-]{0,14}$'
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    UPN_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate and sanitize a username"""
        if not username or not isinstance(username, str):
            raise ValidationError("Username is required and must be a string")
        
        username = username.strip()
        
        if len(username) > 256:
            raise ValidationError("Username too long (max 256 characters)")
        
        if not re.match(InputValidator.USERNAME_PATTERN, username):
            raise ValidationError(f"Invalid username format: {username}")
        
        return username
    
    @staticmethod
    def validate_computer_name(computer_name: str) -> str:
        """Validate and sanitize a computer name"""
        if not computer_name or not isinstance(computer_name, str):
            raise ValidationError("Computer name is required and must be a string")
        
        computer_name = computer_name.strip().upper()
        
        if not re.match(InputValidator.COMPUTER_NAME_PATTERN, computer_name):
            raise ValidationError(f"Invalid computer name format: {computer_name}")
        
        return computer_name
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize an email address"""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required and must be a string")
        
        email = email.strip().lower()
        
        if not re.match(InputValidator.EMAIL_PATTERN, email):
            raise ValidationError(f"Invalid email format: {email}")
        
        return email
    
    @staticmethod
    def validate_upn(upn: str) -> str:
        """Validate and sanitize a User Principal Name"""
        if not upn or not isinstance(upn, str):
            raise ValidationError("UPN is required and must be a string")
        
        upn = upn.strip().lower()
        
        if not re.match(InputValidator.UPN_PATTERN, upn):
            raise ValidationError(f"Invalid UPN format: {upn}")
        
        return upn
    
    @staticmethod
    def check_dangerous_patterns(text: str, context: str = "input") -> None:
        """
        Check for dangerous patterns that could indicate injection attempts
        
        Raises ValidationError if dangerous patterns detected
        """
        if not text or not isinstance(text, str):
            return
        
        for pattern in InputValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.error(f"Dangerous pattern detected in {context}: {pattern}")
                raise ValidationError(f"Input contains dangerous pattern - potential injection attack")
    
    @staticmethod
    def validate_powershell_command(command: str) -> str:
        """
        Validate PowerShell command for safety
        
        Blocks dangerous cmdlets and patterns
        """
        if not command or not isinstance(command, str):
            raise ValidationError("PowerShell command is required and must be a string")
        
        command = command.strip()
        
        # Check for dangerous patterns
        InputValidator.check_dangerous_patterns(command, "PowerShell command")
        
        # Block dangerous PowerShell cmdlets
        dangerous_cmdlets = [
            r'Remove-Item',
            r'\brm\b',
            r'\bdel\b',
            r'Format-',
            r'Clear-',
            r'Remove-Computer',
            r'Restart-Computer',
            r'Stop-Computer',
            r'Invoke-Command',
            r'Invoke-Expression',
            r'iex\s',
            r'Invoke-WebRequest.*\|.*iex',
        ]
        
        for cmdlet in dangerous_cmdlets:
            if re.search(cmdlet, command, re.IGNORECASE):
                raise ValidationError(f"Dangerous PowerShell cmdlet blocked: {cmdlet}")
        
        return command
    
    @staticmethod
    def validate_integer(value: Any, min_val: Optional[int] = None, max_val: Optional[int] = None, name: str = "value") -> int:
        """Validate and convert to integer with optional range checking"""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{name} must be an integer")
        
        if min_val is not None and int_value < min_val:
            raise ValidationError(f"{name} must be >= {min_val}")
        
        if max_val is not None and int_value > max_val:
            raise ValidationError(f"{name} must be <= {max_val}")
        
        return int_value
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Sanitize a search query for safe use in APIs"""
        if not query or not isinstance(query, str):
            raise ValidationError("Search query is required and must be a string")
        
        query = query.strip()
        
        if len(query) > 500:
            raise ValidationError("Search query too long (max 500 characters)")
        
        # Check for dangerous patterns
        InputValidator.check_dangerous_patterns(query, "search query")
        
        return query
