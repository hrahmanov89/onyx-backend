from typing import Dict, List, Optional
import os
from dataclasses import dataclass
from httpx_oauth.clients.openid import BASE_SCOPES, OpenID
from pydantic import BaseModel


@dataclass
class OIDCProviderConfig:
    name: str
    client_id: str
    client_secret: str
    openid_config_url: str
    scopes: List[str]
    additional_params: Dict[str, str] | None = None  # normalized to dict at access time


class OIDCProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, OIDCProviderConfig] = {}

    def register_provider(self, provider: OIDCProviderConfig) -> None:
        """Register an OIDC provider"""
        self.providers[provider.name] = provider

    def get_provider(self, name: str) -> Optional[OIDCProviderConfig]:
        """Get provider by name"""
        return self.providers.get(name)

    def get_all_providers(self) -> Dict[str, OIDCProviderConfig]:
        """Get all registered providers"""
        return self.providers


# Create a singleton registry
oidc_registry = OIDCProviderRegistry()


def setup_default_oidc_provider() -> None:
    """Set up the default OIDC provider from environment variables"""
    client_id = os.environ.get("OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("OAUTH_CLIENT_SECRET", "")
    openid_config_url = os.environ.get("OPENID_CONFIG_URL", "")
    
    # Get custom scopes if set
    oidc_scope_override_str = os.environ.get("OIDC_SCOPE_OVERRIDE", "")
    if oidc_scope_override_str:
        scopes = [scope.strip() for scope in oidc_scope_override_str.split(",")]
    else:
        scopes = list(BASE_SCOPES)
    
    # Add offline_access for refresh tokens if not present
    if "offline_access" not in scopes:
        scopes.append("offline_access")
    
    if client_id and client_secret and openid_config_url:
        provider = OIDCProviderConfig(
            name="default",
            client_id=client_id,
            client_secret=client_secret,
            openid_config_url=openid_config_url,
            scopes=scopes
        )
        oidc_registry.register_provider(provider)


def create_oidc_client(provider_name: str) -> Optional[OpenID]:
    """Create an OIDC client from a registered provider"""
    provider = oidc_registry.get_provider(provider_name)
    if not provider:
        return None
    
    # Normalize additional params for later use (ensure dict)
    if provider.additional_params is None:
        provider.additional_params = {}
    return OpenID(
        provider.client_id,
        provider.client_secret,
        provider.openid_config_url,
        provider.scopes,
    )


# Models for API
class OIDCProviderModel(BaseModel):
    name: str
    display_name: str
    icon_url: Optional[str] = None
    openid_config_url: str
    
    
class CreateOIDCProviderRequest(BaseModel):
    name: str
    display_name: str
    client_id: str
    client_secret: str
    openid_config_url: str
    icon_url: Optional[str] = None
    scopes: List[str] = []
    additional_params: Dict[str, str] = {}
