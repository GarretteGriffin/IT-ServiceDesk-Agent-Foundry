"""
Active Directory Tools - Safe operations built on PowerShell integration

This tool layer:
- Validates inputs
- Wraps PowerShellExecutor with domain logic
- Normalizes outputs
- Raises structured errors
"""

from typing import Dict, Any, List, Optional
import re
from ..integrations.powershell import PowerShellExecutor
from ..core.models import AgentError


class ActiveDirectoryTools:
    """
    Active Directory operations via PowerShell
    
    All operations validate inputs and normalize outputs.
    Caller is responsible for authorization checks.
    """
    
    def __init__(self, ps_executor: PowerShellExecutor, domain: str):
        """
        Initialize AD tools
        
        Args:
            ps_executor: PowerShellExecutor instance
            domain: AD domain name
        """
        self._ps = ps_executor
        self._domain = domain
    
    def _validate_username(self, username: str) -> str:
        """Validate and normalize username"""
        # Strip whitespace
        username = username.strip()
        
        # Basic validation
        if not username:
            raise ValueError("Username cannot be empty")
        
        # Remove domain suffix if present
        if "@" in username:
            username = username.split("@")[0]
        
        # Validate format (alphanumeric, dots, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9._-]+$", username):
            raise ValueError(f"Invalid username format: {username}")
        
        return username
    
    async def get_user_info(
        self,
        username: str,
        include_groups: bool = False
    ) -> Dict[str, Any]:
        """
        Get user information from Active Directory
        
        Args:
            username: Username or email
            include_groups: Whether to include group memberships
        
        Returns:
            User details dict
        
        Raises:
            ValueError: Invalid username
            RuntimeError: PowerShell execution failed
        """
        username = self._validate_username(username)
        
        # Build PowerShell command
        ps_command = f"""
Import-Module ActiveDirectory
try {{
    $user = Get-ADUser -Identity '{username}' -Properties DisplayName,EmailAddress,Enabled,LockedOut,PasswordExpired,PasswordLastSet,LastLogonDate,Department,Title,Manager
    
    $result = @{{
        samAccountName = $user.SamAccountName
        userPrincipalName = $user.UserPrincipalName
        displayName = $user.DisplayName
        emailAddress = $user.EmailAddress
        enabled = $user.Enabled
        lockedOut = $user.LockedOut
        passwordExpired = $user.PasswordExpired
        passwordLastSet = if($user.PasswordLastSet) {{ $user.PasswordLastSet.ToString('yyyy-MM-dd HH:mm:ss') }} else {{ $null }}
        lastLogonDate = if($user.LastLogonDate) {{ $user.LastLogonDate.ToString('yyyy-MM-dd HH:mm:ss') }} else {{ $null }}
        department = $user.Department
        title = $user.Title
        manager = if($user.Manager) {{ (Get-ADUser $user.Manager).DisplayName }} else {{ $null }}
    }}
    
    if ({str(include_groups).lower()}) {{
        $groups = Get-ADPrincipalGroupMembership -Identity '{username}' | Select-Object -ExpandProperty Name
        $result.groups = $groups
    }}
    
    $result | ConvertTo-Json -Compress
}} catch {{
    Write-Error $_.Exception.Message
    exit 1
}}
"""
        
        output = await self._ps.run_command(ps_command)
        
        # Parse JSON output
        import json
        return json.loads(output)
    
    async def reset_password(
        self,
        username: str,
        temporary_password: str,
        must_change: bool = True
    ) -> Dict[str, Any]:
        """
        Reset user password
        
        Args:
            username: Username
            temporary_password: New temporary password
            must_change: Require password change at next logon
        
        Returns:
            Success message
        
        Raises:
            ValueError: Invalid input
            RuntimeError: Operation failed
        """
        username = self._validate_username(username)
        
        if len(temporary_password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        ps_command = f"""
Import-Module ActiveDirectory
try {{
    $securePassword = ConvertTo-SecureString '{temporary_password}' -AsPlainText -Force
    Set-ADAccountPassword -Identity '{username}' -Reset -NewPassword $securePassword
    Set-ADUser -Identity '{username}' -ChangePasswordAtLogon ${str(must_change).lower()}
    
    @{{
        success = $true
        username = '{username}'
        message = 'Password reset successfully'
        mustChangeAtLogon = ${str(must_change).lower()}
    }} | ConvertTo-Json -Compress
}} catch {{
    Write-Error $_.Exception.Message
    exit 1
}}
"""
        
        output = await self._ps.run_command(ps_command)
        import json
        return json.loads(output)
    
    async def unlock_account(self, username: str) -> Dict[str, Any]:
        """
        Unlock user account
        
        Args:
            username: Username
        
        Returns:
            Success message
        """
        username = self._validate_username(username)
        
        ps_command = f"""
Import-Module ActiveDirectory
try {{
    Unlock-ADAccount -Identity '{username}'
    $user = Get-ADUser -Identity '{username}' -Properties LockedOut
    
    @{{
        success = $true
        username = '{username}'
        lockedOut = $user.LockedOut
        message = 'Account unlocked successfully'
    }} | ConvertTo-Json -Compress
}} catch {{
    Write-Error $_.Exception.Message
    exit 1
}}
"""
        
        output = await self._ps.run_command(ps_command)
        import json
        return json.loads(output)
    
    async def get_user_computers(self, username: str) -> List[Dict[str, Any]]:
        """
        Get computers associated with user
        
        Args:
            username: Username
        
        Returns:
            List of computer details
        """
        username = self._validate_username(username)
        
        ps_command = f"""
Import-Module ActiveDirectory
try {{
    $computers = Get-ADComputer -Filter "ManagedBy -eq '(Get-ADUser '{username}').DistinguishedName'" -Properties Name,OperatingSystem,LastLogonDate
    
    $computers | ForEach-Object {{
        @{{
            name = $_.Name
            operatingSystem = $_.OperatingSystem
            lastLogonDate = if($_.LastLogonDate) {{ $_.LastLogonDate.ToString('yyyy-MM-dd HH:mm:ss') }} else {{ $null }}
        }}
    }} | ConvertTo-Json -Compress
}} catch {{
    Write-Error $_.Exception.Message
    exit 1
}}
"""
        
        output = await self._ps.run_command(ps_command)
        import json
        result = json.loads(output)
        
        # Ensure result is a list
        if isinstance(result, dict):
            return [result]
        return result if result else []
    
    async def get_laps_password(self, computer_name: str) -> Dict[str, Any]:
        """
        Get LAPS password for computer (HIGHLY SENSITIVE)
        
        Args:
            computer_name: Computer name
        
        Returns:
            LAPS password and expiration
        
        Note:
            Caller MUST enforce authorization before calling this.
            This is a high-risk operation requiring approval.
        """
        computer_name = computer_name.strip().upper()
        
        ps_command = f"""
Import-Module ActiveDirectory
try {{
    $computer = Get-ADComputer -Identity '{computer_name}' -Properties ms-Mcs-AdmPwd,ms-Mcs-AdmPwdExpirationTime
    
    @{{
        computerName = $computer.Name
        password = $computer.'ms-Mcs-AdmPwd'
        expirationTime = if($computer.'ms-Mcs-AdmPwdExpirationTime') {{ 
            [DateTime]::FromFileTime($computer.'ms-Mcs-AdmPwdExpirationTime').ToString('yyyy-MM-dd HH:mm:ss')
        }} else {{ $null }}
    }} | ConvertTo-Json -Compress
}} catch {{
    Write-Error $_.Exception.Message
    exit 1
}}
"""
        
        output = await self._ps.run_command(ps_command)
        import json
        return json.loads(output)
    
    async def get_bitlocker_recovery_key(self, computer_name: str) -> Dict[str, Any]:
        """
        Get BitLocker recovery key (SENSITIVE)
        
        Args:
            computer_name: Computer name
        
        Returns:
            BitLocker recovery key
        
        Note:
            Caller MUST enforce authorization before calling this.
            This is a high-risk operation requiring approval.
        """
        computer_name = computer_name.strip().upper()
        
        ps_command = f"""
Import-Module ActiveDirectory
try {{
    $computer = Get-ADComputer -Identity '{computer_name}'
    $recoveryInfo = Get-ADObject -Filter {{objectClass -eq 'msFVE-RecoveryInformation'}} -SearchBase $computer.DistinguishedName -Properties msFVE-RecoveryPassword,whenCreated
    
    $recoveryInfo | Select-Object -First 1 | ForEach-Object {{
        @{{
            computerName = '{computer_name}'
            recoveryPassword = $_.'msFVE-RecoveryPassword'
            created = $_.whenCreated.ToString('yyyy-MM-dd HH:mm:ss')
        }}
    }} | ConvertTo-Json -Compress
}} catch {{
    Write-Error $_.Exception.Message
    exit 1
}}
"""
        
        output = await self._ps.run_command(ps_command)
        import json
        return json.loads(output)
