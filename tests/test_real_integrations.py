"""
Real Integration Tests - Actually call APIs
"""

import pytest
import asyncio
from src.tools.active_directory import ADTool
from src.tools.microsoft_graph import GraphTool
from src.tools.servicenow import ServiceNowTool
from src.tools.intune import IntuneTool


class TestRealIntegrations:
    """
    These tests make REAL API calls.
    
    Requirements:
    - Valid credentials in .env
    - Access to test tenant/domain
    - ServiceNow instance with test data
    """
    
    @pytest.mark.asyncio
    async def test_graph_get_user(self):
        """Test real Graph API user lookup"""
        graph = GraphTool()
        
        # Replace with a real test user in your tenant
        result = await graph.get_user_details(
            user_id="test.user@atlasroofing.com",
            include_groups=False,
            include_licenses=False
        )
        
        assert "User Details" in result
        assert "@atlasroofing.com" in result
        print(f"\n✓ Graph API user lookup works:\n{result}")
    
    @pytest.mark.asyncio
    async def test_servicenow_search(self):
        """Test real ServiceNow API incident search"""
        snow = ServiceNowTool()
        
        result = await snow.search_incidents(
            state="in_progress",
            limit=5
        )
        
        assert result is not None
        print(f"\n✓ ServiceNow API search works:\n{result}")
    
    @pytest.mark.asyncio
    async def test_intune_list_devices(self):
        """Test real Intune API device listing"""
        intune = IntuneTool()
        
        result = await intune.list_devices(limit=5)
        
        assert result is not None
        print(f"\n✓ Intune API device list works:\n{result}")
    
    @pytest.mark.asyncio
    async def test_ad_powershell(self):
        """Test real PowerShell execution for AD"""
        ad = ADTool()
        
        # Simple test - get domain info
        result = await ad._execute_powershell(
            "Get-ADDomain | Select-Object -Property Name,DNSRoot,DomainMode | ConvertTo-Json"
        )
        
        assert result is not None
        assert len(result) > 0
        print(f"\n✓ PowerShell execution works:\n{result}")


class TestUnitTests:
    """Unit tests that don't require external services"""
    
    def test_config_loaded(self):
        """Test configuration is loaded"""
        from src.config import settings
        
        assert settings.AZURE_AI_PROJECT_ENDPOINT
        assert settings.GRAPH_CLIENT_ID
        assert settings.SERVICENOW_INSTANCE
        print("\n✓ Configuration loaded successfully")
    
    def test_tool_initialization(self):
        """Test tools can be initialized"""
        ad = ADTool()
        graph = GraphTool()
        snow = ServiceNowTool()
        intune = IntuneTool()
        
        assert ad.domain
        assert graph.tenant_id
        assert snow.instance
        assert intune.tenant_id
        print("\n✓ All tools initialized successfully")
    
    def test_tool_functions_list(self):
        """Test tools return function lists"""
        ad = ADTool()
        graph = GraphTool()
        
        ad_funcs = ad.get_functions()
        graph_funcs = graph.get_functions()
        
        assert len(ad_funcs) > 0
        assert len(graph_funcs) > 0
        assert callable(ad_funcs[0])
        assert callable(graph_funcs[0])
        print(f"\n✓ Tool functions: AD={len(ad_funcs)}, Graph={len(graph_funcs)}")


if __name__ == "__main__":
    print("Running tests with real API calls...")
    print("=" * 80)
    pytest.main([__file__, "-v", "-s"])
