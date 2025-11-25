# IT Service Desk Agent - Azure AI Foundry Deployment

## 📋 Prerequisites

1. **Azure Subscription** with access to Azure AI Foundry
2. **Azure AI Foundry Project** created
3. **App Registration** with Microsoft Graph API permissions:
   - `User.Read.All`
   - `User.ReadWrite.All`
   - `Group.Read.All`
   - `DeviceManagementManagedDevices.Read.All`
   - `DeviceManagementManagedDevices.PrivilegedOperations.All`
4. **ServiceNow Instance** with admin credentials
5. **Active Directory** with PowerShell remoting access

## 🚀 Deployment Steps

### Option 1: Deploy via Azure AI Foundry Portal

1. **Navigate to Azure AI Foundry**
   - Go to [https://ai.azure.com](https://ai.azure.com)
   - Select your project

2. **Upload Agent**
   - Navigate to "Agents" section
   - Click "New Agent" → "Upload Custom Agent"
   - Upload the entire project folder or zip the repository

3. **Configure Environment Variables**
   Set the following environment variables in the portal:

   **Microsoft Graph:**
   ```
   GRAPH_TENANT_ID=<your-tenant-id>
   GRAPH_CLIENT_ID=<your-app-client-id>
   GRAPH_CLIENT_SECRET=<your-app-secret>
   ```

   **ServiceNow:**
   ```
   SERVICENOW_INSTANCE_URL=https://yourinstance.service-now.com
   SERVICENOW_USERNAME=<username>
   SERVICENOW_PASSWORD=<password>
   ```

   **Active Directory:**
   ```
   AD_DOMAIN=example.com
   AD_SERVER=dc01.example.com
   AD_BASE_DN=DC=example,DC=com
   PS_SCRIPT_PATH=./scripts
   ```

4. **Deploy**
   - Click "Deploy Agent"
   - Wait for deployment to complete
   - Test with sample requests

### Option 2: Deploy via Azure CLI

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "<your-subscription-id>"

# Create AI Foundry project (if not exists)
az ml workspace create \
  --name "it-helpdesk-workspace" \
  --resource-group "rg-it-helpdesk" \
  --location "eastus"

# Deploy agent
az ml online-deployment create \
  --file agent.yaml \
  --workspace-name "it-helpdesk-workspace" \
  --resource-group "rg-it-helpdesk"
```

### Option 3: Deploy via Azure Developer CLI (azd)

```bash
# Initialize azd
azd init

# Set environment variables
azd env set GRAPH_TENANT_ID "<your-tenant-id>"
azd env set GRAPH_CLIENT_ID "<your-app-client-id>"
azd env set GRAPH_CLIENT_SECRET "<your-app-secret>"
azd env set SERVICENOW_INSTANCE_URL "https://yourinstance.service-now.com"
azd env set SERVICENOW_USERNAME "<username>"
azd env set SERVICENOW_PASSWORD "<password>"
azd env set AD_DOMAIN "example.com"

# Deploy
azd up
```

## 📦 Required Files for Upload

Upload the following files/folders to Azure AI Foundry:

```
IT-ServiceDesk-Agent-Foundry/
├── agent.yaml                 # Agent blueprint (required)
├── requirements.txt           # Python dependencies (required)
├── src/                       # Source code (required)
│   └── it_service_desk_agent/
├── README.md                  # Documentation
├── examples/                  # Example usage (optional)
└── tests/                     # Tests (optional)
```

### Creating a ZIP for Upload

```powershell
# Create deployment package
$excludes = @('__pycache__', '*.pyc', '.git', '.venv', 'venv', 'node_modules', '.env')
$files = Get-ChildItem -Recurse | Where-Object {
    $item = $_
    -not ($excludes | Where-Object { $item.FullName -like "*$_*" })
}

Compress-Archive -Path $files.FullName -DestinationPath "it-service-desk-agent-v1.0.0.zip"
```

Or use Git archive:
```bash
git archive --format=zip --output=it-service-desk-agent-v1.0.0.zip HEAD
```

## 🔐 Secrets Management

For production deployments, use **Azure Key Vault** instead of environment variables:

1. Create Azure Key Vault:
   ```bash
   az keyvault create \
     --name "kv-it-helpdesk" \
     --resource-group "rg-it-helpdesk" \
     --location "eastus"
   ```

2. Store secrets:
   ```bash
   az keyvault secret set --vault-name "kv-it-helpdesk" --name "graph-client-secret" --value "<secret>"
   az keyvault secret set --vault-name "kv-it-helpdesk" --name "servicenow-password" --value "<password>"
   ```

3. Update `agent.yaml` to reference Key Vault:
   ```yaml
   environment:
     keyvault:
       vault_url: https://kv-it-helpdesk.vault.azure.net/
       secrets:
         - name: GRAPH_CLIENT_SECRET
           key_vault_key: graph-client-secret
         - name: SERVICENOW_PASSWORD
           key_vault_key: servicenow-password
   ```

## 🧪 Testing the Deployment

### Test via Azure AI Foundry Portal

1. Navigate to your deployed agent
2. Click "Test" or "Playground"
3. Send test requests:

**Example 1: User Lookup**
```json
{
  "intent": "identity.user.lookup",
  "parameters": {
    "username": "john.doe",
    "include_groups": true,
    "include_licenses": true
  },
  "context": {
    "user_id": "admin@example.com",
    "session_id": "test-session-1"
  }
}
```

**Example 2: Device Sync**
```json
{
  "intent": "device.sync",
  "parameters": {
    "device_id": "device-guid-123"
  },
  "context": {
    "user_id": "admin@example.com",
    "session_id": "test-session-2"
  }
}
```

**Example 3: Create Ticket**
```json
{
  "intent": "ticket.create",
  "parameters": {
    "short_description": "Password reset request",
    "description": "User unable to login after vacation",
    "priority": "high"
  },
  "context": {
    "user_id": "admin@example.com",
    "session_id": "test-session-3"
  }
}
```

### Test via REST API

Once deployed, you can call the agent via REST API:

```bash
# Get endpoint URL
ENDPOINT_URL=$(az ml online-endpoint show \
  --name "it-service-desk-agent" \
  --workspace-name "it-helpdesk-workspace" \
  --resource-group "rg-it-helpdesk" \
  --query scoring_uri -o tsv)

# Get access key
ACCESS_KEY=$(az ml online-endpoint get-credentials \
  --name "it-service-desk-agent" \
  --workspace-name "it-helpdesk-workspace" \
  --resource-group "rg-it-helpdesk" \
  --query primaryKey -o tsv)

# Send request
curl -X POST "$ENDPOINT_URL" \
  -H "Authorization: Bearer $ACCESS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "identity.user.lookup",
    "parameters": {
      "username": "john.doe",
      "include_groups": true
    },
    "context": {
      "user_id": "admin@example.com",
      "session_id": "test-123"
    }
  }'
```

## 📊 Monitoring

### Application Insights

The agent automatically logs to Application Insights if configured:

```bash
# View logs
az monitor app-insights query \
  --app "<app-insights-name>" \
  --resource-group "rg-it-helpdesk" \
  --analytics-query "traces | where customDimensions.agent_name == 'it-service-desk-agent' | take 100"
```

### View Metrics

```bash
# View request metrics
az monitor metrics list \
  --resource "<agent-resource-id>" \
  --metric "Requests" \
  --interval PT1H
```

## 🔄 Updating the Agent

To update a deployed agent:

1. Make code changes locally
2. Commit and push to GitHub
3. Redeploy via portal or CLI:

```bash
# Update deployment
az ml online-deployment update \
  --file agent.yaml \
  --workspace-name "it-helpdesk-workspace" \
  --resource-group "rg-it-helpdesk"
```

## 🐛 Troubleshooting

### Agent Not Starting
- Check environment variables are set correctly
- Verify all required secrets are in Key Vault
- Check Application Insights logs for startup errors

### Authorization Errors
- Verify app registration has correct Graph API permissions
- Check admin consent is granted for API permissions
- Verify service principal has access to required resources

### ServiceNow Connection Errors
- Test ServiceNow credentials manually
- Check firewall rules allow connections from Azure
- Verify instance URL is correct (include https://)

### Active Directory Errors
- Ensure PowerShell remoting is enabled
- Verify domain controller is accessible from Azure
- Check credentials have necessary AD permissions

## 📚 Additional Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Agent Blueprint Schema](https://azuremlschemas.azureedge.net/latest/agentBlueprint.schema.json)
- [Microsoft Graph API Permissions](https://learn.microsoft.com/graph/permissions-reference)
- [ServiceNow REST API](https://developer.servicenow.com/dev.do#!/reference/api/tokyo/rest/)

## 🆘 Support

For issues or questions:
1. Check GitHub Issues: https://github.com/GarretteGriffin/IT-ServiceDesk-Agent-Foundry/issues
2. Review APPLICATION_INSIGHTS logs in Azure Portal
3. Check audit logs in `security/audit.py` output
