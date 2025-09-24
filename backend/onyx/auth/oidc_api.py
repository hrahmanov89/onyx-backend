from typing import Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from onyx.auth.oidc_providers import (
    CreateOIDCProviderRequest,
    OIDCProviderModel,
    oidc_registry,
    OIDCProviderConfig,
)

class UpdateOIDCProviderRequest(CreateOIDCProviderRequest):
    # All fields optional for PATCH-like semantics
    name: str | None = None
    display_name: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    openid_config_url: Optional[str] = None
    icon_url: Optional[str] = None
    scopes: Optional[List[str]] = None
    additional_params: Optional[Dict[str, str]] = None
from onyx.auth.users import current_admin_user
from onyx.db.models import User
from onyx.db.engine.sql_engine import get_session
from onyx.db.oidc_providers import (
    create_oidc_provider as db_create_oidc_provider,
    delete_oidc_provider as db_delete_oidc_provider,
    get_all_oidc_providers as db_get_all_oidc_providers,
    get_oidc_provider as db_get_oidc_provider,
    update_oidc_provider as db_update_oidc_provider,
)

router = APIRouter(prefix="/oidc-providers", tags=["oidc-providers"])  # Admin API for managing OIDC providers


@router.get("", response_model=List[OIDCProviderModel])
def get_oidc_providers(
    db: Session = Depends(get_session),
    _: User = Depends(current_admin_user),
) -> List[OIDCProviderModel]:
    """Get all registered OIDC providers (DB source of truth)."""
    providers: List[OIDCProviderModel] = []
    for p in db_get_all_oidc_providers(db):
        providers.append(
            OIDCProviderModel(
                name=p.name,
                display_name=p.display_name,
                icon_url=p.icon_url,
                openid_config_url=p.openid_config_url,
            )
        )
    return providers


@router.post("", response_model=OIDCProviderModel, status_code=status.HTTP_201_CREATED)
def create_oidc_provider(
    provider_data: CreateOIDCProviderRequest,
    db: Session = Depends(get_session),
    _: User = Depends(current_admin_user),
) -> OIDCProviderModel:
    """Create a new OIDC provider in DB and sync registry."""
    # Conflict if already exists
    if db_get_oidc_provider(db, provider_data.name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Provider with name {provider_data.name} already exists",
        )

    scopes = provider_data.scopes or ["openid", "email", "profile", "offline_access"]
    if "offline_access" not in scopes:
        scopes.append("offline_access")

    # Persist to DB
    created = db_create_oidc_provider(
        db_session=db,
        name=provider_data.name,
        display_name=provider_data.display_name,
        client_id=provider_data.client_id,
        client_secret=provider_data.client_secret,
        openid_config_url=provider_data.openid_config_url,
        icon_url=provider_data.icon_url,
        scopes=scopes,
        additional_params=provider_data.additional_params,
    )

    # Sync in-memory registry
    reg_cfg = OIDCProviderConfig(
        name=created.name,
        client_id=created.client_id,
        client_secret=created.client_secret,
        openid_config_url=created.openid_config_url,
        scopes=created.scopes,
        additional_params=created.additional_params,
    )
    oidc_registry.register_provider(reg_cfg)

    return OIDCProviderModel(
        name=created.name,
        display_name=created.display_name,
        icon_url=created.icon_url,
        openid_config_url=created.openid_config_url,
    )


@router.put("/{provider_name}", response_model=OIDCProviderModel)
@router.patch("/{provider_name}", response_model=OIDCProviderModel)
def update_oidc_provider(
    provider_name: str,
    provider_update: UpdateOIDCProviderRequest,
    db: Session = Depends(get_session),
    _: User = Depends(current_admin_user),
) -> OIDCProviderModel:
    """Update an existing OIDC provider and sync registry."""
    existing = db_get_oidc_provider(db, provider_name)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

    # Compute new scopes, ensuring offline_access is present if scopes provided
    new_scopes = provider_update.scopes if provider_update.scopes is not None else None
    if new_scopes is not None and "offline_access" not in new_scopes:
        new_scopes.append("offline_access")

    updated = db_update_oidc_provider(
        db_session=db,
        name=provider_name,
        display_name=provider_update.display_name,
        client_id=provider_update.client_id,
        client_secret=provider_update.client_secret,
        openid_config_url=provider_update.openid_config_url,
        icon_url=provider_update.icon_url,
        scopes=new_scopes,
        additional_params=provider_update.additional_params,
    )
    assert updated is not None

    # Sync in-memory registry
    reg_cfg = OIDCProviderConfig(
        name=updated.name,
        client_id=updated.client_id,
        client_secret=updated.client_secret,
        openid_config_url=updated.openid_config_url,
        scopes=updated.scopes,
        additional_params=updated.additional_params,
    )
    oidc_registry.register_provider(reg_cfg)

    return OIDCProviderModel(
        name=updated.name,
        display_name=updated.display_name,
        icon_url=updated.icon_url,
        openid_config_url=updated.openid_config_url,
    )


@router.delete("/{provider_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_oidc_provider(
    provider_name: str,
    db: Session = Depends(get_session),
    _: User = Depends(current_admin_user),
) -> None:
    """Delete an OIDC provider (prevent deleting last provider)."""
    # Prevent delete of last provider to avoid lockout
    all_providers = db_get_all_oidc_providers(db)
    if len(all_providers) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last remaining provider",
        )

    if not db_delete_oidc_provider(db, provider_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider with name {provider_name} not found",
        )

    # Sync in-memory registry (ignore if absent)
    try:
        oidc_registry.providers.pop(provider_name, None)
    except Exception:
        pass
