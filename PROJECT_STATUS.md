# IT Service Desk Agent - Azure AI Foundry

This project has been rebuilt from scratch using **Azure AI Foundry** (formerly Azure AI Studio) instead of Copilot Studio for significantly more power, flexibility, and production capabilities.

## 🎯 Key Advantages Over Copilot Studio

- **Full code control** - Python with complete customization
- **Any model** - GPT-5, o3, o4-mini, Phi-4, or custom models
- **Custom tools** - Build any capability (AD, PowerShell, etc.)
- **Production deployment** - Azure Container Apps, AKS, App Service
- **Advanced RAG** - Azure AI Search with semantic ranking
- **Enterprise security** - Managed Identity, Key Vault, VNet
- **Scalability** - Auto-scaling and load balancing
- **Full observability** - App Insights, tracing, metrics

## 📁 Project Status

### ✅ Completed
- Project structure initialized
- Core agent framework (`src/agent.py`)
- Configuration management (`src/config.py`)
- Active Directory tool with LAPS/Bitlocker support
- Logging utilities
- Dependencies and environment setup

### 🚧 In Progress
- PowerShell execution tool
- ServiceNow integration tool
- Microsoft Graph tool
- Intune tool
- Knowledge search (RAG with AI Search)
- FastAPI web service
- Deployment configurations

### 📝 Next Steps
1. Complete remaining tools
2. Setup Azure AI Foundry project
3. Deploy models (GPT-5, o3-mini)
4. Create Azure AI Search index
5. Deploy to Azure Container Apps
6. Integrate with Teams/web portal

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure credentials

# Run agent
python src/agent.py
```

See [README.md](README.md) for full documentation.

---

**This is the right approach for enterprise-grade AI agents.** 

Azure AI Foundry gives us the power and flexibility needed to build a world-class IT Service Desk agent that can truly accomplish anything requiring IT involvement.
