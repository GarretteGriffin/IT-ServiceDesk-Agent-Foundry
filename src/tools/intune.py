"""
Microsoft Intune Integration Tool
Device management, compliance, and endpoint security
"""

from typing import Annotated, List, Dict, Any, Optional
import asyncio
from datetime import datetime

from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class IntuneTool:
    """
    Microsoft Intune/Endpoint Manager integration
    
    Capabilities:
    - Device inventory and information
    - Compliance policy status
    - Remote actions (wipe, sync, restart)
    - Application deployment
    - Configuration profile management
    - Security baseline queries
    """
    
    def __init__(self):
        self.tenant_id = settings.GRAPH_TENANT_ID
        logger.info(f"Initialized Intune tool for tenant: {self.tenant_id}")
    
    def get_functions(self) -> List[callable]:
        """Return list of tool functions for agent"""
        return [
            self.get_device_info,
            self.list_devices,
            self.check_compliance,
            self.sync_device,
            self.remote_wipe,
            self.restart_device,
            self.get_installed_apps,
            self.deploy_application,
        ]
    
    async def get_device_info(
        self,
        device_name: Annotated[str, "Device name or ID"],
        include_compliance: Annotated[bool, "Include compliance status"] = True,
        include_apps: Annotated[bool, "Include installed apps"] = False,
    ) -> str:
        """Get comprehensive device information from Intune."""
        logger.info(f"Getting device info for: {device_name}")
        
        try:
            # Search for device
            device = await self._intune_call("GET", f"/deviceManagement/managedDevices?$filter=deviceName eq '{device_name}'")
            
            if not device:
                return f"Device not found: {device_name}"
            
            device = device[0]
            
            result = [
                f"Device Information for {device['deviceName']}:",
                f"\nBasic Details:",
                f"  Device ID: {device['id']}",
                f"  Serial Number: {device['serialNumber']}",
                f"  Manufacturer: {device['manufacturer']}",
                f"  Model: {device['model']}",
                f"  OS: {device['operatingSystem']} {device['osVersion']}",
                f"  Enrolled: {device['enrolledDateTime']}",
                f"  Last Sync: {device['lastSyncDateTime']}",
                f"  Management State: {device['managementState']}",
                f"  Ownership: {device['managedDeviceOwnerType']}",
            ]
            
            # User information
            if device.get('userPrincipalName'):
                result.append(f"\nUser:")
                result.append(f"  Primary User: {device['userPrincipalName']}")
                result.append(f"  User Display Name: {device.get('userDisplayName', 'N/A')}")
            
            # Compliance status
            if include_compliance:
                compliance = device.get('complianceState', 'unknown')
                compliance_icon = "✓" if compliance == "compliant" else "✗"
                result.append(f"\nCompliance:")
                result.append(f"  {compliance_icon} Status: {compliance}")
            
            # Installed apps
            if include_apps:
                apps = await self._intune_call("GET", f"/deviceManagement/managedDevices/{device['id']}/detectedApps")
                if apps:
                    result.append(f"\nInstalled Apps ({len(apps)}):")
                    for app in apps[:10]:
                        result.append(f"  • {app['displayName']} ({app.get('version', 'unknown')})")
                    if len(apps) > 10:
                        result.append(f"  ... and {len(apps) - 10} more")
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return f"Failed to get device info: {str(e)}"
    
    async def list_devices(
        self,
        filter_type: Annotated[Optional[str], "Filter: all, windows, ios, android, macos"] = "all",
        managed_by: Annotated[Optional[str], "Filter by user email"] = None,
        limit: Annotated[int, "Maximum devices to return"] = 25,
    ) -> str:
        """List Intune managed devices with filters."""
        logger.info(f"Listing devices (filter: {filter_type}, user: {managed_by})")
        
        try:
            # Build filter
            filters = []
            if filter_type != "all":
                os_map = {
                    "windows": "Windows",
                    "ios": "iOS",
                    "android": "Android",
                    "macos": "macOS",
                }
                if filter_type in os_map:
                    filters.append(f"operatingSystem eq '{os_map[filter_type]}'")
            
            if managed_by:
                filters.append(f"userPrincipalName eq '{managed_by}'")
            
            filter_string = " and ".join(filters) if filters else None
            
            # Query devices
            endpoint = f"/deviceManagement/managedDevices?$top={limit}"
            if filter_string:
                endpoint += f"&$filter={filter_string}"
            
            devices = await self._intune_call("GET", endpoint)
            
            if not devices:
                return f"No devices found matching criteria"
            
            result = [f"Found {len(devices)} device(s):\n"]
            for device in devices:
                compliance_icon = "✓" if device.get('complianceState') == "compliant" else "✗"
                result.append(
                    f"{compliance_icon} {device['deviceName']}\n"
                    f"   User: {device.get('userPrincipalName', 'Unassigned')}\n"
                    f"   OS: {device['operatingSystem']} {device.get('osVersion', '')}\n"
                    f"   Last Sync: {device.get('lastSyncDateTime', 'Never')}\n"
                )
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return f"Failed to list devices: {str(e)}"
    
    async def check_compliance(
        self,
        device_name: Annotated[str, "Device name or ID"],
    ) -> str:
        """Check device compliance status and policy violations."""
        logger.info(f"Checking compliance for: {device_name}")
        
        try:
            # Get device
            device = await self._intune_call("GET", f"/deviceManagement/managedDevices?$filter=deviceName eq '{device_name}'")
            
            if not device:
                return f"Device not found: {device_name}"
            
            device = device[0]
            device_id = device['id']
            
            # Get compliance policies
            policies = await self._intune_call("GET", f"/deviceManagement/managedDevices/{device_id}/deviceCompliancePolicyStates")
            
            compliance_state = device.get('complianceState', 'unknown')
            
            result = [
                f"Compliance Status for {device['deviceName']}:",
                f"\nOverall Status: {compliance_state.upper()}",
            ]
            
            if policies:
                result.append(f"\nPolicy Compliance ({len(policies)} policies):")
                for policy in policies:
                    status_icon = "✓" if policy['state'] == "compliant" else "✗"
                    result.append(
                        f"{status_icon} {policy['displayName']}\n"
                        f"   State: {policy['state']}\n"
                        f"   Version: {policy.get('version', 'N/A')}"
                    )
            
            # Get non-compliant settings
            if compliance_state != "compliant":
                result.append(f"\n⚠ Device is non-compliant. Review policies above.")
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            return f"Failed to check compliance: {str(e)}"
    
    async def sync_device(
        self,
        device_name: Annotated[str, "Device name or ID"],
    ) -> str:
        """Force Intune device sync to apply policies and get latest state."""
        logger.info(f"Syncing device: {device_name}")
        
        try:
            # Get device
            device = await self._intune_call("GET", f"/deviceManagement/managedDevices?$filter=deviceName eq '{device_name}'")
            
            if not device:
                return f"Device not found: {device_name}"
            
            device_id = device[0]['id']
            
            # Trigger sync
            await self._intune_call("POST", f"/deviceManagement/managedDevices/{device_id}/syncDevice")
            
            # Audit log
            logger.info(f"Triggered sync for device {device_name}")
            
            return (
                f"✓ Device sync initiated\n\n"
                f"Device: {device_name}\n"
                f"Action: Sync with Intune\n\n"
                f"The device will check in with Intune and apply any pending policies.\n"
                f"This may take a few minutes to complete."
            )
            
        except Exception as e:
            logger.error(f"Error syncing device: {e}")
            return f"Failed to sync device: {str(e)}"
    
    async def remote_wipe(
        self,
        device_name: Annotated[str, "Device name or ID"],
        wipe_type: Annotated[str, "Wipe type: selective (remove company data) or full (factory reset)"] = "selective",
    ) -> str:
        """Perform remote wipe on a device. Use selective to keep personal data."""
        logger.info(f"Remote wipe requested for {device_name} (type: {wipe_type})")
        
        try:
            # Get device
            device = await self._intune_call("GET", f"/deviceManagement/managedDevices?$filter=deviceName eq '{device_name}'")
            
            if not device:
                return f"Device not found: {device_name}"
            
            device_id = device[0]['id']
            
            # Trigger wipe
            if wipe_type.lower() == "full":
                await self._intune_call("POST", f"/deviceManagement/managedDevices/{device_id}/wipe")
                action = "Full factory reset"
            else:
                await self._intune_call("POST", f"/deviceManagement/managedDevices/{device_id}/retire")
                action = "Selective wipe (company data only)"
            
            # Audit log - CRITICAL operation
            logger.warning(f"REMOTE WIPE INITIATED: {device_name} ({wipe_type})")
            
            return (
                f"⚠ Remote wipe initiated\n\n"
                f"Device: {device_name}\n"
                f"Action: {action}\n\n"
                f"This action cannot be undone. The device will be wiped on next check-in."
            )
            
        except Exception as e:
            logger.error(f"Error performing remote wipe: {e}")
            return f"Failed to perform remote wipe: {str(e)}"
    
    async def restart_device(
        self,
        device_name: Annotated[str, "Device name or ID"],
    ) -> str:
        """Restart a remote device."""
        logger.info(f"Restart requested for device: {device_name}")
        
        try:
            # Get device
            device = await self._intune_call("GET", f"/deviceManagement/managedDevices?$filter=deviceName eq '{device_name}'")
            
            if not device:
                return f"Device not found: {device_name}"
            
            device_id = device[0]['id']
            
            # Trigger restart
            await self._intune_call("POST", f"/deviceManagement/managedDevices/{device_id}/rebootNow")
            
            # Audit log
            logger.info(f"Triggered restart for device {device_name}")
            
            return (
                f"✓ Device restart initiated\n\n"
                f"Device: {device_name}\n"
                f"Action: Remote restart\n\n"
                f"The device will restart immediately if online."
            )
            
        except Exception as e:
            logger.error(f"Error restarting device: {e}")
            return f"Failed to restart device: {str(e)}"
    
    async def get_installed_apps(
        self,
        device_name: Annotated[str, "Device name or ID"],
        limit: Annotated[int, "Maximum apps to return"] = 50,
    ) -> str:
        """Get list of applications installed on a device."""
        logger.info(f"Getting installed apps for: {device_name}")
        
        try:
            # Get device
            device = await self._intune_call("GET", f"/deviceManagement/managedDevices?$filter=deviceName eq '{device_name}'")
            
            if not device:
                return f"Device not found: {device_name}"
            
            device_id = device[0]['id']
            
            # Get installed apps
            apps = await self._intune_call("GET", f"/deviceManagement/managedDevices/{device_id}/detectedApps?$top={limit}")
            
            if not apps:
                return f"No installed apps found for {device_name}"
            
            result = [f"Installed Applications on {device_name} ({len(apps)}):\n"]
            for app in apps:
                result.append(
                    f"📦 {app['displayName']}\n"
                    f"   Version: {app.get('version', 'Unknown')}\n"
                    f"   Publisher: {app.get('publisher', 'Unknown')}\n"
                    f"   Size: {app.get('sizeInByte', 0) / 1024 / 1024:.1f} MB"
                )
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error getting installed apps: {e}")
            return f"Failed to get installed apps: {str(e)}"
    
    async def deploy_application(
        self,
        device_name: Annotated[str, "Device name or ID"],
        app_name: Annotated[str, "Application name to deploy"],
    ) -> str:
        """Deploy an application to a device from Intune app catalog."""
        logger.info(f"Deploying app {app_name} to {device_name}")
        
        try:
            # Get device
            device = await self._intune_call("GET", f"/deviceManagement/managedDevices?$filter=deviceName eq '{device_name}'")
            
            if not device:
                return f"Device not found: {device_name}"
            
            device_id = device[0]['id']
            
            # Search for app
            apps = await self._intune_call("GET", f"/deviceAppManagement/mobileApps?$filter=displayName eq '{app_name}'")
            
            if not apps:
                return f"Application not found in Intune: {app_name}"
            
            app_id = apps[0]['id']
            
            # Create assignment
            data = {
                "mobileAppAssignments": [
                    {
                        "target": {
                            "@odata.type": "#microsoft.graph.allDevicesAssignmentTarget"
                        },
                        "intent": "required"
                    }
                ]
            }
            
            await self._intune_call("POST", f"/deviceAppManagement/mobileApps/{app_id}/assignments", data=data)
            
            # Trigger sync to apply immediately
            await self._intune_call("POST", f"/deviceManagement/managedDevices/{device_id}/syncDevice")
            
            # Audit log
            logger.info(f"Deployed app {app_name} to device {device_name}")
            
            return (
                f"✓ Application deployment initiated\n\n"
                f"Device: {device_name}\n"
                f"Application: {app_name}\n"
                f"Action: Required installation\n\n"
                f"The app will be installed on next device check-in (sync triggered)."
            )
            
        except Exception as e:
            logger.error(f"Error deploying application: {e}")
            return f"Failed to deploy application: {str(e)}"
    
    async def _intune_call(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        """Make Intune API call via Microsoft Graph."""
        # Placeholder - in production use actual Graph API
        await asyncio.sleep(0.1)
        
        # Simulate responses
        if "/managedDevices?" in endpoint and method == "GET":
            return [{
                "id": "device123",
                "deviceName": "LAPTOP-001",
                "serialNumber": "SN12345",
                "manufacturer": "Dell",
                "model": "Latitude 5420",
                "operatingSystem": "Windows",
                "osVersion": "10.0.22631",
                "enrolledDateTime": "2025-01-15T10:00:00Z",
                "lastSyncDateTime": "2025-11-24T09:00:00Z",
                "managementState": "managed",
                "managedDeviceOwnerType": "company",
                "userPrincipalName": "jsmith@company.com",
                "userDisplayName": "John Smith",
                "complianceState": "compliant",
            }]
        elif "/deviceCompliancePolicyStates" in endpoint:
            return [{
                "displayName": "Windows 10 Security Baseline",
                "state": "compliant",
                "version": "1.0",
            }]
        elif "/detectedApps" in endpoint:
            return [
                {"displayName": "Microsoft Office 365", "version": "16.0.17328", "publisher": "Microsoft", "sizeInByte": 2147483648},
                {"displayName": "Google Chrome", "version": "120.0.6099", "publisher": "Google", "sizeInByte": 314572800},
            ]
        elif "/mobileApps?" in endpoint and method == "GET":
            return [{"id": "app123", "displayName": "Microsoft Teams"}]
        elif method == "POST":
            return {"success": True}
        
        return []
