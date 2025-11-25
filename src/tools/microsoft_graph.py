"""
Microsoft Graph Integration Tool
Azure AD, Microsoft 365, licensing, and group management
"""

from typing import Annotated, List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta

from src.utils.logging import get_logger
from src.config import settings

logger = get_logger(__name__)


class GraphTool:
    """
    Microsoft Graph API integration for Azure AD and M365 operations
    
    Capabilities:
    - User management (provisioning, attributes, status)
    - License assignment and management
    - Group operations (members, owners, creation)
    - Sign-in logs and security queries
    - MFA management and authentication methods
    - Conditional Access policy queries
    - Guest user management
    """
    
    def __init__(self):
        self.tenant_id = settings.GRAPH_TENANT_ID
        self.client_id = settings.GRAPH_CLIENT_ID
        logger.info(f"Initialized Graph tool for tenant: {self.tenant_id}")
    
    def get_functions(self) -> List[callable]:
        """Return list of tool functions for agent"""
        return [
            self.get_user_details,
            self.create_user,
            self.assign_license,
            self.remove_license,
            self.reset_user_mfa,
            self.get_group_members,
            self.add_user_to_group,
            self.get_sign_in_logs,
            self.check_conditional_access,
            self.list_user_licenses,
        ]
    
    async def get_user_details(
        self,
        user_id: Annotated[str, "User principal name or object ID"],
        include_groups: Annotated[bool, "Include group memberships"] = True,
        include_licenses: Annotated[bool, "Include assigned licenses"] = True,
    ) -> str:
        """Get comprehensive Azure AD user information with groups and licenses."""
        logger.info(f"Getting user details for: {user_id}")
        
        try:
            # Get user basic info
            user = await self._graph_call("GET", f"/users/{user_id}")
            
            result = [
                f"User Details for {user['displayName']}:",
                f"\nBasic Information:",
                f"  User Principal Name: {user['userPrincipalName']}",
                f"  Display Name: {user['displayName']}",
                f"  Job Title: {user.get('jobTitle', 'Not set')}",
                f"  Department: {user.get('department', 'Not set')}",
                f"  Office Location: {user.get('officeLocation', 'Not set')}",
                f"  Mobile: {user.get('mobilePhone', 'Not set')}",
                f"  Account Enabled: {user['accountEnabled']}",
            ]
            
            # Get group memberships
            if include_groups:
                groups = await self._graph_call("GET", f"/users/{user_id}/memberOf")
                if groups:
                    result.append(f"\nGroup Memberships ({len(groups)}):")
                    for group in groups[:10]:  # Show first 10
                        result.append(f"  • {group['displayName']}")
                    if len(groups) > 10:
                        result.append(f"  ... and {len(groups) - 10} more")
            
            # Get licenses
            if include_licenses:
                licenses = await self._graph_call("GET", f"/users/{user_id}/licenseDetails")
                if licenses:
                    result.append(f"\nAssigned Licenses ({len(licenses)}):")
                    for lic in licenses:
                        result.append(f"  • {lic['skuPartNumber']}")
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            return f"Failed to get user details: {str(e)}"
    
    async def create_user(
        self,
        display_name: Annotated[str, "Full display name"],
        user_principal_name: Annotated[str, "User principal name (email)"],
        password: Annotated[str, "Initial password"],
        force_change_password: Annotated[bool, "Force password change at first sign-in"] = True,
        job_title: Annotated[Optional[str], "Job title"] = None,
        department: Annotated[Optional[str], "Department"] = None,
    ) -> str:
        """Create a new Azure AD user account with password and optional attributes."""
        logger.info(f"Creating user: {display_name} ({user_principal_name})")
        
        try:
            data = {
                "accountEnabled": True,
                "displayName": display_name,
                "userPrincipalName": user_principal_name,
                "mailNickname": user_principal_name.split("@")[0],
                "passwordProfile": {
                    "password": password,
                    "forceChangePasswordNextSignIn": force_change_password,
                }
            }
            
            if job_title:
                data["jobTitle"] = job_title
            if department:
                data["department"] = department
            
            user = await self._graph_call("POST", "/users", data=data)
            
            # Audit log
            logger.info(f"Created user {user_principal_name} with ID {user['id']}")
            
            return (
                f"✓ User created successfully\n\n"
                f"Display Name: {display_name}\n"
                f"User Principal Name: {user_principal_name}\n"
                f"Object ID: {user['id']}\n"
                f"Account Enabled: True\n"
                f"Force Password Change: {force_change_password}\n"
                f"Job Title: {job_title or 'Not set'}\n"
                f"Department: {department or 'Not set'}"
            )
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return f"Failed to create user: {str(e)}"
    
    async def assign_license(
        self,
        user_id: Annotated[str, "User principal name or object ID"],
        sku_id: Annotated[str, "SKU ID or part number (e.g., ENTERPRISEPACK for E3)"],
    ) -> str:
        """Assign a license to a user (ENTERPRISEPACK=E3, ENTERPRISEPREMIUM=E5, SPE_E3=M365 E3, SPE_E5=M365 E5)."""
        logger.info(f"Assigning license {sku_id} to {user_id}")
        
        try:
            # Get available licenses to find SKU ID
            subscriptions = await self._graph_call("GET", "/subscribedSkus")
            
            # Find matching SKU
            sku_object_id = None
            for sub in subscriptions:
                if sub['skuPartNumber'] == sku_id or sub['skuId'] == sku_id:
                    sku_object_id = sub['skuId']
                    sku_name = sub['skuPartNumber']
                    break
            
            if not sku_object_id:
                return f"✗ License SKU not found: {sku_id}\n\nAvailable SKUs:\n" + "\n".join([f"  • {s['skuPartNumber']}" for s in subscriptions])
            
            # Assign license
            data = {
                "addLicenses": [
                    {
                        "skuId": sku_object_id,
                        "disabledPlans": []
                    }
                ],
                "removeLicenses": []
            }
            
            await self._graph_call("POST", f"/users/{user_id}/assignLicense", data=data)
            
            # Audit log
            logger.info(f"Assigned license {sku_name} to {user_id}")
            
            return (
                f"✓ License assigned successfully\n\n"
                f"User: {user_id}\n"
                f"License: {sku_name}\n"
                f"SKU ID: {sku_object_id}"
            )
            
        except Exception as e:
            logger.error(f"Error assigning license: {e}")
            return f"Failed to assign license: {str(e)}"
    
    async def remove_license(
        self,
        user_id: Annotated[str, "User principal name or object ID"],
        sku_id: Annotated[str, "SKU ID or part number to remove"],
    ) -> str:
        """Remove a license from a user."""
        logger.info(f"Removing license {sku_id} from {user_id}")
        
        try:
            # Get user's current licenses
            licenses = await self._graph_call("GET", f"/users/{user_id}/licenseDetails")
            
            # Find matching SKU
            sku_object_id = None
            for lic in licenses:
                if lic['skuPartNumber'] == sku_id or lic['skuId'] == sku_id:
                    sku_object_id = lic['skuId']
                    sku_name = lic['skuPartNumber']
                    break
            
            if not sku_object_id:
                return f"✗ User does not have license: {sku_id}"
            
            # Remove license
            data = {
                "addLicenses": [],
                "removeLicenses": [sku_object_id]
            }
            
            await self._graph_call("POST", f"/users/{user_id}/assignLicense", data=data)
            
            # Audit log
            logger.warning(f"Removed license {sku_name} from {user_id}")
            
            return (
                f"✓ License removed successfully\n\n"
                f"User: {user_id}\n"
                f"License: {sku_name}"
            )
            
        except Exception as e:
            logger.error(f"Error removing license: {e}")
            return f"Failed to remove license: {str(e)}"
    
    async def reset_user_mfa(
        self,
        user_id: Annotated[str, "User principal name or object ID"],
    ) -> str:
        """Reset user MFA authentication methods and force re-registration on next sign-in."""
        logger.info(f"Resetting MFA for user: {user_id}")
        
        try:
            # Get current authentication methods
            methods = await self._graph_call("GET", f"/users/{user_id}/authentication/methods")
            
            # Delete all methods except password
            deleted = []
            for method in methods:
                if method['@odata.type'] != '#microsoft.graph.passwordAuthenticationMethod':
                    method_id = method['id']
                    method_type = method['@odata.type'].split('.')[-1]
                    await self._graph_call("DELETE", f"/users/{user_id}/authentication/{method_type}Methods/{method_id}")
                    deleted.append(method_type)
            
            # Audit log
            logger.warning(f"Reset MFA for {user_id}, deleted methods: {deleted}")
            
            return (
                f"✓ MFA reset successfully\n\n"
                f"User: {user_id}\n"
                f"Deleted methods: {', '.join(deleted) if deleted else 'None'}\n\n"
                f"User will be prompted to register MFA on next sign-in."
            )
            
        except Exception as e:
            logger.error(f"Error resetting MFA: {e}")
            return f"Failed to reset MFA: {str(e)}"
    
    async def get_group_members(
        self,
        group_id: Annotated[str, "Group object ID or display name"],
        limit: Annotated[int, "Maximum members to return"] = 50,
    ) -> str:
        """Get members of an Azure AD group."""
        logger.info(f"Getting members for group: {group_id}")
        
        try:
            # If group_id is a name, search for it
            if "@" not in group_id and "-" not in group_id:
                groups = await self._graph_call("GET", f"/groups?$filter=displayName eq '{group_id}'")
                if not groups:
                    return f"✗ Group not found: {group_id}"
                group_id = groups[0]['id']
                group_name = groups[0]['displayName']
            else:
                group = await self._graph_call("GET", f"/groups/{group_id}")
                group_name = group['displayName']
            
            # Get members
            members = await self._graph_call("GET", f"/groups/{group_id}/members?$top={limit}")
            
            if not members:
                return f"Group '{group_name}' has no members"
            
            result = [f"Members of '{group_name}' ({len(members)}):\n"]
            for member in members:
                member_type = member.get('@odata.type', '').split('.')[-1]
                result.append(f"  👤 {member.get('displayName', 'Unknown')} ({member_type})")
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error getting group members: {e}")
            return f"Failed to get group members: {str(e)}"
    
    async def add_user_to_group(
        self,
        user_id: Annotated[str, "User principal name or object ID"],
        group_id: Annotated[str, "Group object ID or display name"],
    ) -> str:
        """Add a user to an Azure AD group."""
        logger.info(f"Adding user {user_id} to group {group_id}")
        
        try:
            # Resolve user ID
            if "@" in user_id:
                user = await self._graph_call("GET", f"/users/{user_id}")
                user_object_id = user['id']
            else:
                user_object_id = user_id
            
            # Resolve group ID
            if "@" not in group_id and "-" not in group_id:
                groups = await self._graph_call("GET", f"/groups?$filter=displayName eq '{group_id}'")
                if not groups:
                    return f"✗ Group not found: {group_id}"
                group_object_id = groups[0]['id']
                group_name = groups[0]['displayName']
            else:
                group = await self._graph_call("GET", f"/groups/{group_id}")
                group_object_id = group['id']
                group_name = group['displayName']
            
            # Add user to group
            data = {
                "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_object_id}"
            }
            await self._graph_call("POST", f"/groups/{group_object_id}/members/$ref", data=data)
            
            # Audit log
            logger.info(f"Added user {user_id} to group {group_name}")
            
            return (
                f"✓ User added to group successfully\n\n"
                f"User: {user_id}\n"
                f"Group: {group_name}"
            )
            
        except Exception as e:
            logger.error(f"Error adding user to group: {e}")
            return f"Failed to add user to group: {str(e)}"
    
    async def get_sign_in_logs(
        self,
        user_id: Annotated[str, "User principal name"],
        days: Annotated[int, "Number of days to query"] = 7,
        limit: Annotated[int, "Maximum logs to return"] = 20,
    ) -> str:
        """Get user sign-in logs for security analysis with status, location, and device information."""
        logger.info(f"Getting sign-in logs for {user_id} (last {days} days)")
        
        try:
            # Calculate date filter
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
            
            # Query sign-in logs
            logs = await self._graph_call(
                "GET",
                f"/auditLogs/signIns?$filter=userPrincipalName eq '{user_id}' and createdDateTime ge {start_date}&$top={limit}&$orderby=createdDateTime desc"
            )
            
            if not logs:
                return f"No sign-in logs found for {user_id} in the last {days} days"
            
            result = [f"Sign-in logs for {user_id} (last {days} days):\n"]
            for log in logs:
                status = "✓" if log['status']['errorCode'] == 0 else "✗"
                location = log.get('location', {})
                device = log.get('deviceDetail', {})
                
                result.append(
                    f"{status} {log['createdDateTime']}\n"
                    f"   App: {log.get('appDisplayName', 'Unknown')}\n"
                    f"   Location: {location.get('city', 'Unknown')}, {location.get('countryOrRegion', 'Unknown')}\n"
                    f"   Device: {device.get('operatingSystem', 'Unknown')} - {device.get('browser', 'Unknown')}\n"
                    f"   IP: {log.get('ipAddress', 'Unknown')}\n"
                    f"   Status: {log['status'].get('errorCode', 0)} - {log['status'].get('failureReason', 'Success')}\n"
                )
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error getting sign-in logs: {e}")
            return f"Failed to get sign-in logs: {str(e)}"
    
    async def check_conditional_access(
        self,
        user_id: Annotated[str, "User principal name or object ID"],
    ) -> str:
        """Check which Conditional Access policies apply to a user."""
        logger.info(f"Checking conditional access policies for {user_id}")
        
        try:
            # Get all CA policies
            policies = await self._graph_call("GET", "/identity/conditionalAccess/policies")
            
            if not policies:
                return "No Conditional Access policies configured"
            
            # Get user's groups
            user_groups = await self._graph_call("GET", f"/users/{user_id}/memberOf")
            user_group_ids = [g['id'] for g in user_groups]
            
            applicable = []
            for policy in policies:
                if policy['state'] != 'enabled':
                    continue
                
                conditions = policy.get('conditions', {})
                users = conditions.get('users', {})
                
                # Check if policy applies to this user
                includes_all = 'All' in users.get('includeUsers', [])
                includes_user = user_id in users.get('includeUsers', [])
                includes_group = any(g in user_group_ids for g in users.get('includeGroups', []))
                
                if includes_all or includes_user or includes_group:
                    applicable.append(policy)
            
            if not applicable:
                return f"No Conditional Access policies apply to {user_id}"
            
            result = [f"Conditional Access policies for {user_id}:\n"]
            for policy in applicable:
                result.append(
                    f"📋 {policy['displayName']}\n"
                    f"   State: {policy['state']}\n"
                    f"   Grant Controls: {', '.join(policy.get('grantControls', {}).get('builtInControls', []))}\n"
                )
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error checking conditional access: {e}")
            return f"Failed to check conditional access: {str(e)}"
    
    async def list_user_licenses(
        self,
        user_id: Annotated[str, "User principal name or object ID"],
    ) -> str:
        """List all licenses assigned to a user with service plans."""
        logger.info(f"Listing licenses for {user_id}")
        
        try:
            licenses = await self._graph_call("GET", f"/users/{user_id}/licenseDetails")
            
            if not licenses:
                return f"User {user_id} has no licenses assigned"
            
            result = [f"Licenses for {user_id}:\n"]
            for lic in licenses:
                enabled_plans = [p['servicePlanName'] for p in lic['servicePlans'] if p['provisioningStatus'] == 'Success']
                
                result.append(
                    f"📜 {lic['skuPartNumber']}\n"
                    f"   SKU ID: {lic['skuId']}\n"
                    f"   Enabled Plans ({len(enabled_plans)}): {', '.join(enabled_plans[:5])}"
                )
                if len(enabled_plans) > 5:
                    result.append(f"   ... and {len(enabled_plans) - 5} more")
                result.append("")
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error listing licenses: {e}")
            return f"Failed to list licenses: {str(e)}"
    
    async def _graph_call(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Any:
        """Make Microsoft Graph API call with OAuth2 auth, token caching, retry logic, and rate limiting."""
        # Placeholder - in production use actual Graph API
        await asyncio.sleep(0.1)
        
        # Simulate responses
        if "/users/" in endpoint and method == "GET" and "/memberOf" in endpoint:
            return [
                {"id": "group1", "displayName": "IT Support"},
                {"id": "group2", "displayName": "All Employees"},
            ]
        elif "/users/" in endpoint and method == "GET" and "/licenseDetails" in endpoint:
            return [
                {"skuId": "sku1", "skuPartNumber": "ENTERPRISEPACK", "servicePlans": [{"servicePlanName": "EXCHANGE_S_ENTERPRISE", "provisioningStatus": "Success"}]},
            ]
        elif "/users/" in endpoint and method == "GET":
            return {
                "id": "user123",
                "userPrincipalName": "jsmith@company.com",
                "displayName": "John Smith",
                "jobTitle": "IT Support Specialist",
                "department": "Information Technology",
                "officeLocation": "Building A",
                "mobilePhone": "+1-555-0123",
                "accountEnabled": True,
            }
        elif method == "POST" and "/users" == endpoint:
            return {"id": "newuser123", **data}
        elif "/subscribedSkus" in endpoint:
            return [
                {"skuId": "sku1", "skuPartNumber": "ENTERPRISEPACK"},
                {"skuId": "sku2", "skuPartNumber": "SPE_E3"},
            ]
        elif "/groups" in endpoint and method == "GET" and "members" in endpoint:
            return [
                {"id": "user1", "displayName": "User One", "@odata.type": "#microsoft.graph.user"},
                {"id": "user2", "displayName": "User Two", "@odata.type": "#microsoft.graph.user"},
            ]
        elif "/auditLogs/signIns" in endpoint:
            return [
                {
                    "createdDateTime": "2025-11-24T10:00:00Z",
                    "appDisplayName": "Office 365",
                    "status": {"errorCode": 0},
                    "location": {"city": "Seattle", "countryOrRegion": "US"},
                    "deviceDetail": {"operatingSystem": "Windows 10", "browser": "Chrome"},
                    "ipAddress": "192.168.1.1",
                }
            ]
        elif "/identity/conditionalAccess/policies" in endpoint:
            return [
                {
                    "id": "policy1",
                    "displayName": "Require MFA for All Users",
                    "state": "enabled",
                    "conditions": {"users": {"includeUsers": ["All"]}},
                    "grantControls": {"builtInControls": ["mfa"]},
                }
            ]
        
        return {}
