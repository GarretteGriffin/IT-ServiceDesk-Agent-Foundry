# Integration Tests

These tests call **real external APIs** and require proper credentials.

## DO NOT Run These Tests Without:

1. Valid Azure credentials (Graph API app registration)
2. Valid ServiceNow instance credentials
3. Active Directory with PowerShell remoting access
4. Understanding that these tests will:
   - Create/modify/delete real resources
   - Incur API costs
   - Potentially affect production if not isolated

## Running Integration Tests

Integration tests are **disabled by default**. To run them:

```bash
# Set environment variable
export RUN_INTEGRATION_TESTS=1

# Run integration tests
pytest integration_tests/ -v

# Or with coverage
pytest integration_tests/ -v --cov=it_service_desk_agent
```

## Test Environment Setup

Create a separate `.env.test` file with test credentials:

```env
# Test Azure AD tenant (NOT production)
GRAPH_TENANT_ID=test-tenant-id
GRAPH_CLIENT_ID=test-client-id
GRAPH_CLIENT_SECRET=test-secret

# Test ServiceNow instance
SERVICENOW_INSTANCE_URL=https://dev12345.service-now.com
SERVICENOW_USERNAME=test_user
SERVICENOW_PASSWORD=test_password

# Test Active Directory (isolated test domain)
AD_DOMAIN=testdomain.com
AD_SERVER=testdc.testdomain.com
```

## Best Practices

1. **Never run against production** - Use dedicated test environments
2. **Clean up after tests** - Delete created resources
3. **Use test data** - Never use real user/device data
4. **Isolate tests** - Each test should be independent
5. **Mock when possible** - Prefer unit tests with mocks

## Guard Pattern

All integration tests should start with:

```python
import os
import pytest

# Skip if integration tests not enabled
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled (set RUN_INTEGRATION_TESTS=1 to enable)"
)
```

This ensures tests won't accidentally run in CI or local dev without explicit opt-in.
