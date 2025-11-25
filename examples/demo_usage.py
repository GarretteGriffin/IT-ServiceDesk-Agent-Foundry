"""
Example usage demonstrating the IT Service Desk Agent

This script shows how to use the agent system for various IT operations:
- Identity management (user lookups, password resets, license management)
- Device management (device queries, remote actions)
- Ticket management (incident creation, updates, knowledge base)
"""

import asyncio
from it_service_desk_agent import handle_request
from it_service_desk_agent.core.models import RequestContext


async def example_identity_operations():
    """Demonstrate identity management operations"""
    print("\n" + "="*60)
    print("IDENTITY MANAGEMENT EXAMPLES")
    print("="*60)
    
    # Example 1: Look up user information
    print("\n1. User Lookup (AD + Azure AD)")
    context = RequestContext(
        user_id="admin@atlasroofing.com",
        session_id="demo-session-1",
        request_id="req-001"
    )
    
    response = await handle_request(
        intent="identity.user.lookup",
        parameters={
            "username": "john.doe",
            "include_groups": True,
            "include_licenses": True
        },
        context=context
    )
    print(f"Success: {response.success}")
    if response.success:
        print(f"User: {response.result.get('display_name')}")
        print(f"Email: {response.result.get('upn')}")
        print(f"Enabled: {response.result.get('enabled')}")
        print(f"Groups: {len(response.result.get('groups', []))}")
        print(f"Licenses: {len(response.result.get('licenses', []))}")
    
    # Example 2: Password reset (requires approval)
    print("\n2. Password Reset (Requires Approval)")
    response = await handle_request(
        intent="identity.password.reset",
        parameters={
            "username": "john.doe",
            "temporary_password": "TempPass123!",
            "must_change": True
        },
        context=context
    )
    print(f"Success: {response.success}")
    if response.success:
        print(f"Password reset for: {response.result.get('username')}")
    
    # Example 3: Unlock account
    print("\n3. Unlock Account")
    response = await handle_request(
        intent="identity.account.unlock",
        parameters={"username": "john.doe"},
        context=context
    )
    print(f"Success: {response.success}")
    
    # Example 4: Get user devices
    print("\n4. Get User Devices")
    response = await handle_request(
        intent="identity.user.devices",
        parameters={"username": "john.doe"},
        context=context
    )
    print(f"Success: {response.success}")
    if response.success:
        print(f"Devices: {len(response.result.get('computers', []))}")
    
    # Example 5: Assign license
    print("\n5. Assign License (Requires Approval)")
    response = await handle_request(
        intent="identity.license.assign",
        parameters={
            "username": "john.doe@atlasroofing.com",
            "sku_id": "SPE_E3"
        },
        context=context
    )
    print(f"Success: {response.success}")


async def example_device_operations():
    """Demonstrate device management operations"""
    print("\n" + "="*60)
    print("DEVICE MANAGEMENT EXAMPLES")
    print("="*60)
    
    context = RequestContext(
        user_id="admin@atlasroofing.com",
        session_id="demo-session-2",
        request_id="req-002"
    )
    
    # Example 1: Get device details
    print("\n1. Get Device Details")
    response = await handle_request(
        intent="device.get",
        parameters={"device_id": "LAPTOP-ABC123"},
        context=context
    )
    print(f"Success: {response.success}")
    if response.success:
        print(f"Device: {response.result.get('device_name')}")
        print(f"OS: {response.result.get('os')}")
        print(f"User: {response.result.get('user')}")
        print(f"Compliance: {response.result.get('compliance_state')}")
    
    # Example 2: List devices with filters
    print("\n2. List Windows Devices")
    response = await handle_request(
        intent="device.list",
        parameters={
            "os_type": "Windows",
            "compliance_state": "compliant",
            "limit": 10
        },
        context=context
    )
    print(f"Success: {response.success}")
    if response.success:
        print(f"Found {response.result.get('count')} devices")
    
    # Example 3: Sync device
    print("\n3. Sync Device with Intune")
    response = await handle_request(
        intent="device.sync",
        parameters={"device_id": "device-guid-123"},
        context=context
    )
    print(f"Success: {response.success}")
    
    # Example 4: Restart device (requires approval)
    print("\n4. Restart Device (Requires Approval)")
    response = await handle_request(
        intent="device.restart",
        parameters={"device_id": "device-guid-123"},
        context=context
    )
    print(f"Success: {response.success}")
    
    # Example 5: Wipe device (CRITICAL - requires explicit approval)
    print("\n5. Wipe Device (CRITICAL - Requires Explicit Approval)")
    response = await handle_request(
        intent="device.wipe",
        parameters={"device_id": "device-guid-123"},
        context=context
    )
    print(f"Success: {response.success}")


async def example_ticket_operations():
    """Demonstrate ticket management operations"""
    print("\n" + "="*60)
    print("TICKET MANAGEMENT EXAMPLES")
    print("="*60)
    
    context = RequestContext(
        user_id="admin@atlasroofing.com",
        session_id="demo-session-3",
        request_id="req-003"
    )
    
    # Example 1: Search incidents
    print("\n1. Search Incidents")
    response = await handle_request(
        intent="ticket.search",
        parameters={
            "query": "password reset",
            "state": "new",
            "priority": "high",
            "limit": 10
        },
        context=context
    )
    print(f"Success: {response.success}")
    if response.success:
        print(f"Found {response.result.get('count')} incidents")
    
    # Example 2: Create incident
    print("\n2. Create Incident (Requires Approval)")
    response = await handle_request(
        intent="ticket.create",
        parameters={
            "short_description": "User cannot access email",
            "description": "User John Doe reports unable to access Outlook. Error: Cannot connect to server.",
            "priority": "high",
            "caller_id": "john.doe@atlasroofing.com",
            "assignment_group": "IT Support"
        },
        context=context
    )
    print(f"Success: {response.success}")
    if response.success:
        print(f"Created: {response.result.get('incident_number')}")
        print(f"State: {response.result.get('state')}")
    
    # Example 3: Update incident
    print("\n3. Update Incident (Requires Approval)")
    response = await handle_request(
        intent="ticket.update",
        parameters={
            "incident_number": "INC0010001",
            "work_notes": "Investigating email server connectivity",
            "state": "in_progress"
        },
        context=context
    )
    print(f"Success: {response.success}")
    
    # Example 4: Resolve incident
    print("\n4. Resolve Incident (Requires Approval)")
    response = await handle_request(
        intent="ticket.resolve",
        parameters={
            "incident_number": "INC0010001",
            "resolution_notes": "Reset user mailbox permissions. User confirmed email access restored."
        },
        context=context
    )
    print(f"Success: {response.success}")
    
    # Example 5: Search knowledge base
    print("\n5. Search Knowledge Base")
    response = await handle_request(
        intent="ticket.kb_search",
        parameters={
            "query": "password reset procedure",
            "limit": 5
        },
        context=context
    )
    print(f"Success: {response.success}")
    if response.success:
        print(f"Found {response.result.get('count')} knowledge articles")
        for article in response.result.get('articles', [])[:3]:
            print(f"  - {article.get('title')}")


async def example_error_handling():
    """Demonstrate error handling"""
    print("\n" + "="*60)
    print("ERROR HANDLING EXAMPLES")
    print("="*60)
    
    context = RequestContext(
        user_id="user@atlasroofing.com",
        session_id="demo-session-4",
        request_id="req-004"
    )
    
    # Example 1: Unknown intent
    print("\n1. Unknown Intent")
    response = await handle_request(
        intent="unknown.operation",
        parameters={},
        context=context
    )
    print(f"Success: {response.success}")
    if not response.success:
        print(f"Error: {response.error.message}")
    
    # Example 2: Missing required parameters
    print("\n2. Missing Required Parameters")
    response = await handle_request(
        intent="identity.user.lookup",
        parameters={},  # Missing 'username'
        context=context
    )
    print(f"Success: {response.success}")
    if not response.success:
        print(f"Error: {response.error.message}")
    
    # Example 3: Authorization failure
    print("\n3. Unauthorized Operation")
    limited_context = RequestContext(
        user_id="limited.user@atlasroofing.com",  # User without admin rights
        session_id="demo-session-5",
        request_id="req-005"
    )
    response = await handle_request(
        intent="identity.password.reset",
        parameters={
            "username": "john.doe",
            "temporary_password": "TempPass123!"
        },
        context=limited_context
    )
    print(f"Success: {response.success}")
    if not response.success:
        print(f"Error: {response.error.message}")


async def main():
    """Run all examples"""
    print("\n" + "#"*60)
    print("# IT SERVICE DESK AGENT - USAGE EXAMPLES")
    print("#"*60)
    print("\nNOTE: These examples demonstrate the API structure.")
    print("In a real environment, you would need:")
    print("  - Valid .env configuration")
    print("  - Active Directory/Azure AD access")
    print("  - ServiceNow instance credentials")
    print("  - Proper authorization policies")
    
    try:
        # Run identity examples
        await example_identity_operations()
        
        # Run device examples
        await example_device_operations()
        
        # Run ticket examples
        await example_ticket_operations()
        
        # Run error handling examples
        await example_error_handling()
        
        print("\n" + "#"*60)
        print("# EXAMPLES COMPLETE")
        print("#"*60)
        print("\nAll examples demonstrate:")
        print("  ✓ Intent-based routing")
        print("  ✓ Type-safe parameters")
        print("  ✓ Context propagation")
        print("  ✓ Authorization checks")
        print("  ✓ Audit logging")
        print("  ✓ Error handling")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("This is expected if not running in a configured environment.")


if __name__ == "__main__":
    asyncio.run(main())
