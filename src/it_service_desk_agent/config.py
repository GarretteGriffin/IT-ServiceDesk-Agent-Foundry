"""Centralized configuration using Pydantic - no more scattered env reads"""

from functools import lru_cache
from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment
    
    All configuration goes through this class.
    No direct os.getenv() calls elsewhere.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Microsoft Graph
    graph_tenant_id: str = Field(..., env="GRAPH_TENANT_ID")
    graph_client_id: str = Field(..., env="GRAPH_CLIENT_ID")
    graph_client_secret: str = Field(..., env="GRAPH_CLIENT_SECRET")
    graph_base_url: str = Field("https://graph.microsoft.com/v1.0", env="GRAPH_BASE_URL")
    
    # ServiceNow
    snow_instance_url: str = Field(..., env="SERVICENOW_INSTANCE_URL")
    snow_username: str = Field(..., env="SERVICENOW_USERNAME")
    snow_password: str = Field(..., env="SERVICENOW_PASSWORD")
    
    # Active Directory / PowerShell
    ad_domain: str = Field("atlasroofing.com", env="AD_DOMAIN")
    ad_server: str = Field(..., env="AD_SERVER")
    ad_base_dn: str = Field("DC=atlasroofing,DC=com", env="AD_BASE_DN")
    ps_script_path: str = Field("./scripts", env="PS_SCRIPT_PATH")
    
    # Azure AI Foundry (if using agents)
    azure_ai_project_endpoint: Optional[str] = Field(None, env="AZURE_AI_PROJECT_ENDPOINT")
    azure_ai_model_deployment: str = Field("gpt-4o", env="AZURE_AI_MODEL_DEPLOYMENT")
    
    # Security
    allowed_origins: str = Field("*", env="ALLOWED_ORIGINS")
    api_key_header: str = Field("X-API-Key", env="API_KEY_HEADER")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")


@lru_cache()
def get_settings() -> Settings:
    """
    Get settings singleton
    
    Cached so we only parse .env once.
    """
    return Settings()
