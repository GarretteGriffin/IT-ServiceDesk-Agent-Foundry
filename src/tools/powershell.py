"""
PowerShell Execution Tool
Execute PowerShell scripts for Exchange, networking, file servers, and complex operations
"""

from typing import Annotated, List, Dict, Any, Optional
import asyncio
from datetime import datetime

from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class PowerShellTool:
    """
    PowerShell script execution tool for complex IT operations
    
    Capabilities:
    - Exchange Online operations (mailbox, distribution lists, calendar)
    - Network diagnostics (ping, traceroute, DNS, port testing)
    - File server management (shares, permissions, quotas)
    - Bulk Active Directory operations
    - Service management (start/stop/restart remote services)
    - Log analysis (event logs, IIS logs, custom logs)
    """
    
    def __init__(self):
        self.automation_account = settings.AUTOMATION_ACCOUNT_NAME
        self.resource_group = settings.AUTOMATION_RESOURCE_GROUP
        logger.info("Initialized PowerShell execution tool")
    
    def get_functions(self) -> List[callable]:
        """Return list of tool functions for agent"""
        return [
            self.execute_exchange_command,
            self.network_diagnostics,
            self.manage_file_share,
            self.check_service_status,
            self.restart_remote_service,
            self.analyze_event_logs,
            self.get_disk_space,
            self.test_connectivity,
        ]
    
    async def execute_exchange_command(
        self,
        command: Annotated[str, "Exchange Online PowerShell command to execute"],
        mailbox: Annotated[Optional[str], "Target mailbox identity"] = None,
    ) -> str:
        """
        Execute Exchange Online PowerShell command.
        
        Examples:
        - Get mailbox info: "Get-Mailbox -Identity user@company.com"
        - Get mailbox permissions: "Get-MailboxPermission -Identity user@company.com"
        - Add calendar permissions: "Add-MailboxFolderPermission"
        """
        logger.info(f"Executing Exchange command: {command[:50]}...")
        
        try:
            # Sanitize and validate command
            if not self._is_safe_command(command):
                return "❌ Command rejected: Contains unsafe operations"
            
            script = f"""
# Connect to Exchange Online
Connect-ExchangeOnline -CertificateThumbPrint $env:CERT_THUMBPRINT -AppID $env:APP_ID -Organization $env:ORGANIZATION

try {{
    # Execute command
    {command}
    
    # Log for audit
    Write-Output "`n[AUDIT] Command executed successfully at $(Get-Date)"
    
}} finally {{
    Disconnect-ExchangeOnline -Confirm:$false
}}
"""
            
            result = await self._execute_via_automation(script, "ExchangeOnline")
            
            return f"Exchange command executed:\n{result}"
            
        except Exception as e:
            logger.error(f"Error executing Exchange command: {e}")
            return f"Failed to execute Exchange command: {str(e)}"
    
    async def network_diagnostics(
        self,
        target: Annotated[str, "Target hostname or IP address"],
        diagnostics: Annotated[List[str], "List of diagnostics to run: ping, traceroute, dns, port_test"] = ["ping", "dns"],
    ) -> str:
        """
        Run comprehensive network diagnostics on a target host.
        
        Available diagnostics:
        - ping: ICMP connectivity test
        - traceroute: Path tracing
        - dns: DNS resolution and records
        - port_test: Common port connectivity (80, 443, 3389, 445)
        """
        logger.info(f"Running network diagnostics for: {target}")
        
        try:
            script = f"""
$target = '{target}'
$results = @()

# Ping test
if ('{diagnostics}' -like '*ping*') {{
    $pingResult = Test-Connection -ComputerName $target -Count 4 -ErrorAction SilentlyContinue
    if ($pingResult) {{
        $avgLatency = ($pingResult | Measure-Object -Property ResponseTime -Average).Average
        $results += "✓ Ping: Success (Avg latency: ${{avgLatency}}ms)"
    }} else {{
        $results += "✗ Ping: Failed (Host unreachable)"
    }}
}}

# DNS test
if ('{diagnostics}' -like '*dns*') {{
    try {{
        $dnsResult = Resolve-DnsName -Name $target -ErrorAction Stop
        $ipAddresses = $dnsResult | Where-Object {{$_.Type -eq 'A'}} | Select-Object -ExpandProperty IPAddress
        $results += "✓ DNS: Resolved to $($ipAddresses -join ', ')"
    }} catch {{
        $results += "✗ DNS: Resolution failed"
    }}
}}

# Traceroute
if ('{diagnostics}' -like '*traceroute*') {{
    $traceResult = Test-NetConnection -ComputerName $target -TraceRoute -ErrorAction SilentlyContinue
    if ($traceResult) {{
        $hops = $traceResult.TraceRoute -join ' → '
        $results += "✓ Traceroute: $hops"
    }}
}}

# Port test
if ('{diagnostics}' -like '*port_test*') {{
    $ports = @(80, 443, 3389, 445, 22)
    foreach ($port in $ports) {{
        $portTest = Test-NetConnection -ComputerName $target -Port $port -WarningAction SilentlyContinue
        if ($portTest.TcpTestSucceeded) {{
            $results += "✓ Port $port`: Open"
        }} else {{
            $results += "✗ Port $port`: Closed"
        }}
    }}
}}

$results -join "`n"
"""
            
            result = await self._execute_via_automation(script, "Network")
            
            return f"Network diagnostics for {target}:\n\n{result}"
            
        except Exception as e:
            logger.error(f"Error running network diagnostics: {e}")
            return f"Failed to run diagnostics: {str(e)}"
    
    async def manage_file_share(
        self,
        server: Annotated[str, "File server name"],
        action: Annotated[str, "Action: list, create, remove, permissions"],
        share_name: Annotated[Optional[str], "Share name (for create/remove/permissions)"] = None,
        path: Annotated[Optional[str], "Local path for new share"] = None,
    ) -> str:
        """
        Manage file shares on a file server.
        
        Actions:
        - list: List all shares on server
        - create: Create new share
        - remove: Remove share
        - permissions: View share permissions
        """
        logger.info(f"File share action '{action}' on {server}")
        
        try:
            if action == "list":
                script = f"""
Get-SmbShare -CimSession '{server}' | 
    Select-Object Name, Path, Description, ShareState, CurrentUsers |
    Format-Table -AutoSize | Out-String
"""
            
            elif action == "create":
                if not share_name or not path:
                    return "❌ share_name and path required for create action"
                
                script = f"""
New-SmbShare -Name '{share_name}' -Path '{path}' -CimSession '{server}' -FullAccess 'Domain Admins'
Write-Output "✓ Share '{share_name}' created at {path}"
"""
            
            elif action == "permissions":
                if not share_name:
                    return "❌ share_name required for permissions action"
                
                script = f"""
Get-SmbShareAccess -Name '{share_name}' -CimSession '{server}' |
    Format-Table -AutoSize | Out-String
"""
            
            else:
                return f"❌ Unknown action: {action}"
            
            result = await self._execute_via_automation(script, "FileServer")
            
            return f"File share {action} on {server}:\n{result}"
            
        except Exception as e:
            logger.error(f"Error managing file share: {e}")
            return f"Failed to manage file share: {str(e)}"
    
    async def check_service_status(
        self,
        computer: Annotated[str, "Computer name"],
        service_name: Annotated[str, "Service name to check"],
    ) -> str:
        """Check status of a Windows service on remote computer."""
        logger.info(f"Checking service '{service_name}' on {computer}")
        
        try:
            script = f"""
$service = Get-Service -Name '{service_name}' -ComputerName '{computer}' -ErrorAction Stop
$result = @{{
    Name = $service.Name
    DisplayName = $service.DisplayName
    Status = $service.Status
    StartType = $service.StartType
}}

$result | Format-List | Out-String
"""
            
            result = await self._execute_via_automation(script, "ServiceManagement")
            
            return f"Service status:\n{result}"
            
        except Exception as e:
            logger.error(f"Error checking service: {e}")
            return f"Failed to check service: {str(e)}"
    
    async def restart_remote_service(
        self,
        computer: Annotated[str, "Computer name"],
        service_name: Annotated[str, "Service name to restart"],
        force: Annotated[bool, "Force restart even if dependent services exist"] = False,
    ) -> str:
        """Restart a Windows service on remote computer."""
        logger.info(f"Restarting service '{service_name}' on {computer}")
        
        try:
            force_flag = "-Force" if force else ""
            
            script = f"""
$service = Get-Service -Name '{service_name}' -ComputerName '{computer}'
$initialStatus = $service.Status

Write-Output "Current status: $initialStatus"
Write-Output "Restarting service..."

Restart-Service -Name '{service_name}' -ComputerName '{computer}' {force_flag} -ErrorAction Stop

Start-Sleep -Seconds 5

$service = Get-Service -Name '{service_name}' -ComputerName '{computer}'
Write-Output "New status: $($service.Status)"

if ($service.Status -eq 'Running') {{
    Write-Output "✓ Service restarted successfully"
}} else {{
    Write-Output "⚠ Service status: $($service.Status)"
}}
"""
            
            result = await self._execute_via_automation(script, "ServiceManagement")
            
            # Audit log
            logger.warning(f"Service '{service_name}' restarted on {computer}")
            
            return f"Service restart:\n{result}"
            
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            return f"Failed to restart service: {str(e)}"
    
    async def analyze_event_logs(
        self,
        computer: Annotated[str, "Computer name"],
        log_name: Annotated[str, "Log name: System, Application, Security"],
        level: Annotated[str, "Level: Error, Warning, Information"] = "Error",
        hours: Annotated[int, "Hours of history to analyze"] = 24,
    ) -> str:
        """Analyze Windows Event Logs for issues."""
        logger.info(f"Analyzing {log_name} logs on {computer}")
        
        try:
            script = f"""
$startTime = (Get-Date).AddHours(-{hours})
$events = Get-WinEvent -ComputerName '{computer}' -FilterHashtable @{{
    LogName = '{log_name}'
    Level = [System.Diagnostics.Eventing.Reader.StandardEventLevel]::{level}
    StartTime = $startTime
}} -MaxEvents 50 -ErrorAction Stop

$summary = $events | Group-Object Id | Sort-Object Count -Descending | Select-Object -First 10 Name, Count

Write-Output "Top 10 Event IDs (last {hours} hours):"
$summary | Format-Table -AutoSize | Out-String

Write-Output "`nRecent Events:"
$events | Select-Object -First 5 TimeCreated, Id, Message | Format-List | Out-String
"""
            
            result = await self._execute_via_automation(script, "EventLogs")
            
            return f"Event log analysis for {computer}:\n{result}"
            
        except Exception as e:
            logger.error(f"Error analyzing event logs: {e}")
            return f"Failed to analyze logs: {str(e)}"
    
    async def get_disk_space(
        self,
        computer: Annotated[str, "Computer name"],
        threshold_percent: Annotated[int, "Alert threshold percentage"] = 10,
    ) -> str:
        """Check disk space on remote computer."""
        logger.info(f"Checking disk space on {computer}")
        
        try:
            script = f"""
$disks = Get-CimInstance -ClassName Win32_LogicalDisk -ComputerName '{computer}' -Filter "DriveType=3"

foreach ($disk in $disks) {{
    $freePercent = [math]::Round(($disk.FreeSpace / $disk.Size) * 100, 2)
    $freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
    $sizeGB = [math]::Round($disk.Size / 1GB, 2)
    
    $status = if ($freePercent -lt {threshold_percent}) {{ "⚠ LOW" }} else {{ "✓ OK" }}
    
    Write-Output "$($disk.DeviceID) - $status - $freeGB GB free of $sizeGB GB ($freePercent%)"
}}
"""
            
            result = await self._execute_via_automation(script, "DiskSpace")
            
            return f"Disk space on {computer}:\n{result}"
            
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return f"Failed to check disk space: {str(e)}"
    
    async def test_connectivity(
        self,
        source: Annotated[str, "Source computer"],
        destination: Annotated[str, "Destination host"],
        port: Annotated[int, "Port number to test"],
    ) -> str:
        """Test network connectivity from source to destination on specific port."""
        logger.info(f"Testing connectivity from {source} to {destination}:{port}")
        
        try:
            script = f"""
$result = Invoke-Command -ComputerName '{source}' -ScriptBlock {{
    param($dest, $p)
    Test-NetConnection -ComputerName $dest -Port $p
}} -ArgumentList '{destination}', {port}

$status = if ($result.TcpTestSucceeded) {{ "✓ OPEN" }} else {{ "✗ CLOSED" }}

Write-Output "Connection test: $status"
Write-Output "Source: {source}"
Write-Output "Destination: {destination}:{port}"
Write-Output "Result: $($result.TcpTestSucceeded)"
if ($result.PingSucceeded) {{
    Write-Output "Ping: Success"
}}
"""
            
            result = await self._execute_via_automation(script, "Network")
            
            return f"Connectivity test:\n{result}"
            
        except Exception as e:
            logger.error(f"Error testing connectivity: {e}")
            return f"Failed to test connectivity: {str(e)}"
    
    def _is_safe_command(self, command: str) -> bool:
        """Validate command safety - prevent dangerous operations"""
        dangerous_keywords = [
            "remove-item", "rm ", "del ", "format-",
            "remove-mailbox", "remove-distributiongroup",
            "disable-mailbox", "set-mailbox -deleteditem"
        ]
        
        command_lower = command.lower()
        return not any(keyword in command_lower for keyword in dangerous_keywords)
    
    async def _execute_via_automation(self, script: str, runbook_name: str) -> str:
        """
        Execute PowerShell script via Azure Automation
        
        In production:
        1. Call Azure Automation API to start runbook
        2. Pass script as parameter
        3. Poll for completion
        4. Return output
        5. Log execution for audit trail
        """
        # Placeholder - in production use Azure Automation API
        await asyncio.sleep(0.2)  # Simulate API call
        
        return f"PowerShell execution completed via Azure Automation (runbook: {runbook_name})"
