from typing import List
import logging
from onyx.db.engine.sql_engine import get_session_with_current_tenant
from onyx.db.oidc_providers import get_all_oidc_providers
from onyx.auth.oidc_providers import OIDCProviderConfig, oidc_registry
from shared_configs.configs import MULTI_TENANT, POSTGRES_DEFAULT_SCHEMA

logger = logging.getLogger(__name__)

def load_oidc_providers_from_db() -> List[str]:
    """Load OIDC providers from the database into the in-memory registry.
    Returns list of provider names loaded. Swallows errors (returns empty list) if table missing or other issues.
    """
    loaded: List[str] = []
    try:
        # Single-tenant path first; multi-tenant will require iterating schemas (future work)
        if MULTI_TENANT:
            return []  # Skip for now
        with get_session_with_current_tenant() as db_session:
            db_providers = get_all_oidc_providers(db_session)
            for p in db_providers:
                # ensure additional_params is dict
                add_params = p.additional_params or {}
                scopes = p.scopes or ["openid", "email", "profile", "offline_access"]
                if "offline_access" not in scopes:
                    scopes.append("offline_access")
                cfg = OIDCProviderConfig(
                    name=p.name,
                    client_id=p.client_id,
                    client_secret=p.client_secret,
                    openid_config_url=p.openid_config_url,
                    scopes=scopes,
                    additional_params=add_params,
                )
                oidc_registry.register_provider(cfg)
                loaded.append(p.name)
        if loaded:
            logger.info("Loaded %d OIDC providers from DB: %s", len(loaded), ",".join(loaded))
    except Exception as e:  # broad catch to avoid startup failure
        logger.debug("Skipping DB OIDC provider load: %s", e)
        return []
    return loaded
