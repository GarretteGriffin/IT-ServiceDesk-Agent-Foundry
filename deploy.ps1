# Azure AI Foundry Deployment Helper Script
# This script helps package and deploy the IT Service Desk Agent

param(
    [Parameter(Mandatory=$false)]
    [string]$Action = "package",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath = ".\deployment",
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Package-Agent {
    Write-ColorOutput Green "`n=== Packaging IT Service Desk Agent for Azure AI Foundry ===`n"
    
    # Create output directory
    if (Test-Path $OutputPath) {
        Remove-Item -Path $OutputPath -Recurse -Force
    }
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    
    # Files/folders to include
    $includeItems = @(
        "src",
        "agent.yaml",
        "requirements.txt",
        "README.md",
        "AZURE_DEPLOYMENT.md",
        "pyproject.toml"
    )
    
    Write-ColorOutput Cyan "Copying files to deployment directory..."
    foreach ($item in $includeItems) {
        if (Test-Path $item) {
            Copy-Item -Path $item -Destination $OutputPath -Recurse -Force
            Write-ColorOutput Gray "  ✓ $item"
        }
    }
    
    # Create ZIP archive
    $zipName = "it-service-desk-agent-v$Version.zip"
    $zipPath = Join-Path (Get-Location) $zipName
    
    Write-ColorOutput Cyan "`nCreating ZIP archive..."
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    Compress-Archive -Path "$OutputPath\*" -DestinationPath $zipPath -Force
    
    Write-ColorOutput Green "`n✓ Package created successfully!"
    Write-ColorOutput White "  Location: $zipPath"
    Write-ColorOutput White "  Size: $([math]::Round((Get-Item $zipPath).Length / 1MB, 2)) MB"
    
    # Show next steps
    Write-ColorOutput Yellow "`n=== Next Steps ==="
    Write-ColorOutput White "1. Go to https://ai.azure.com"
    Write-ColorOutput White "2. Navigate to your project → Agents"
    Write-ColorOutput White "3. Click 'New Agent' → 'Upload Custom Agent'"
    Write-ColorOutput White "4. Upload: $zipPath"
    Write-ColorOutput White "5. Configure environment variables (see AZURE_DEPLOYMENT.md)"
    Write-ColorOutput White "6. Deploy and test"
    
    Write-ColorOutput Cyan "`nFor detailed instructions, see: AZURE_DEPLOYMENT.md"
}

function Test-Prerequisites {
    Write-ColorOutput Green "`n=== Checking Prerequisites ===`n"
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorOutput Gray "✓ Python: $pythonVersion"
    } catch {
        Write-ColorOutput Red "✗ Python not found. Please install Python 3.10+"
        return $false
    }
    
    # Check Azure CLI (optional)
    try {
        $azVersion = az version --query '\"azure-cli\"' -o tsv 2>&1
        Write-ColorOutput Gray "✓ Azure CLI: $azVersion"
    } catch {
        Write-ColorOutput Yellow "○ Azure CLI not found (optional for deployment)"
    }
    
    # Check required files
    $requiredFiles = @("agent.yaml", "requirements.txt", "src\it_service_desk_agent\entrypoint.py")
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-ColorOutput Gray "✓ $file"
        } else {
            Write-ColorOutput Red "✗ Missing required file: $file"
            return $false
        }
    }
    
    Write-ColorOutput Green "`n✓ All prerequisites met"
    return $true
}

function Show-Configuration {
    Write-ColorOutput Green "`n=== Required Configuration ===`n"
    
    Write-ColorOutput Cyan "Microsoft Graph API:"
    Write-ColorOutput White "  GRAPH_TENANT_ID=<your-tenant-id>"
    Write-ColorOutput White "  GRAPH_CLIENT_ID=<your-app-client-id>"
    Write-ColorOutput White "  GRAPH_CLIENT_SECRET=<your-app-secret>"
    
    Write-ColorOutput Cyan "`nServiceNow:"
    Write-ColorOutput White "  SERVICENOW_INSTANCE_URL=https://yourinstance.service-now.com"
    Write-ColorOutput White "  SERVICENOW_USERNAME=<username>"
    Write-ColorOutput White "  SERVICENOW_PASSWORD=<password>"
    
    Write-ColorOutput Cyan "`nActive Directory:"
    Write-ColorOutput White "  AD_DOMAIN=example.com"
    Write-ColorOutput White "  AD_SERVER=dc01.example.com"
    Write-ColorOutput White "  AD_BASE_DN=DC=example,DC=com"
    Write-ColorOutput White "  PS_SCRIPT_PATH=./scripts"
    
    Write-ColorOutput Yellow "`nSet these in Azure AI Foundry Portal after deployment"
}

function Deploy-ToAzure {
    Write-ColorOutput Green "`n=== Deploying to Azure AI Foundry ===`n"
    
    # Check if Azure CLI is available
    try {
        az version | Out-Null
    } catch {
        Write-ColorOutput Red "✗ Azure CLI not found. Please install: https://aka.ms/InstallAzureCLI"
        return
    }
    
    # Get workspace details
    $workspace = Read-Host "Enter workspace name"
    $resourceGroup = Read-Host "Enter resource group name"
    
    Write-ColorOutput Cyan "`nDeploying agent..."
    
    try {
        az ml online-deployment create `
            --file agent.yaml `
            --workspace-name $workspace `
            --resource-group $resourceGroup
        
        Write-ColorOutput Green "`n✓ Deployment initiated successfully!"
        Write-ColorOutput White "Monitor deployment in Azure Portal or AI Foundry"
    } catch {
        Write-ColorOutput Red "`n✗ Deployment failed: $_"
    }
}

# Main execution
switch ($Action.ToLower()) {
    "package" {
        if (Test-Prerequisites) {
            Package-Agent
            Show-Configuration
        }
    }
    "check" {
        Test-Prerequisites
    }
    "config" {
        Show-Configuration
    }
    "deploy" {
        if (Test-Prerequisites) {
            Package-Agent
            Deploy-ToAzure
        }
    }
    default {
        Write-ColorOutput Yellow "Usage: .\deploy.ps1 -Action [package|check|config|deploy]"
        Write-ColorOutput White "`nActions:"
        Write-ColorOutput White "  package  - Create deployment package (default)"
        Write-ColorOutput White "  check    - Check prerequisites"
        Write-ColorOutput White "  config   - Show configuration requirements"
        Write-ColorOutput White "  deploy   - Package and deploy to Azure"
    }
}
