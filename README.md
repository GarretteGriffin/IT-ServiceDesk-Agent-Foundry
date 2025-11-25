# IT Service Desk Agent - Azure AI Foundry

[![Azure AI Foundry](https://img.shields.io/badge/Azure%20AI%20Foundry-Agent-0078D4)](https://ai.azure.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)

**Enterprise-grade AI agent built on Azure AI Foundry for comprehensive IT operations**

Production-ready IT Service Desk agent with advanced automation capabilities, built using Azure AI Agent Framework, custom tools for Active Directory, PowerShell execution, and integration with enterprise systems.

---

## 🚀 Why Azure AI Foundry?

Unlike Copilot Studio, Azure AI Foundry provides:

- ✅ **Custom Function/Tool Support** - Build any capability you need
- ✅ **Production-Grade Deployment** - Azure Container Apps, Kubernetes, or App Service
- ✅ **Advanced RAG** - Azure AI Search integration with semantic ranking
- ✅ **Model Flexibility** - Use any model (GPT-5, o3, o4-mini, Phi-4, custom models)
- ✅ **Full Code Control** - Python/C# with complete customization
- ✅ **Enterprise Security** - Managed Identity, Key Vault, VNet integration
- ✅ **Scalability** - Auto-scaling, load balancing, global distribution
- ✅ **Observability** - Application Insights, tracing, metrics
- ✅ **CI/CD Integration** - Azure DevOps, GitHub Actions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface Layer                         │
│  (Teams, Web Portal, Slack, Email, API)                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│              Azure AI Foundry Agent Core                         │
│  - Agent Framework (ChatAgent)                                   │
│  - GPT-5 / o3 Model                                              │
│  - Conversation Management (Threads)                             │
│  - Tool Orchestration                                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┬──────────────┐
        │                         │              │
┌───────▼─────────┐   ┌──────────▼──────┐  ┌───▼──────────────┐
│ Custom Tools    │   │  Azure Services │  │ Knowledge Base   │
│                 │   │                 │  │                  │
│ • AD Management │   │ • Key Vault     │  │ • AI Search      │
│ • PowerShell    │   │ • Monitor       │  │ • ServiceNow KB  │
│ • ServiceNow    │   │ • App Insights  │  │ • SharePoint     │
│ • Intune        │   │ • Cosmos DB     │  │ • MS Learn       │
│ • Graph API     │   │ • Blob Storage  │  │ • Internal Docs  │
│ • Exchange      │   │                 │  │                  │
└─────────────────┘   └─────────────────┘  └──────────────────┘
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

### Test Agent

```python
from src.agent import ITServiceDeskAgent

async def test():
    agent = ITServiceDeskAgent()
    response = await agent.run("Reset password for jsmith@atlasroofing.com")
    print(response)
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
