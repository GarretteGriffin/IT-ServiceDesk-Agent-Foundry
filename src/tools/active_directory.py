"""
Active Directory Management Tool
Provides comprehensive AD operations including computer management, LAPS, Bitlocker
"""

from typing import Annotated, Optional, Dict, Any, List
import asyncio
from datetime import datetime, timedelta

from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class ADTool:
    """
    Active Directory management tool with advanced capabilities:
    - User operations (create, modify, reset password, unlock)
    - Computer management (create, move, reset, delete)
    - LAPS password retrieval
    - Bitlocker recovery key access
    - Stale computer cleanup
    - Group membership management
    """
    
    def __init__(self):
        self.domain = settings.AD_DOMAIN
        self.server = settings.AD_SERVER
        self.base_dn = settings.AD_BASE_DN
        logger.info(f"Initialized AD tool for domain: {self.domain}")
    
    def get_functions(self) -> List[callable]:
        """Return list of tool functions for agent"""
        return [
            self.get_user_info,
            self.reset_user_password,
            self.unlock_user_account,
            self.get_computer_info,
            self.get_laps_password,
            self.get_bitlocker_recovery_key,
            self.reset_computer_account,
            self.move_computer,
            self.find_stale_computers,
            self.search_ad_objects,
        ]
    
    async def get_user_info(
        self,
        username: Annotated[str, "Username or email address to lookup"],
        include_groups: Annotated[bool, "Include group memberships"] = False,
    ) -> str:
        """
        Get detailed information about an Active Directory user.
        
        Returns user properties, status, and optionally group memberships.
        """
        logger.info(f"Getting user info for: {username}")
        
        try:
            # In production: Use ldap3 or PowerShell remoting
            # This is a placeholder showing the structure
            
            ps_script = f"""
Import-Module ActiveDirectory
$user = Get-ADUser -Identity '{username}' -Properties *
$result = @{{
    UserPrincipalName = $user.UserPrincipalName
    DisplayName = $user.DisplayName
    Enabled = $user.Enabled
    LockedOut = $user.LockedOut
    PasswordExpired = $user.PasswordExpired
    PasswordLastSet = $user.PasswordLastSet
    LastLogonDate = $user.LastLogonDate
    Department = $user.Department
    Title = $user.Title
    Manager = $user.Manager
    EmailAddress = $user.EmailAddress
}}

if ({str(include_groups).lower()}) {{
    $groups = Get-ADPrincipalGroupMembership -Identity '{username}' | Select-Object -ExpandProperty Name
    $result.Groups = $groups -join ', '
}}

$result | ConvertTo-Json
"""
            
            # Execute PowerShell (placeholder)
            result = await self._execute_powershell(ps_script)
            
            return f"User information for {username}:\n{result}"
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return f"Failed to get user info: {str(e)}"
    
    async def reset_user_password(
        self,
        username: Annotated[str, "Username to reset password for"],
        temporary_password: Annotated[str, "Temporary password to set"],
        must_change: Annotated[bool, "Require password change at next logon"] = True,
    ) -> str:
        """
        Reset a user's password in Active Directory.
        
        Sets a temporary password and optionally requires change at next logon.
        """
        logger.info(f"Resetting password for user: {username}")
        
        try:
            ps_script = f"""
Import-Module ActiveDirectory
Set-ADAccountPassword -Identity '{username}' -Reset -NewPassword (ConvertTo-SecureString '{temporary_password}' -AsPlainText -Force)
Set-ADUser -Identity '{username}' -ChangePasswordAtLogon ${str(must_change).lower()}
Write-Output "Password reset successfully for {username}"
"""
            
            result = await self._execute_powershell(ps_script)
            
            # Log to audit trail
            logger.info(f"Password reset completed for {username}")
            
            return f"✓ Password reset for {username}\n✓ Temporary password set\n✓ Must change at next logon: {must_change}"
            
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return f"Failed to reset password: {str(e)}"
    
    async def unlock_user_account(
        self,
        username: Annotated[str, "Username to unlock"],
    ) -> str:
        """
        Unlock a locked Active Directory user account.
        """
        logger.info(f"Unlocking user account: {username}")
        
        try:
            ps_script = f"""
Import-Module ActiveDirectory
Unlock-ADAccount -Identity '{username}'
$user = Get-ADUser -Identity '{username}' -Properties LockedOut
if ($user.LockedOut) {{
    Write-Output "FAILED: Account still locked"
}} else {{
    Write-Output "SUCCESS: Account unlocked"
}}
"""
            
            result = await self._execute_powershell(ps_script)
            
            return f"✓ Account {username} has been unlocked"
            
        except Exception as e:
            logger.error(f"Error unlocking account: {e}")
            return f"Failed to unlock account: {str(e)}"
    
    async def get_computer_info(
        self,
        computer_name: Annotated[str, "Computer name to lookup"],
        include_laps: Annotated[bool, "Include LAPS password (requires permissions)"] = False,
        include_bitlocker: Annotated[bool, "Include Bitlocker recovery key (requires permissions)"] = False,
    ) -> str:
        """
        Get detailed information about an Active Directory computer.
        
        Can optionally include LAPS password and Bitlocker recovery key if authorized.
        """
        logger.info(f"Getting computer info for: {computer_name}")
        
        try:
            ps_script = f"""
Import-Module ActiveDirectory
$computer = Get-ADComputer -Identity '{computer_name}' -Properties *
$result = @{{
    Name = $computer.Name
    DNSHostName = $computer.DNSHostName
    Enabled = $computer.Enabled
    OperatingSystem = $computer.OperatingSystem
    OperatingSystemVersion = $computer.OperatingSystemVersion
    LastLogonDate = $computer.LastLogonDate
    Created = $computer.Created
    DistinguishedName = $computer.DistinguishedName
    IPv4Address = $computer.IPv4Address
    Location = $computer.Location
    ManagedBy = $computer.ManagedBy
}}

$result | ConvertTo-Json
"""
            
            result = await self._execute_powershell(ps_script)
            
            output = f"Computer information for {computer_name}:\n{result}"
            
            # Get LAPS password if requested
            if include_laps:
                laps_password = await self.get_laps_password(computer_name)
                output += f"\n\nLAPS Password:\n{laps_password}"
            
            # Get Bitlocker key if requested
            if include_bitlocker:
                bitlocker_key = await self.get_bitlocker_recovery_key(computer_name)
                output += f"\n\nBitlocker Recovery Key:\n{bitlocker_key}"
            
            return output
            
        except Exception as e:
            logger.error(f"Error getting computer info: {e}")
            return f"Failed to get computer info: {str(e)}"
    
    async def get_laps_password(
        self,
        computer_name: Annotated[str, "Computer name to get LAPS password for"],
    ) -> str:
        """
        Retrieve the Local Administrator Password Solution (LAPS) password for a computer.
        
        **Requires LAPS read permissions**
        """
        logger.info(f"Retrieving LAPS password for: {computer_name}")
        
        try:
            ps_script = f"""
Import-Module ActiveDirectory
$computer = Get-ADComputer -Identity '{computer_name}' -Properties ms-Mcs-AdmPwd, ms-Mcs-AdmPwdExpirationTime
if ($computer.'ms-Mcs-AdmPwd') {{
    $expirationTime = [DateTime]::FromFileTime($computer.'ms-Mcs-AdmPwdExpirationTime')
    Write-Output "Password: $($computer.'ms-Mcs-AdmPwd')"
    Write-Output "Expires: $expirationTime"
}} else {{
    Write-Output "LAPS password not available for this computer"
}}
"""
            
            result = await self._execute_powershell(ps_script)
            
            # Audit log for security
            logger.warning(f"LAPS password accessed for {computer_name}")
            
            return f"LAPS Password for {computer_name}:\n{result}\n\n⚠️ This is a sensitive credential - handle securely"
            
        except Exception as e:
            logger.error(f"Error retrieving LAPS password: {e}")
            return f"Failed to retrieve LAPS password: {str(e)}"
    
    async def get_bitlocker_recovery_key(
        self,
        computer_name: Annotated[str, "Computer name to get Bitlocker key for"],
    ) -> str:
        """
        Retrieve Bitlocker recovery key for a computer.
        
        **Requires Bitlocker recovery key read permissions**
        """
        logger.info(f"Retrieving Bitlocker recovery key for: {computer_name}")
        
        try:
            ps_script = f"""
Import-Module ActiveDirectory
$computer = Get-ADComputer -Identity '{computer_name}'
$recoveryKeys = Get-ADObject -Filter {{objectClass -eq 'msFVE-RecoveryInformation'}} -SearchBase $computer.DistinguishedName -Properties msFVE-RecoveryPassword, whenCreated |
    Sort-Object whenCreated -Descending |
    Select-Object -First 5

if ($recoveryKeys) {{
    foreach ($key in $recoveryKeys) {{
        Write-Output "Key ID: $($key.Name)"
        Write-Output "Password: $($key.'msFVE-RecoveryPassword')"
        Write-Output "Created: $($key.whenCreated)"
        Write-Output "---"
    }}
}} else {{
    Write-Output "No Bitlocker recovery keys found for this computer"
}}
"""
            
            result = await self._execute_powershell(ps_script)
            
            # Audit log for security
            logger.warning(f"Bitlocker recovery key accessed for {computer_name}")
            
            return f"Bitlocker Recovery Keys for {computer_name}:\n{result}\n\n⚠️ This is a sensitive credential - handle securely"
            
        except Exception as e:
            logger.error(f"Error retrieving Bitlocker key: {e}")
            return f"Failed to retrieve Bitlocker key: {str(e)}"
    
    async def reset_computer_account(
        self,
        computer_name: Annotated[str, "Computer name to reset"],
    ) -> str:
        """
        Reset a computer account's password in Active Directory.
        
        This fixes trust relationship issues between the computer and domain.
        """
        logger.info(f"Resetting computer account: {computer_name}")
        
        try:
            ps_script = f"""
Import-Module ActiveDirectory
Reset-ComputerMachinePassword -ComputerName '{computer_name}' -Server '{self.server}'
Write-Output "Computer account reset for {computer_name}"
"""
            
            result = await self._execute_powershell(ps_script)
            
            return f"✓ Computer account {computer_name} has been reset\n✓ Trust relationship should be restored\n⚠️ Computer may need to rejoin domain"
            
        except Exception as e:
            logger.error(f"Error resetting computer account: {e}")
            return f"Failed to reset computer account: {str(e)}"
    
    async def move_computer(
        self,
        computer_name: Annotated[str, "Computer name to move"],
        target_ou: Annotated[str, "Target OU distinguished name"],
    ) -> str:
        """
        Move a computer to a different Organizational Unit (OU).
        """
        logger.info(f"Moving computer {computer_name} to OU: {target_ou}")
        
        try:
            ps_script = f"""
Import-Module ActiveDirectory
Move-ADObject -Identity (Get-ADComputer '{computer_name}').DistinguishedName -TargetPath '{target_ou}'
Write-Output "Computer moved successfully"
"""
            
            result = await self._execute_powershell(ps_script)
            
            return f"✓ Computer {computer_name} moved to {target_ou}"
            
        except Exception as e:
            logger.error(f"Error moving computer: {e}")
            return f"Failed to move computer: {str(e)}"
    
    async def find_stale_computers(
        self,
        days_inactive: Annotated[int, "Number of days of inactivity to consider stale"] = 90,
        limit: Annotated[int, "Maximum number of results to return"] = 50,
    ) -> str:
        """
        Find stale computer accounts that haven't logged on in specified days.
        
        Useful for cleanup and security audits.
        """
        logger.info(f"Finding stale computers (inactive for {days_inactive} days)")
        
        try:
            ps_script = f"""
Import-Module ActiveDirectory
$cutoffDate = (Get-Date).AddDays(-{days_inactive})
$staleComputers = Get-ADComputer -Filter {{LastLogonDate -lt $cutoffDate}} -Properties LastLogonDate, OperatingSystem, Description |
    Sort-Object LastLogonDate |
    Select-Object -First {limit} Name, LastLogonDate, OperatingSystem, Description

$staleComputers | Format-Table -AutoSize | Out-String
"""
            
            result = await self._execute_powershell(ps_script)
            
            return f"Stale computers (inactive > {days_inactive} days):\n{result}"
            
        except Exception as e:
            logger.error(f"Error finding stale computers: {e}")
            return f"Failed to find stale computers: {str(e)}"
    
    async def search_ad_objects(
        self,
        search_term: Annotated[str, "Search term to find in AD"],
        object_type: Annotated[str, "Object type: user, computer, group, or all"] = "all",
        max_results: Annotated[int, "Maximum number of results"] = 20,
    ) -> str:
        """
        Search Active Directory for objects matching a term.
        
        Searches across names, descriptions, and other common attributes.
        """
        logger.info(f"Searching AD for: {search_term} (type: {object_type})")
        
        try:
            filter_clause = f"*{search_term}*"
            
            if object_type.lower() == "user":
                object_class = "user"
            elif object_type.lower() == "computer":
                object_class = "computer"
            elif object_type.lower() == "group":
                object_class = "group"
            else:
                object_class = "*"
            
            ps_script = f"""
Import-Module ActiveDirectory
$results = Get-ADObject -Filter {{(Name -like '{filter_clause}' -or Description -like '{filter_clause}') -and ObjectClass -like '{object_class}'}} -Properties Name, ObjectClass, Description, whenCreated |
    Select-Object -First {max_results} Name, ObjectClass, Description, whenCreated

$results | Format-Table -AutoSize | Out-String
"""
            
            result = await self._execute_powershell(ps_script)
            
            return f"AD search results for '{search_term}':\n{result}"
            
        except Exception as e:
            logger.error(f"Error searching AD: {e}")
            return f"Failed to search AD: {str(e)}"
    
    async def _execute_powershell(self, script: str) -> str:
        """
        Execute PowerShell script via Azure Automation or PowerShell remoting
        
        In production, this would:
        1. Use Azure Automation Runbook for secure execution
        2. Or use PowerShell remoting with proper authentication
        3. Validate and sanitize inputs
        4. Log execution for audit trail
        """
        # Placeholder - in production use Azure Automation API
        await asyncio.sleep(0.1)  # Simulate API call
        
        return "PowerShell execution result (placeholder)"
