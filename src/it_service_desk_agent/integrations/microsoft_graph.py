"""Microsoft Graph API client - thin wrapper over base HTTP client"""

from typing import Dict, Any, Optional, List
from azure.identity.aio import ClientSecretCredential
from .base_http import HttpIntegrationClient


class MicrosoftGraphClient(HttpIntegrationClient):
    """
    Microsoft Graph API client
    
    Handles:
    - OAuth token acquisition via azure-identity
    - Common Graph API operations
    - No business logic - just API calls
    """
    
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        base_url: str = "https://graph.microsoft.com/v1.0"
    ):
        """
        Initialize Graph client
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: App registration client ID
            client_secret: App registration secret
            base_url: Graph API base URL (defaults to v1.0)
        """
        # Get OAuth token
        self._credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Initialize base client (we'll add token to headers on each request)
        super().__init__(
            base_url=base_url,
            headers={"Content-Type": "application/json"}
        )
        
        self._tenant_id = tenant_id
    
    async def _get_token(self) -> str:
        """Get OAuth access token"""
        token = await self._credential.get_token("https://graph.microsoft.com/.default")
        return token.token
    
    async def _request(self, method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Override to add bearer token"""
        token = await self._get_token()
        
        # Add authorization header
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["Authorization"] = f"Bearer {token}"
        
        result = await super()._request(method, url, **kwargs)
        
        # Handle paged responses
        if isinstance(result, dict) and "value" in result:
            return result["value"]
        
        return result
    
    # User operations
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by UPN or object ID"""
        return await self._request("GET", f"/users/{user_id}")
    
    async def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's group memberships"""
        return await self._request("GET", f"/users/{user_id}/memberOf")
    
    async def get_user_licenses(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's assigned licenses"""
        return await self._request("GET", f"/users/{user_id}/licenseDetails")
    
    # License operations
    async def assign_license(self, user_id: str, sku_id: str) -> Dict[str, Any]:
        """Assign license to user"""
        data = {
            "addLicenses": [{"skuId": sku_id}],
            "removeLicenses": []
        }
        return await self._request("POST", f"/users/{user_id}/assignLicense", json=data)
    
    async def remove_license(self, user_id: str, sku_id: str) -> Dict[str, Any]:
        """Remove license from user"""
        data = {
            "addLicenses": [],
            "removeLicenses": [sku_id]
        }
        return await self._request("POST", f"/users/{user_id}/assignLicense", json=data)
    
    # Group operations
    async def get_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """Get group members"""
        return await self._request("GET", f"/groups/{group_id}/members")
    
    async def add_group_member(self, group_id: str, user_id: str) -> Dict[str, Any]:
        """Add user to group"""
        data = {
            "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"
        }
        return await self._request("POST", f"/groups/{group_id}/members/$ref", json=data)
    
    # Device operations (for Intune)
    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get managed device info"""
        return await self._request("GET", f"/deviceManagement/managedDevices/{device_id}")
    
    async def list_devices(self, filter_query: Optional[str] = None, top: int = 50) -> List[Dict[str, Any]]:
        """List managed devices"""
        params = {"$top": top}
        if filter_query:
            params["$filter"] = filter_query
        return await self._request("GET", "/deviceManagement/managedDevices", params=params)
    
    async def sync_device(self, device_id: str) -> Dict[str, Any]:
        """Trigger device sync"""
        return await self._request("POST", f"/deviceManagement/managedDevices/{device_id}/syncDevice")
    
    async def restart_device(self, device_id: str) -> Dict[str, Any]:
        """Restart device remotely"""
        return await self._request("POST", f"/deviceManagement/managedDevices/{device_id}/rebootNow")
    
    async def wipe_device(self, device_id: str) -> Dict[str, Any]:
        """Wipe device (DESTRUCTIVE)"""
        return await self._request("POST", f"/deviceManagement/managedDevices/{device_id}/wipe")
