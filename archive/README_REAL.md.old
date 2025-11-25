# IT Service Desk Agent - Real Implementation

**Status: Working Prototype with Real API Integrations**

This is an Azure AI Foundry agent system for IT helpdesk automation. It actually calls real APIs (no mocks).

## What Actually Works Today

✅ **Real API Integrations**
- Microsoft Graph API (Azure AD, licenses, groups) - uses httpx + azure-identity
- Active Directory via PowerShell - executes real PowerShell commands
- ServiceNow REST API - basic auth + httpx
- Microsoft Intune via Graph API - device management endpoints

✅ **4 Working Agents**
- Active Directory Agent - user/computer management via PowerShell
- Microsoft Graph Agent - Azure AD + M365 operations
- ServiceNow Agent - incident management
- Intune Agent - device management

✅ **Simple Routing**
- Keyword-based routing (no over-engineered orchestration)
- Each agent has specific tools
- Direct API calls (no asyncio.sleep() placeholders)

## What Doesn't Work Yet

❌ **No Tests** - test file exists but needs to be run against your tenant  
❌ **No RBAC** - no role-based access control  
❌ **No Approvals** - no confirmation workflow for destructive operations  
❌ **No Rate Limiting** - no throttling or retry logic  
❌ **No API Server** - no FastAPI wrapper  
❌ **No Deployment Configs** - no Docker/Kubernetes/Terraform  
❌ **Secrets in .env** - not using Key Vault yet

## Setup

### 1. Clone

```bash
git clone https://github.com/GarretteGriffin/IT-ServiceDesk-Agent-Foundry.git
cd IT-ServiceDesk-Agent-Foundry
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file with your credentials:

```env
# Azure AI Foundry
AZURE_AI_PROJECT_ENDPOINT=https://your-project.cognitiveservices.azure.com
AZURE_AI_MODEL_DEPLOYMENT=gpt-4o
AZURE_TENANT_ID=your-tenant-id
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=your-resource-group

# Microsoft Graph
GRAPH_CLIENT_ID=your-app-client-id
GRAPH_CLIENT_SECRET=your-app-secret
GRAPH_TENANT_ID=your-tenant-id

# ServiceNow
SERVICENOW_INSTANCE=yourinstance
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=your-password

# Active Directory
AD_DOMAIN=yourdomain.com
AD_SERVER=dc01.yourdomain.com
AD_BASE_DN=DC=yourdomain,DC=com
```

### 4. Run

```bash
python src/simple_agent_system.py
```

## How It Works

1. **User asks a question**: "Reset password for john.smith"
2. **Simple routing**: Keyword match → Active Directory Agent
3. **Agent processes**: Calls real AD PowerShell command
4. **Response returned**: "Password reset successfully for john.smith@domain.com"

No complex orchestration. No 19 micro-agents. Just 4 agents that actually work.

## Real Usage Examples

```python
from src.simple_agent_system import ITServiceDesk

service_desk = ITServiceDesk()
await service_desk.initialize()

# Look up a user (calls Graph API)
response = await service_desk.query("Look up john.smith@company.com")

# Reset password (calls AD via PowerShell)
response = await service_desk.query("Reset password for jane.doe")

# Create incident (calls ServiceNow API)
response = await service_desk.query("Create incident for printer not working")

# Check device (calls Intune via Graph API)
response = await service_desk.query("Check compliance for LAPTOP-12345")
```

## Testing

Run integration tests (requires valid credentials):

```bash
pytest tests/test_real_integrations.py -v -s
```

This will actually call:
- Microsoft Graph API to look up a user
- ServiceNow API to search incidents
- Intune API to list devices
- PowerShell to query AD

## Architecture

```
src/
├── simple_agent_system.py   # Main system (4 agents, simple routing)
├── tools/
│   ├── active_directory.py  # Real PowerShell execution
│   ├── microsoft_graph.py   # Real Graph API (httpx + azure-identity)
│   ├── servicenow.py        # Real ServiceNow API (httpx + basic auth)
│   └── intune.py            # Real Intune API (Graph API)
├── config.py                # Pydantic settings from .env
└── utils/                   # Logging, validation, audit

tests/
└── test_real_integrations.py  # Real API tests (not mocks)
```

## What's Next

1. **Run Tests** - Verify real API calls work with your tenant
2. **Add Approvals** - Confirmation prompts for password resets, device wipes
3. **Add RBAC** - Simple role checking before dangerous operations
4. **Move Secrets** - Migrate from .env to Azure Key Vault
5. **Add API Server** - FastAPI wrapper for production use
6. **Add Monitoring** - Application Insights integration

## Contributing

This is a real working prototype, not vaporware. PRs welcome for:
- Real features that actually work
- Tests that actually run
- Documentation that matches reality

Not welcome:
- Marketing speak
- Fake features
- Architecture astronautics

## License

MIT

---

**Note**: This README describes what actually exists in the code. No fake project trees, no imaginary features, no "coming soon" fantasies.
