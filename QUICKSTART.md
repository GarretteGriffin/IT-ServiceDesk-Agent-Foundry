# Quick Start: Deploy to Azure AI Foundry

This guide gets you from code to deployed agent in 5 minutes.

## 🚀 Fast Path (Recommended)

### Step 1: Package the Agent

Run the deployment helper script:

```powershell
.\deploy.ps1 -Action package
```

This creates `it-service-desk-agent-v1.0.0.zip` ready for upload.

### Step 2: Upload to Azure AI Foundry

1. **Open Azure AI Foundry Portal**
   - Navigate to [https://ai.azure.com](https://ai.azure.com)
   - Sign in with your Azure account
   - Select your AI Foundry project (or create one)

2. **Create New Agent**
   - Go to **Agents** in the left navigation
   - Click **+ New Agent**
   - Select **Upload Custom Agent**

3. **Upload the ZIP**
   - Browse and select `it-service-desk-agent-v1.0.0.zip`
   - Click **Upload**
   - Wait for upload to complete (~30 seconds)

### Step 3: Configure Environment Variables

In the Azure AI Foundry portal, set these environment variables:

**Required - Microsoft Graph:**
```
GRAPH_TENANT_ID=<your-azure-ad-tenant-id>
GRAPH_CLIENT_ID=<your-app-registration-client-id>
GRAPH_CLIENT_SECRET=<your-app-registration-secret>
```

**Required - ServiceNow:**
```
SERVICENOW_INSTANCE_URL=https://yourinstance.service-now.com
SERVICENOW_USERNAME=<your-servicenow-username>
SERVICENOW_PASSWORD=<your-servicenow-password>
```

**Required - Active Directory:**
```
AD_DOMAIN=example.com
AD_SERVER=dc01.example.com
```

**Optional:**
```
GRAPH_BASE_URL=https://graph.microsoft.com/v1.0
AD_BASE_DN=DC=example,DC=com
PS_SCRIPT_PATH=./scripts
```

### Step 4: Deploy

1. Click **Deploy** button
2. Wait for deployment (~2-3 minutes)
3. Status will change to **Running**

### Step 5: Test

Click **Test** or **Playground** and try:

```json
{
  "intent": "identity.user.lookup",
  "parameters": {
    "username": "john.doe",
    "include_groups": true
  },
  "context": {
    "user_id": "admin@example.com",
    "session_id": "test-123"
  }
}
```

Expected response:
```json
{
  "success": true,
  "result": {
    "display_name": "John Doe",
    "upn": "john.doe@example.com",
    "enabled": true,
    "groups": [...],
    "licenses": [...]
  },
  "latency_ms": 245
}
```

## ✅ You're Done!

Your agent is now live and can handle 16 different intents across:
- **Identity Management** (6 intents)
- **Device Management** (5 intents)
- **Ticket Management** (5 intents)

## 📋 What Gets Deployed

The deployment includes:
- ✅ 3 agents (Identity, Device, Ticket)
- ✅ 16 intents with full capabilities
- ✅ 4 tool classes (AD, Graph, ServiceNow, Intune)
- ✅ 27 methods for IT operations
- ✅ RBAC security with 20+ policies
- ✅ Audit logging for all operations

## 🔐 Security Notes

1. **Use Key Vault in Production**
   - Don't store secrets in environment variables
   - Migrate to Azure Key Vault: See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md#-secrets-management)

2. **Review RBAC Policies**
   - Default policies in `src/it_service_desk_agent/security/registry.py`
   - Customize for your organization's needs

3. **Enable Audit Logging**
   - All operations are logged via `AuditLogger`
   - Configure Application Insights for monitoring

## 📊 Available Intents

### Identity Management
```
identity.user.lookup         - Look up user (AD + Azure AD)
identity.password.reset      - Reset password (requires approval)
identity.account.unlock      - Unlock account
identity.user.devices        - Get user's devices
identity.license.assign      - Assign license (requires approval)
identity.license.remove      - Remove license (requires approval)
```

### Device Management
```
device.get                   - Get device details
device.list                  - List devices with filters
device.sync                  - Trigger Intune sync
device.restart               - Restart device (requires approval)
device.wipe                  - Wipe device (CRITICAL - requires approval)
```

### Ticket Management
```
ticket.search                - Search incidents
ticket.create                - Create incident (requires approval)
ticket.update                - Update incident (requires approval)
ticket.resolve               - Resolve incident (requires approval)
ticket.kb_search             - Search knowledge base
```

## 🆘 Troubleshooting

**Agent won't start?**
- Check all environment variables are set
- Verify app registration has Graph API permissions
- Check Application Insights logs

**Authorization errors?**
- Verify admin consent granted for API permissions
- Check user roles in context match RBAC policies

**Can't connect to ServiceNow?**
- Test credentials manually
- Verify instance URL format (include https://)
- Check firewall rules

**Active Directory errors?**
- Ensure PowerShell remoting enabled
- Verify domain controller accessible from Azure
- Check AD credentials have necessary permissions

## 📚 Next Steps

1. **Review Examples**: Check `examples/demo_usage.py` for all 16 intents
2. **Customize Security**: Update RBAC policies in `security/registry.py`
3. **Add Monitoring**: Configure Application Insights alerts
4. **Scale Up**: Review [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for production best practices

## 🎯 Alternative Deployment Methods

- **Azure CLI**: See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md#option-2-deploy-via-azure-cli)
- **Azure DevOps**: Create pipeline with `agent.yaml`
- **GitHub Actions**: Use Azure credentials secret
- **Terraform**: Use `azurerm_machine_learning_workspace` resource

---

**Need Help?** See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for detailed documentation.
