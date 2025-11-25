"""
Configuration management using Pydantic Settings
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Azure AI Foundry
    AZURE_AI_PROJECT_ENDPOINT: str
    AZURE_AI_MODEL_DEPLOYMENT: str = "gpt-5"
    AZURE_TENANT_ID: str
    AZURE_SUBSCRIPTION_ID: str
    AZURE_RESOURCE_GROUP: str = "rg-it-agent"
    
    # Azure AI Search
    AZURE_SEARCH_ENDPOINT: str
    AZURE_SEARCH_INDEX_NAME: str = "it-knowledge-base"
    AZURE_SEARCH_API_VERSION: str = "2023-11-01"
    
    # Microsoft Graph
    GRAPH_CLIENT_ID: str
    GRAPH_CLIENT_SECRET: str
    GRAPH_TENANT_ID: str
    GRAPH_SCOPES: str = "User.ReadWrite.All,Group.ReadWrite.All,Directory.ReadWrite.All"
    
    # ServiceNow
    SERVICENOW_INSTANCE: str
    SERVICENOW_CLIENT_ID: Optional[str] = None
    SERVICENOW_CLIENT_SECRET: Optional[str] = None
    SERVICENOW_USERNAME: Optional[str] = None
    SERVICENOW_PASSWORD: Optional[str] = None
    
    # Active Directory
    AD_DOMAIN: str = "atlasroofing.com"
    AD_SERVER: str
    AD_BASE_DN: str = "DC=atlasroofing,DC=com"
    AD_SERVICE_ACCOUNT: str
    AD_SERVICE_PASSWORD: Optional[str] = None  # Load from Key Vault
    
    # Azure Automation
    AUTOMATION_ACCOUNT_NAME: str
    AUTOMATION_RESOURCE_GROUP: str
    AUTOMATION_SUBSCRIPTION_ID: str
    
    # Azure Key Vault
    KEY_VAULT_URL: str
    
    # Application Insights
    APPLICATIONINSIGHTS_CONNECTION_STRING: str
    
    # Agent Configuration
    AGENT_NAME: str = "IT Service Desk Agent"
    AGENT_INSTRUCTIONS_FILE: str = "./config/agent_instructions.txt"
    MAX_CONVERSATION_HISTORY: int = 20
    DEFAULT_TEMPERATURE: float = 0.7
    ENABLE_STREAMING: bool = True
    
    # Security
    ALLOWED_ORIGINS: str = "https://teams.microsoft.com,https://portal.azure.com"
    API_KEY_HEADER: str = "X-API-Key"
    ENABLE_AUTH: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse allowed origins into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def graph_scopes_list(self) -> list[str]:
        """Parse Graph API scopes into list"""
        return [scope.strip() for scope in self.GRAPH_SCOPES.split(",")]


# Global settings instance
settings = Settings()
