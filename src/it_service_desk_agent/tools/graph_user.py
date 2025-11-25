"""
Microsoft Graph User Tools - Safe operations built on Graph integration

This tool layer:
- Validates inputs
- Wraps MicrosoftGraphClient with domain logic
- Normalizes outputs
- Provides user-friendly abstractions
"""

from typing import Dict, Any, List, Optional
import re
from ..integrations.microsoft_graph import MicrosoftGraphClient


class GraphUserTools:
    """
    Microsoft Graph operations for user management
    
    All operations validate inputs and normalize outputs.
    Caller is responsible for authorization checks.
    """
    
    def __init__(self, graph_client: MicrosoftGraphClient):
        """
        Initialize Graph user tools
        
        Args:
            graph_client: MicrosoftGraphClient instance
        """
        self._graph = graph_client
    
    def _validate_upn(self, upn: str) -> str:
        """Validate user principal name (email format)"""
        upn = upn.strip().lower()
        
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", upn):
            raise ValueError(f"Invalid email format: {upn}")
        
        return upn
    
    async def get_user_profile(
        self,
        upn: str,
        include_groups: bool = False,
        include_licenses: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive user profile from Azure AD
        
        Args:
            upn: User principal name (email)
            include_groups: Include group memberships
            include_licenses: Include license details
        
        Returns:
            User profile dict with normalized fields
        """
        upn = self._validate_upn(upn)
        
        # Get base user info
        user = await self._graph.get_user(upn)
        
        result = {
            "upn": user.get("userPrincipalName"),
            "display_name": user.get("displayName"),
            "email": user.get("mail"),
            "job_title": user.get("jobTitle"),
            "department": user.get("department"),
            "office_location": user.get("officeLocation"),
            "mobile_phone": user.get("mobilePhone"),
            "business_phones": user.get("businessPhones", []),
            "account_enabled": user.get("accountEnabled"),
            "id": user.get("id")
        }
        
        # Optionally get groups
        if include_groups:
            groups = await self._graph.get_user_groups(upn)
            result["groups"] = [
                {
                    "id": g.get("id"),
                    "display_name": g.get("displayName"),
                    "mail": g.get("mail")
                }
                for g in groups
            ]
        
        # Optionally get licenses
        if include_licenses:
            licenses = await self._graph.get_user_licenses(upn)
            result["licenses"] = [
                {
                    "sku_id": lic.get("skuId"),
                    "sku_part_number": lic.get("skuPartNumber")
                }
                for lic in licenses
            ]
        
        return result
    
    async def get_user_groups(self, upn: str) -> List[Dict[str, Any]]:
        """
        Get user's group memberships
        
        Args:
            upn: User principal name
        
        Returns:
            List of groups with details
        """
        upn = self._validate_upn(upn)
        groups = await self._graph.get_user_groups(upn)
        
        return [
            {
                "id": g.get("id"),
                "display_name": g.get("displayName"),
                "description": g.get("description"),
                "mail": g.get("mail"),
                "security_enabled": g.get("securityEnabled", False)
            }
            for g in groups
        ]
    
    async def get_user_licenses(self, upn: str) -> List[Dict[str, Any]]:
        """
        Get user's license assignments
        
        Args:
            upn: User principal name
        
        Returns:
            List of licenses with friendly names
        """
        upn = self._validate_upn(upn)
        licenses = await self._graph.get_user_licenses(upn)
        
        # Map SKU part numbers to friendly names
        sku_names = {
            "SPE_E3": "Microsoft 365 E3",
            "SPE_E5": "Microsoft 365 E5",
            "ENTERPRISEPACK": "Office 365 E3",
            "ENTERPRISEPREMIUM": "Office 365 E5",
            "POWER_BI_PRO": "Power BI Pro",
            "PROJECTPROFESSIONAL": "Project Plan 3",
            "VISIOCLIENT": "Visio Plan 2",
        }
        
        return [
            {
                "sku_id": lic.get("skuId"),
                "sku_part_number": lic.get("skuPartNumber"),
                "friendly_name": sku_names.get(lic.get("skuPartNumber"), lic.get("skuPartNumber"))
            }
            for lic in licenses
        ]
    
    async def assign_license(self, upn: str, sku_id: str) -> Dict[str, Any]:
        """
        Assign license to user
        
        Args:
            upn: User principal name
            sku_id: SKU ID to assign
        
        Returns:
            Success confirmation
        
        Note:
            Caller MUST enforce authorization before calling this.
        """
        upn = self._validate_upn(upn)
        
        await self._graph.assign_license(upn, sku_id)
        
        return {
            "success": True,
            "upn": upn,
            "sku_id": sku_id,
            "message": "License assigned successfully"
        }
    
    async def remove_license(self, upn: str, sku_id: str) -> Dict[str, Any]:
        """
        Remove license from user
        
        Args:
            upn: User principal name
            sku_id: SKU ID to remove
        
        Returns:
            Success confirmation
        
        Note:
            Caller MUST enforce authorization before calling this.
        """
        upn = self._validate_upn(upn)
        
        await self._graph.remove_license(upn, sku_id)
        
        return {
            "success": True,
            "upn": upn,
            "sku_id": sku_id,
            "message": "License removed successfully"
        }
    
    async def add_to_group(self, upn: str, group_id: str) -> Dict[str, Any]:
        """
        Add user to group
        
        Args:
            upn: User principal name
            group_id: Group object ID
        
        Returns:
            Success confirmation
        
        Note:
            Caller MUST enforce authorization before calling this.
        """
        upn = self._validate_upn(upn)
        
        # Get user ID
        user = await self._graph.get_user(upn)
        user_id = user.get("id")
        
        await self._graph.add_group_member(group_id, user_id)
        
        return {
            "success": True,
            "upn": upn,
            "group_id": group_id,
            "message": "User added to group successfully"
        }
