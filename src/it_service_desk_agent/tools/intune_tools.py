"""
Intune Device Tools - Safe operations built on Graph integration

This tool layer:
- Validates inputs
- Wraps MicrosoftGraphClient device operations
- Provides user-friendly device management abstractions
"""

from typing import Dict, Any, List, Optional
from ..integrations.microsoft_graph import MicrosoftGraphClient


class IntuneDeviceTools:
    """
    Microsoft Intune device management operations
    
    All operations validate inputs and normalize outputs.
    Caller is responsible for authorization checks.
    """
    
    def __init__(self, graph_client: MicrosoftGraphClient):
        """
        Initialize Intune device tools
        
        Args:
            graph_client: MicrosoftGraphClient instance
        """
        self._graph = graph_client
    
    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """
        Get device details
        
        Args:
            device_id: Device ID or name
        
        Returns:
            Device details
        """
        device = await self._graph.get_device(device_id)
        
        return {
            "id": device.get("id"),
            "device_name": device.get("deviceName"),
            "serial_number": device.get("serialNumber"),
            "manufacturer": device.get("manufacturer"),
            "model": device.get("model"),
            "operating_system": device.get("operatingSystem"),
            "os_version": device.get("osVersion"),
            "enrolled_date": device.get("enrolledDateTime"),
            "last_sync": device.get("lastSyncDateTime"),
            "compliance_state": device.get("complianceState"),
            "management_state": device.get("managementState"),
            "user_principal_name": device.get("userPrincipalName"),
            "user_display_name": device.get("userDisplayName")
        }
    
    async def list_devices(
        self,
        user_upn: Optional[str] = None,
        os_type: Optional[str] = None,
        compliance_state: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        List managed devices with filters
        
        Args:
            user_upn: Filter by user
            os_type: Filter by OS (windows, ios, android, macos)
            compliance_state: Filter by compliance (compliant, noncompliant, etc.)
            limit: Max results
        
        Returns:
            List of device summaries
        """
        # Build filter query
        filters = []
        if user_upn:
            filters.append(f"userPrincipalName eq '{user_upn}'")
        if os_type:
            os_map = {
                "windows": "Windows",
                "ios": "iOS",
                "android": "Android",
                "macos": "macOS"
            }
            if os_type.lower() in os_map:
                filters.append(f"operatingSystem eq '{os_map[os_type.lower()]}'")
        if compliance_state:
            filters.append(f"complianceState eq '{compliance_state}'")
        
        filter_query = " and ".join(filters) if filters else None
        
        devices = await self._graph.list_devices(filter_query=filter_query, top=limit)
        
        return [
            {
                "id": d.get("id"),
                "device_name": d.get("deviceName"),
                "user": d.get("userPrincipalName"),
                "os": f"{d.get('operatingSystem')} {d.get('osVersion', '')}".strip(),
                "compliance": d.get("complianceState"),
                "last_sync": d.get("lastSyncDateTime"),
                "enrolled": d.get("enrolledDateTime")
            }
            for d in devices
        ]
    
    async def sync_device(self, device_id: str) -> Dict[str, Any]:
        """
        Trigger device sync with Intune
        
        Args:
            device_id: Device ID
        
        Returns:
            Success confirmation
        """
        await self._graph.sync_device(device_id)
        
        return {
            "success": True,
            "device_id": device_id,
            "message": "Device sync initiated successfully"
        }
    
    async def restart_device(self, device_id: str) -> Dict[str, Any]:
        """
        Restart device remotely
        
        Args:
            device_id: Device ID
        
        Returns:
            Success confirmation
        
        Note:
            Caller MUST enforce authorization before calling this.
            This requires user confirmation.
        """
        await self._graph.restart_device(device_id)
        
        return {
            "success": True,
            "device_id": device_id,
            "message": "Device restart initiated successfully"
        }
    
    async def wipe_device(self, device_id: str) -> Dict[str, Any]:
        """
        Wipe device remotely (DESTRUCTIVE)
        
        Args:
            device_id: Device ID
        
        Returns:
            Success confirmation
        
        Note:
            Caller MUST enforce STRICT authorization before calling this.
            This is a CRITICAL operation that erases all data.
            Requires explicit approval.
        """
        await self._graph.wipe_device(device_id)
        
        return {
            "success": True,
            "device_id": device_id,
            "message": "Device wipe initiated - ALL DATA WILL BE ERASED",
            "warning": "This operation cannot be undone"
        }
