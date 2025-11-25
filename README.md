# IT Service Desk Agent - Azure AI Foundry

**Status: Development - Clean Architecture Implementation**

Enterprise IT Service Desk agent system built on Azure AI Foundry with proper software engineering patterns.

## Architecture

Clean separation of concerns:

```
Core Domain (models, agent protocol)
  ↓
Orchestration (router with intent registry)
  ↓
Tool Layer (domain-specific operations)
  ↓
Integrations (HTTP clients, PowerShell executor)
  ↓
External Systems (Graph, AD, ServiceNow, Intune)
```

### Package Structure

```
src/it_service_desk_agent/
├── __init__.py                    # Public API
├── entrypoint.py                  # Azure AI Foundry handler
├── config.py                      # Centralized settings
├── secrets.py                     # Key Vault abstraction
├── core/
│   ├── models.py                  # AgentRequest, AgentResponse, RequestContext
│   └── agent.py                   # Agent protocol + AgentCapability
├── orchestration/
│   └── router.py                  # Intent-based routing
├── security/
│   ├── policy.py                  # RBAC models
│   ├── registry.py                # Policy enforcement (20+ policies)
│   └── audit.py                   # AuditLogger
├── integrations/
│   ├── base_http.py               # Shared HTTP client
│   ├── microsoft_graph.py         # Graph API client
│   ├── servicenow.py              # ServiceNow client
│   └── powershell.py              # PowerShell executor
├── tools/                         # Domain-specific operations (TBD)
└── agents/                        # Concrete agent implementations (TBD)
    └── identity_agent.py          # Example: IdentityAgent

tests/
├── test_router.py                 # Router unit tests (mocked)
└── test_security.py               # Security layer tests (mocked)

integration_tests/                 # Real API tests (optional)
```

## Installation

### Prerequisites

- Python 3.10+
- Azure subscription with:
  - Azure AI Foundry project (optional)
  - App registration with Graph API permissions
  - ServiceNow instance (optional)
  - Active Directory with PowerShell remoting (optional)

### Install Package

```bash
# Clone repository
git clone https://github.com/GarretteGriffin/IT-ServiceDesk-Agent-Foundry.git
cd IT-ServiceDesk-Agent-Foundry

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Configuration

Create `.env` file:

```env
# Microsoft Graph
GRAPH_TENANT_ID=your-tenant-id
GRAPH_CLIENT_ID=your-app-client-id
GRAPH_CLIENT_SECRET=your-app-secret

# ServiceNow
SERVICENOW_INSTANCE_URL=https://yourinstance.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=your-password

# Active Directory
AD_DOMAIN=example.com
AD_SERVER=dc01.example.com
AD_BASE_DN=DC=example,DC=com
PS_SCRIPT_PATH=./scripts

# Azure AI Foundry (optional)
AZURE_AI_PROJECT_ENDPOINT=https://your-project.cognitiveservices.azure.com
AZURE_AI_MODEL_DEPLOYMENT=gpt-4o
```

## Usage

### As Azure AI Foundry Handler

```python
from it_service_desk_agent.entrypoint import handle_request

# Request from Azure AI Foundry
payload = {
    "intent": "identity.user.lookup",
    "parameters": {"username": "user@example.com"},
    "context": {
        "user_id": "admin@example.com",
        "source": "teams",
        "correlation_id": "abc-123",
        "risk_level": "low",
        "approval_granted": False
    }
}

response = handle_request(payload)
print(response["success"])  # True
print(response["data"])     # User details
```

### Direct Router Usage

```python
from it_service_desk_agent import AgentRouter, AgentRequest, Settings
from it_service_desk_agent.core.models import RequestContext
from it_service_desk_agent.agents.identity_agent import IdentityAgent

# Initialize
settings = Settings()
router = AgentRouter()

# Register agents
# (In production, use register_default_agents())
identity_agent = IdentityAgent(ad_tools=None, graph_tools=None)
router.register_agent(identity_agent)

# Process request
request = AgentRequest(
    intent="identity.user.lookup",
    parameters={"username": "user@example.com"},
    context=RequestContext(
        user_id="admin@example.com",
        source="cli",
        correlation_id="test-123",
        risk_level="low"
    )
)

response = await router.route(request)
```

## Security Model

### Authorization

All sensitive operations enforce authorization through `security.registry.authorize()`:

```python
from it_service_desk_agent.security.registry import authorize

# Check if user has required roles + approvals
authorize("identity.password.reset", request.context)
```

### Policies (20+)

Key policies defined in `security/registry.py`:

| Operation | Required Roles | Risk Level | Approval Required |
|-----------|----------------|------------|-------------------|
| `identity.password.reset` | it_helpdesk, it_admin | medium | Yes |
| `ad.laps.retrieve` | it_admin | high | Yes |
| `intune.device.wipe` | it_admin | critical | Yes |
| `graph.license.assign` | it_admin | medium | Yes |
| `servicenow.incident.create` | it_helpdesk, it_admin | low | No |

### Audit Logging

All operations are logged via `security.audit.AuditLogger`:

```python
from it_service_desk_agent.security.audit import AuditLogger, AuditEventType

AuditLogger.log_operation(
    event_type=AuditEventType.PASSWORD_RESET,
    context=request_context,
    outcome="success",
    details={"target_user": "user@example.com"}
)
```

## Testing

### Unit Tests (Mocked)

```bash
# Run unit tests (no external API calls)
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=it_service_desk_agent --cov-report=term-missing
```

### Integration Tests (Optional)

```bash
# Run integration tests against real APIs
RUN_INTEGRATION_TESTS=1 pytest integration_tests/ -v
```

## Development Status

### ✅ Completed

- Core abstractions (Agent protocol, models)
- Intent-based router with fail-fast duplicate detection
- Security layer with RBAC + audit logging (20+ policies)
- Integration clients (Graph, ServiceNow, PowerShell base)
- Configuration management (Pydantic Settings)
- Unit tests for router and security (mocked)
- Package structure and installability

### 🚧 In Progress

- Tool layer (ActiveDirectoryTools, GraphUserTools, etc.)
- Concrete agents (IdentityAgent partially implemented)
- Integration layer completion
- Integration tests

### ❌ Not Implemented

- Agent registration in `register_default_agents()`
- Tool implementations wrapping integrations
- Complete agent implementations (DeviceAgent, TicketAgent, etc.)
- Key Vault integration (secrets.py has TODO)
- Rate limiting and retry logic
- API server (FastAPI wrapper)
- Deployment configs (Docker, Kubernetes, Terraform)

## What's Different from Previous Versions

### Before (archived in `archive/`):

❌ 19 micro-agent architecture astronautics  
❌ Multiple competing system files  
❌ `asyncio.sleep()` placeholders instead of real APIs  
❌ Scattered `os.getenv()` calls  
❌ Security theater (no actual RBAC)  
❌ Tests that call real APIs  

### Now:

✅ Clean architecture with proper separation of concerns  
✅ One canonical router + agent system  
✅ Agent protocol with strict interface  
✅ Real integration clients (no mocks in production code)  
✅ Centralized configuration (Pydantic Settings)  
✅ Real RBAC enforcement (`authorize()` function)  
✅ Audit logging for all sensitive operations  
✅ Unit tests with mocks (no external dependencies)  

## Contributing

This is an internal prototype. Before production deployment:

1. ✅ Complete tool layer implementations
2. ✅ Wire agents to tools in `register_default_agents()`
3. ✅ Implement Key Vault integration
4. ✅ Add rate limiting and retry logic
5. ✅ Security review and penetration testing
6. ✅ Integration tests against production-like environment
7. ✅ Deployment automation (IaC)

## License

MIT License - See LICENSE file for details.

## Credits

Built on:
- [Azure AI Foundry](https://ai.azure.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [httpx](https://www.python-httpx.org/)
- [Azure Identity](https://learn.microsoft.com/python/api/overview/azure/identity-readme)
