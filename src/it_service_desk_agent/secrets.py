"""
Secret provider abstraction - migration path to Key Vault

TODO: Replace with Azure Key Vault integration
For now, wraps Settings to decouple call sites from .env
"""

from .config import get_settings, Settings


def get_secret_settings() -> Settings:
    """
    Get settings with secrets
    
    Current: Returns settings from .env
    Future: Will fetch secrets from Azure Key Vault
    
    Use this instead of get_settings() when you need secrets.
    Makes Key Vault migration easier - only change this file.
    """
    # TODO: Replace with Key Vault client
    # from azure.keyvault.secrets import SecretClient
    # client = SecretClient(vault_url=..., credential=...)
    # graph_secret = client.get_secret("graph-client-secret").value
    # etc.
    
    return get_settings()
