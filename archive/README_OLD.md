# IT Service Desk Micro-Agent System - Azure AI Foundry

[![Azure AI Foundry](https://img.shields.io/badge/Azure%20AI%20Foundry-Micro--Agent-0078D4)](https://ai.azure.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![Security Hardened](https://img.shields.io/badge/Security-Hardened-green)](docs/SECURITY.md)
[![Architecture](https://img.shields.io/badge/Architecture-19--Agent-orange)](docs/ARCHITECTURE.md)
[![Agents](https://img.shields.io/badge/Agents-19%20Specialized-brightgreen)](#micro-agent-catalog)

**World-Class IT Service Desk powered by Azure AI Foundry micro-agent architecture**

This revolutionary system uses **19 ultra-specialized AI agents** coordinated by an AI-powered orchestrator with workflow management to handle complex IT operations with maximum accuracy, security, and speed.

## ⚠️ Current Status: DEVELOPMENT / TESTING ONLY

**DO NOT deploy to production without:**
1. Completing security review (see [Security Checklist](#security-checklist))
2. Implementing RBAC for per-user permissions
3. Running full test suite against prod-like environment
4. Conducting penetration testing on all tool integrations
5. Setting up audit log monitoring and alerting

---

## Architecture

Azure AI Foundry provides:
- Custom tool development (vs limited connectors in Copilot Studio)
- Flexible deployment options (Container Apps, AKS, App Service)
- Full code control with Python/C#
- Model choice (GPT-5, o3, o4-mini, etc.)
- Enterprise security (Managed Identity, Key Vault, VNet)

---

## 🏗️ Micro-Agent Architecture (19 Agents)

### Why Micro-Agents?

**Revolutionary approach**: Instead of 1 monolithic agent or 6 broad specialists, we use **19 ultra-focused micro-agents** with **single responsibilities**.

✅ **Maximum Accuracy** - Each agent does ONE thing exceptionally well  
✅ **Superior Security** - Sensitive operations (LAPS, Bitlocker) isolated in dedicated agents  
✅ **AI Orchestration** - GPT-4o-powered workflow engine with 4-stage processing  
✅ **Parallel Execution** - Independent tasks run concurrently (3x faster)  
✅ **Risk-Based Confirmations** - Automatic security controls based on operation risk  
✅ **Complete Audit Trail** - Agent-level accountability for all operations  
✅ **Technician Support** - Dedicated agent for troubleshooting guidance  
✅ **Cost Optimized** - GPT-4o-mini for simple queries, GPT-4o for complex orchestration  

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    MASTER ORCHESTRATOR                          │
│         AI Workflow Engine (GPT-4o)                            │
│  Intent Analysis → Workflow Planning → Orchestration →         │
│  Response Synthesis                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────▼────────────┐
                │  WORKFLOW COORDINATOR   │
                │  Multi-step execution   │
                │  State management       │
                └────────────┬────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │         A2A Tool Connections           │
        └────────────────────┬────────────────────┘
                             │
    ┌────────┬───────────────┼────────────┬────────┐
    │        │               │            │        │
┌───▼────┐ ┌▼──────┐ ┌──────▼─────┐ ┌───▼────┐ ┌▼────────┐
│IDENTITY│ │DEVICE │ │ TICKETING  │ │SECURITY│ │TECHNICIAN│
│(6 micro)│ │(4 micro)│ │  (3 micro) │ │(3 micro)│ │(1 agent)│
└────────┘ └────────┘ └────────────┘ └────────┘ └─────────┘
```

### Micro-Agent Catalog (19 Agents)

#### 🔐 Identity & Access Management (6 agents)
| Agent | Responsibility | Risk | Model |
|-------|----------------|------|-------|
| **AD User Lookup** | Read-only AD queries | LOW | GPT-4o-mini |
| **AD Password Reset** | Password resets ONLY | MEDIUM | GPT-4o |
| **AD Computer Mgmt** | Computer accounts + LAPS | HIGH | GPT-4o |
| **Azure AD User** | Cloud identity lookup | LOW | GPT-4o-mini |
| **License Management** | Office 365 licenses | MEDIUM | GPT-4o |
| **Group Membership** | AD/Azure AD groups | MEDIUM | GPT-4o |

#### 💻 Device Management (4 agents)
| Agent | Responsibility | Risk | Model |
|-------|----------------|------|-------|
| **Device Inventory** | Device info lookup | LOW | GPT-4o-mini |
| **Compliance Check** | Policy compliance | LOW | GPT-4o |
| **Remote Actions** | Lock/wipe/sync/restart | MEDIUM-CRITICAL | GPT-4o |
| **App Deployment** | App installation status | LOW | GPT-4o-mini |

#### 🎫 Ticketing & Documentation (3 agents)
| Agent | Responsibility | Risk | Model |
|-------|----------------|------|-------|
| **Incident Creation** | Create ServiceNow tickets | LOW | GPT-4o |
| **Ticket Query** | Search/update tickets | LOW | GPT-4o |
| **Knowledge Base Search** | KB article lookup | LOW | GPT-4o-mini |

#### 🔒 Security & Credentials (3 agents)
| Agent | Responsibility | Risk | Model |
|-------|----------------|------|-------|
| **LAPS Retrieval** | Local admin passwords | **HIGH** | GPT-4o |
| **Bitlocker Recovery** | Recovery keys | **HIGH** | GPT-4o |
| **Sign-In Analysis** | Authentication logs | LOW | GPT-4o |

#### 👨‍💻 Technician Support (1 agent)
| Agent | Responsibility | Risk | Model |
|-------|----------------|------|-------|
| **Technician Assistant** | Troubleshooting guidance | LOW | GPT-4o |

#### 🧠 Orchestration (2 components)
| Component | Responsibility | Model |
|-----------|----------------|-------|
| **Master Orchestrator** | AI workflow engine (4-stage process) | GPT-4o |
| **Workflow Coordinator** | Multi-agent execution manager | N/A |

### Orchestration Intelligence (4-Stage Process)

**Stage 1: Intent Analysis**
- Parse query and extract entities (users, devices, groups, etc.)
- Classify intent (information/modification/investigation/workflow)
- Assess risk level (LOW/MEDIUM/HIGH/CRITICAL)
- Identify context (follow-up, urgency, ticket reference)

**Stage 2: Workflow Planning**
- Break into atomic tasks (single-responsibility operations)
- Identify dependencies (sequential vs parallel)
- Select micro-agents (routing to 18 specialists)
- Determine execution order (optimize for speed and safety)

**Stage 3: Execution Orchestration**
- Execute tasks via A2A tool connections
- Handle risk-based confirmations automatically
- Aggregate results from multiple agents
- Handle failures gracefully (retry, skip, escalate)

**Stage 4: Response Synthesis**
- Format results (clear, actionable)
- Provide context (why, timeline, next steps)
- Create audit trail (what, who, when, why)
- Suggest follow-ups (proactive recommendations)

### Example: Multi-Agent VPN Troubleshooting

```
User: "User can't access VPN"

Master Orchestrator Analysis:
├─ Intent: Investigation + Resolution
├─ Entities: VPN, user (need to identify)
├─ Risk: LOW to MEDIUM (depends on findings)
└─ Agents needed: 4 micro-agents

Execution Plan:
Step 1 (Parallel execution):
├─ Group Membership Agent → Check VPN-Users group
├─ Device Inventory Agent → Get user's devices
├─ Compliance Check Agent → Check device compliance
└─ Sign-In Analysis Agent → Check authentication issues

Step 2 (Conditional on findings):
If not in VPN-Users:
  └─ Group Membership Agent → Add to VPN-Users (MEDIUM risk, confirm)
If device non-compliant:
  ├─ Provide remediation steps to user
  └─ Remote Actions Agent → Sync device (force re-check)
If authentication issues:
  └─ Provide MFA troubleshooting steps

Step 3 (Response Synthesis):
✓ Root cause: User not in VPN-Users group
✓ Action taken: Added to group (confirmed by user)
⏳ Timeline: 15 minutes for propagation
📋 Next steps: Sign out, sign back in, try VPN
```

---

## 📦 Installation

### Prerequisites

- Python 3.11+
- Azure subscription
- Azure AI Foundry project
- Azure CLI installed

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/atlas/it-servicedesk-agent-foundry.git
cd it-servicedesk-agent-foundry

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Configure environment variables
# Edit .env with your Azure AI Foundry project details
```

### Azure Resources Setup

```bash
# Login to Azure
az login

# Create resource group
az group create --name rg-it-agent --location eastus

# Create Azure AI Foundry project (via portal or CLI)
# https://ai.azure.com/

# Deploy required models (in Azure AI Foundry portal)
# - gpt-5 or gpt-4.1 for general operations
# - o3-mini for complex reasoning tasks

# Create Azure AI Search for RAG
az search service create --name search-it-kb --resource-group rg-it-agent --sku basic
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
# Azure AI Foundry
AZURE_AI_PROJECT_ENDPOINT=https://<project>.api.azureml.ms
AZURE_AI_MODEL_DEPLOYMENT=gpt-5
AZURE_TENANT_ID=<your-tenant-id>
AZURE_SUBSCRIPTION_ID=<your-subscription-id>

# Azure AI Search (for RAG)
AZURE_SEARCH_ENDPOINT=https://<search>.search.windows.net
AZURE_SEARCH_INDEX_NAME=it-knowledge-base

# Microsoft Graph
GRAPH_CLIENT_ID=<app-registration-id>
GRAPH_CLIENT_SECRET=<secret>

# ServiceNow
SERVICENOW_INSTANCE=<instance>.service-now.com
SERVICENOW_CLIENT_ID=<client-id>
SERVICENOW_CLIENT_SECRET=<secret>

# Active Directory
AD_DOMAIN=atlasroofing.com
AD_SERVER=dc01.atlasroofing.com

# Azure Automation (for PowerShell)
AUTOMATION_ACCOUNT_NAME=automation-it-ops
AUTOMATION_RESOURCE_GROUP=rg-it-agent

# Logging
APPLICATIONINSIGHTS_CONNECTION_STRING=<connection-string>
```

---

## 🚀 Usage

### Run Locally

```bash
# Start the agent
python src/main.py

# Or with FastAPI server
uvicorn src.api:app --reload --port 8000
```

### Test Multi-Agent System

```python
from src.multi_agent_system import MultiAgentITServiceDesk
import asyncio

async def test():
    # Initialize multi-agent system
    service_desk = MultiAgentITServiceDesk()
    await service_desk.initialize()
    
    # Example queries (orchestrator routes to specialists)
    queries = [
        "Reset password for jsmith@atlasroofing.com",  # → AD Agent
        "Check if user has Office 365 license",        # → Graph Agent
        "Is laptop DESK-001 compliant?",                # → Intune Agent
        "Create incident for printer issue",            # → ServiceNow Agent
        "How do I connect to VPN?",                     # → Knowledge Base Agent
    ]
    
    for query in queries:
        response = await service_desk.run(query)
        print(f"User: {query}")
        print(f"Response: {response}\n")
    
    # Cleanup
    await service_desk.cleanup()

# Run
asyncio.run(test())
```

### Run Specific Agent Directly

```python
from src.agents import ActiveDirectoryAgent

async def test_ad_agent():
    # Test a single specialist agent
    ad_agent = ActiveDirectoryAgent()
    await ad_agent.initialize()
    
    response = await ad_agent.process_request(
        "Get information for user jsmith"
    )
    print(response)
    
    await ad_agent.cleanup()
```

### Deploy to Azure

```bash
# Build Docker image
docker build -t it-servicedesk-agent .

# Push to Azure Container Registry
az acr build --registry <registry> --image it-servicedesk-agent:latest .

# Deploy to Azure Container Apps
az containerapp create \
  --name it-servicedesk-agent \
  --resource-group rg-it-agent \
  --image <registry>.azurecr.io/it-servicedesk-agent:latest \
  --environment <environment> \
  --ingress external \
  --target-port 8000
```

---

## 🛠️ Custom Tools

### Active Directory Tool

```python
from src.tools.active_directory import ADTool

# Get computer info with LAPS password
result = await ad_tool.get_computer_info("DESKTOP-001", include_laps=True)

# Reset computer account
await ad_tool.reset_computer_account("DESKTOP-001")

# Get Bitlocker recovery key
key = await ad_tool.get_bitlocker_key("DESKTOP-001")
```

### PowerShell Execution Tool

```python
from src.tools.powershell import PowerShellTool

# Execute Exchange Online command
result = await ps_tool.execute_exchange(
    "Get-Mailbox -Identity jsmith | Select-Object *"
)

# Network diagnostics
result = await ps_tool.network_diagnostics("server01.atlasroofing.com")
```

### ServiceNow Tool

```python
from src.tools.servicenow import ServiceNowTool

# Search incidents
incidents = await snow_tool.search_incidents(
    filters={"assigned_to": "me", "state": "open"}
)

# Create incident
incident = await snow_tool.create_incident(
    short_description="Password reset for user",
    category="Account Management",
    urgency="2"
)
```

---

## 📚 Key Features

### 1. **Intelligent Conversation Management**
- Multi-turn conversations with context retention
- Thread persistence for ongoing tickets
- User authentication and authorization

### 2. **Advanced Automation**
- Active Directory computer management (LAPS, Bitlocker, stale cleanup)
- PowerShell script execution (Exchange, AD, file servers)
- ServiceNow ticket automation
- Microsoft Intune device operations

### 3. **Knowledge Grounding (RAG)**
- Azure AI Search integration
- ServiceNow knowledge base
- Internal documentation (SharePoint)
- Microsoft Learn articles
- Historical ticket resolutions

### 4. **Security & Compliance**
- Azure Managed Identity authentication
- Azure Key Vault for secrets
- Audit logging to Azure Monitor
- Role-based access control
- Data encryption at rest and in transit

### 5. **Observability**
- Application Insights integration
- Distributed tracing
- Custom metrics and alerts
- Performance monitoring

---

## 🎯 Example Use Cases

### Password Reset
```
User: "Reset password for jsmith@company.com"
Agent: 
  1. Validates user permissions
  2. Checks AD user status
  3. Generates temporary password
  4. Resets password in AD
  5. Sends notification email
  6. Creates ServiceNow incident
  7. Returns confirmation with ticket number
```

### Device Troubleshooting
```
User: "DESKTOP-001 is not responding"
Agent:
  1. Queries Intune for device status
  2. Checks AD computer account
  3. Retrieves recent event logs
  4. Pings device
  5. Suggests remediation steps
  6. Offers remote restart option
```

### Bulk Provisioning
```
User: "Provision 50 new users from CSV"
Agent:
  1. Validates CSV format
  2. Checks for duplicate accounts
  3. Creates AD accounts in batches
  4. Assigns licenses via Graph API
  5. Enrolls devices in Intune
  6. Sends welcome emails
  7. Updates ServiceNow CMDB
```

---

## 🏗️ Project Structure

```
IT-ServiceDesk-Agent-Foundry/
├── src/
│   ├── agent.py                    # Main agent class
│   ├── api.py                      # FastAPI endpoints
│   ├── config.py                   # Configuration management
│   ├── tools/                      # Custom tools
│   │   ├── active_directory.py    # AD operations
│   │   ├── powershell.py          # PowerShell execution
│   │   ├── servicenow.py          # ServiceNow integration
│   │   ├── microsoft_graph.py     # Graph API operations
│   │   ├── intune.py              # Intune device management
│   │   └── exchange.py            # Exchange Online operations
│   ├── knowledge/                  # RAG knowledge base
│   │   ├── search.py              # Azure AI Search integration
│   │   └── indexing.py            # Document indexing
│   └── utils/                      # Utility functions
│       ├── auth.py                # Authentication
│       ├── logging.py             # Logging setup
│       └── validation.py          # Input validation
├── tests/                          # Unit and integration tests
├── deployment/                     # Deployment configs
│   ├── Dockerfile                 # Container definition
│   ├── docker-compose.yml         # Local testing
│   ├── kubernetes/                # K8s manifests
│   └── terraform/                 # Infrastructure as Code
├── docs/                           # Documentation
├── .env.example                    # Environment template
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Project metadata
└── README.md                       # This file
```

---

## 🔒 Security Best Practices

- **Use Managed Identity** for Azure resource authentication
- **Store secrets in Key Vault** (connection strings, API keys)
- **Enable Azure AD authentication** for API endpoints
- **Implement RBAC** for tool access (least privilege)
- **Audit all operations** to Azure Monitor
- **Encrypt data** at rest and in transit
- **Regular security scans** in CI/CD pipeline

---

## 📈 Monitoring & Observability

### Application Insights

```python
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation, measure, view

# Track custom metrics
agent_requests = measure.MeasureInt("agent/requests", "Number of agent requests")
```

### Logging

```python
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string=APPINSIGHTS_CONNECTION_STRING))
```

---

## 🚢 Deployment Options

### 1. Azure Container Apps (Recommended)
- Serverless container hosting
- Auto-scaling based on load
- Built-in ingress and HTTPS
- Low operational overhead

### 2. Azure App Service
- Platform-as-a-Service
- Easy deployment slots
- Built-in authentication
- Custom domain support

### 3. Azure Kubernetes Service (AKS)
- Full container orchestration
- Advanced networking
- High availability
- Complex workloads

---

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit

# Run integration tests
pytest tests/integration

# Run with coverage
pytest --cov=src tests/

# Load testing
locust -f tests/load/locustfile.py
```

---

## 📝 License

Copyright © 2025 Atlas Roofing Corporation. All rights reserved.

---

## 🤝 Contributing

This is an internal project. For contributions:

1. Create feature branch
2. Implement changes with tests
3. Submit pull request for review
4. CI/CD pipeline validates changes
5. Deploy to staging for validation
6. Promote to production

---

## 🆘 Support

- **Technical Issues:** Create GitHub issue
- **Azure Questions:** Contact Cloud Architecture team
- **Agent Functionality:** IT Development team
- **Urgent Production Issues:** On-call rotation

---

**Built with 🔧 by Atlas IT Development Team**

*Powered by Azure AI Foundry*
