# Security Documentation

## Current Security Posture

### ✅ Implemented
- **Dynamic capability detection** - Agent only claims tools that are configured
- **Input validation** - All user inputs sanitized before processing
- **Audit logging** - Sensitive operations logged with classification (OperationType)
- **Safe-by-default instructions** - Agent requires confirmation for destructive operations
- **Fail-safe initialization** - Agent won't start without at least one configured tool

### ⚠️ Partially Implemented
- **Audit trail** - Structure exists but not shipped to SIEM/Azure Monitor
- **Configuration validation** - Tools check for credentials but don't validate permissions
- **Error handling** - Exists but not comprehensive across all edge cases

### ❌ Not Implemented (REQUIRED FOR PRODUCTION)
- **Role-Based Access Control (RBAC)** - No per-user permission scoping
- **Just-In-Time (JIT) Access** - No temporary privilege elevation
- **Rate limiting** - No protection against abuse/DoS
- **Approval workflows** - Destructive operations can execute immediately
- **Secret rotation** - No automated credential refresh
- **Threat detection** - No anomaly detection for suspicious patterns
- **Disaster recovery** - No backup/restore for agent state

---

## Security Checklist for Production

### Authentication & Authorization
- [ ] Implement Azure AD authentication for all API access
- [ ] Add per-user RBAC (read-only vs operator vs admin roles)
- [ ] Implement JIT access for sensitive operations (LAPS, Bitlocker, resets)
- [ ] Add approval workflow for destructive actions (wipes, deletions)
- [ ] Validate service principal permissions match least-privilege principle
- [ ] Implement token validation and refresh

### Input Validation & Sanitization
- [ ] Review all InputValidator patterns for completeness
- [ ] Add fuzzing tests for injection vulnerabilities
- [ ] Validate all tool outputs before returning to user
- [ ] Implement content filtering for PII/secrets in responses
- [ ] Add max request size limits

### Audit & Monitoring
- [ ] Ship audit logs to Azure Monitor / Sentinel
- [ ] Configure alerts for sensitive operations (LAPS access, wipes, etc.)
- [ ] Set up dashboards for operation tracking
- [ ] Implement anomaly detection (unusual user behavior, bulk operations)
- [ ] Create runbooks for security incident response
- [ ] Define retention policy for audit logs (compliance requirement)

### Secrets Management
- [ ] Move all credentials from .env to Azure Key Vault
- [ ] Implement secret rotation schedule
- [ ] Use Managed Identity instead of client secrets where possible
- [ ] Audit Key Vault access logs
- [ ] Implement break-glass procedures for Key Vault access

### Network Security
- [ ] Deploy agent in VNet with private endpoints
- [ ] Configure NSGs to restrict inbound/outbound traffic
- [ ] Use Azure Private Link for Azure service connections
- [ ] Implement Web Application Firewall (WAF) if exposing API
- [ ] Configure DDoS protection

### Tool-Specific Security
#### Active Directory
- [ ] Validate AD service account has minimum required permissions
- [ ] Implement read-only mode (disable password resets, unlocks)
- [ ] Add approval requirement for LAPS/Bitlocker retrieval
- [ ] Log all AD writes to separate high-security audit log
- [ ] Implement stale computer cleanup dry-run mode

#### PowerShell Execution
- [ ] Review and harden command validation (InputValidator.validate_powershell_command)
- [ ] Implement runbook signing in Azure Automation
- [ ] Add execution timeout limits
- [ ] Restrict runbook access to specific Automation accounts
- [ ] Implement output size limits

#### Microsoft Graph / Intune
- [ ] Review Graph API permissions (use least-privilege scopes)
- [ ] Add approval workflow for device wipes
- [ ] Implement dry-run mode for bulk operations
- [ ] Validate tenant isolation (no cross-tenant access)

#### ServiceNow
- [ ] Use OAuth instead of basic auth
- [ ] Implement read-only mode for testing
- [ ] Validate incident creation doesn't expose sensitive data
- [ ] Add rate limiting for ticket creation

### Deployment Security
- [ ] Use private container registry (Azure Container Registry with RBAC)
- [ ] Scan container images for vulnerabilities
- [ ] Implement pod security policies (if using Kubernetes)
- [ ] Configure resource limits (CPU, memory)
- [ ] Enable Application Insights for distributed tracing
- [ ] Implement health checks and liveness probes

### Compliance & Governance
- [ ] Document data residency requirements
- [ ] Implement data retention policies
- [ ] Create disaster recovery plan
- [ ] Define incident response procedures
- [ ] Conduct security review with InfoSec team
- [ ] Perform penetration testing
- [ ] Create compliance documentation (SOC 2, ISO 27001, etc.)

---

## Known Limitations

### No Multi-Tenancy
- Agent does not isolate operations per tenant/organization
- Credentials are global (one AD account, one Graph app, one ServiceNow instance)
- **Risk:** Cross-tenant data leakage if credentials misconfigured

### No User Context Propagation
- Agent executes all operations with service principal identity
- No way to track "Alice requested password reset for Bob"
- **Mitigation:** Audit logs include user context field (must be passed by caller)

### Placeholder Implementations
- PowerShell execution uses `asyncio.sleep()` instead of Azure Automation API
- Microsoft Graph calls return mocked data instead of real API calls
- ServiceNow integration is simulated
- **Risk:** Production use will fail until integrations are completed

### No Rate Limiting
- No protection against rapid-fire requests
- Could exhaust API quotas (Graph, ServiceNow, Azure Automation)
- **Risk:** Denial of service, cost overruns

### Limited Error Recovery
- No retry logic with exponential backoff
- Partial failures (e.g., 3 of 5 users updated) are not handled gracefully
- No circuit breaker for failing external services

---

## Secure Configuration Example

```bash
# Azure AI Foundry
AZURE_AI_PROJECT_ENDPOINT=https://YOUR_PROJECT.api.azureml.ms
AZURE_AI_MODEL_DEPLOYMENT=gpt-5-deployment
AZURE_TENANT_ID=YOUR_TENANT_ID
AZURE_SUBSCRIPTION_ID=YOUR_SUBSCRIPTION_ID

# Use Managed Identity (no client secret)
# AZURE_CLIENT_ID=<managed-identity-client-id>

# Microsoft Graph (App Registration with least-privilege)
GRAPH_TENANT_ID=YOUR_TENANT_ID
GRAPH_CLIENT_ID=YOUR_APP_ID
# GRAPH_CLIENT_SECRET stored in Key Vault, not .env

# Active Directory (read-only service account)
AD_DOMAIN=corp.company.com
AD_SERVER=dc01.corp.company.com
AD_SERVICE_ACCOUNT=svc-agent-readonly@corp.company.com
# AD_SERVICE_PASSWORD stored in Key Vault

# ServiceNow (OAuth, not basic auth)
SERVICENOW_INSTANCE=yourinstance.service-now.com
SERVICENOW_CLIENT_ID=YOUR_OAUTH_CLIENT_ID
# SERVICENOW_CLIENT_SECRET stored in Key Vault

# Azure Automation (for PowerShell execution)
AZURE_AUTOMATION_ACCOUNT_NAME=automation-agent
AZURE_AUTOMATION_RESOURCE_GROUP=rg-agent-prod
AZURE_AUTOMATION_SUBSCRIPTION_ID=YOUR_SUBSCRIPTION_ID

# Azure AI Search (for RAG)
AZURE_AI_SEARCH_ENDPOINT=https://YOUR_SEARCH.search.windows.net
AZURE_AI_SEARCH_INDEX_NAME=kb-index
# AZURE_AI_SEARCH_KEY stored in Key Vault

# Agent Configuration
AGENT_NAME=IT-ServiceDesk-Agent
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true
SAFE_MODE=true  # Require confirmation for destructive ops
```

---

## Incident Response

### Suspected Compromise
1. **Immediately revoke** service principal credentials
2. **Rotate** all secrets in Key Vault
3. **Review** audit logs for suspicious activity (export to secure location)
4. **Disable** agent deployment (scale to 0 replicas)
5. **Notify** security team and conduct forensic analysis

### Unauthorized Access Detected
1. **Identify** scope of access (what resources were touched)
2. **Revoke** user/app permissions
3. **Review** AD, Graph, Intune changes made during incident window
4. **Rollback** unauthorized changes if possible
5. **Document** incident for post-mortem

### Audit Log Tampering
1. **Preserve** evidence (snapshots of logs before tampering)
2. **Investigate** how tampering occurred (compromised creds, bug)
3. **Implement** immutable audit logging (write-once storage)
4. **Enhance** monitoring (alert on log deletion/modification)

---

## Safe Operations Mode

For initial deployment, enable safe mode to prevent destructive actions:

```python
# In src/agent.py
if settings.SAFE_MODE:
    # Remove destructive operations from tool list
    dangerous_tools = [
        'reset_user_password',
        'get_laps_password',
        'get_bitlocker_recovery_key',
        'remote_wipe',
        'restart_remote_service',
    ]
    self.tools = [t for t in self.tools if t.__name__ not in dangerous_tools]
```

---

## Contact

Security concerns: **security@company.com**  
Production deployment: **devops@company.com**  
Architecture questions: **architecture@company.com**
