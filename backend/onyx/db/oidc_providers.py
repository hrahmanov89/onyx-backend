from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from onyx.db.oidc import OIDCProviderConfig


def create_oidc_provider(
    db_session: Session,
    name: str,
    display_name: str,
    client_id: str,
    client_secret: str,
    openid_config_url: str,
    icon_url: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    additional_params: Optional[Dict[str, str]] = None,
) -> OIDCProviderConfig:
    """Create a new OIDC provider configuration in the database"""
    if scopes is None:
        scopes = ["openid", "email", "profile", "offline_access"]
        
    provider = OIDCProviderConfig(
        name=name,
        display_name=display_name,
        client_id=client_id,
        client_secret=client_secret,
        openid_config_url=openid_config_url,
        icon_url=icon_url,
        scopes=scopes,
        additional_params=additional_params or {},
    )
    
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


def get_oidc_provider(db_session: Session, name: str) -> Optional[OIDCProviderConfig]:
    """Get an OIDC provider by name"""
    return db_session.query(OIDCProviderConfig).filter(OIDCProviderConfig.name == name).first()


def get_all_oidc_providers(db_session: Session) -> List[OIDCProviderConfig]:
    """Get all OIDC providers"""
    return db_session.query(OIDCProviderConfig).all()


def update_oidc_provider(
    db_session: Session,
    name: str,
    display_name: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    openid_config_url: Optional[str] = None,
    icon_url: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    additional_params: Optional[Dict[str, str]] = None,
) -> Optional[OIDCProviderConfig]:
    """Update an existing OIDC provider"""
    provider = get_oidc_provider(db_session, name)
    if not provider:
        return None
    
    if display_name is not None:
        provider.display_name = display_name
    if client_id is not None:
        provider.client_id = client_id
    if client_secret is not None:
        provider.client_secret = client_secret
    if openid_config_url is not None:
        provider.openid_config_url = openid_config_url
    if icon_url is not None:
        provider.icon_url = icon_url
    if scopes is not None:
        provider.scopes = scopes
    if additional_params is not None:
        provider.additional_params = additional_params
    
    db_session.commit()
    db_session.refresh(provider)
    return provider


def delete_oidc_provider(db_session: Session, name: str) -> bool:
    """Delete an OIDC provider"""
    provider = get_oidc_provider(db_session, name)
    if not provider:
        return False
    
    db_session.delete(provider)
    db_session.commit()
    return True
