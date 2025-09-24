import os
import logging
from fastapi import APIRouter

from onyx.auth.users import auth_backend, create_onyx_oauth_router, fastapi_users, USER_AUTH_SECRET
from onyx.auth.oidc_providers import create_oidc_client, oidc_registry, setup_default_oidc_provider, OIDCProviderConfig
from onyx.configs.app_configs import WEB_DOMAIN

logger = logging.getLogger(__name__)


def setup_oidc_auth(application):
    """Set up OIDC authentication with support for multiple providers.

    Consolidated implementation. Supports env override for redirect URLs.
    """
    # Load providers from DB if available else env default
    from onyx.auth.oidc_loader import load_oidc_providers_from_db  # local import to avoid circular
    try:
        loaded = load_oidc_providers_from_db()
        if not loaded:
            setup_default_oidc_provider()
    except Exception:
        # Fallback to env default if DB not ready
        setup_default_oidc_provider()

    oidc_router = APIRouter()

    @oidc_router.get("/providers", include_in_schema=False)
    def list_oidc_providers():
        providers = []
        for name, _ in oidc_registry.get_all_providers().items():
            providers.append(
                {
                    "name": name,
                    "display_name": name.capitalize(),
                    "authorize_url": f"/auth/oidc/{name}/authorize",
                }
            )
        return providers

    env_override = os.environ.get("OIDC_REDIRECT_URL")

    for provider_name, _ in oidc_registry.get_all_providers().items():
        oidc_client = create_oidc_client(provider_name)
        if not oidc_client:
            logger.warning(
                "Skipping OIDC provider '%s' (initialization failed)", provider_name
            )
            continue

        # Default per-provider redirect
        redirect_url = f"{WEB_DOMAIN}/auth/oidc/{provider_name}/callback"
        if env_override:
            if "{provider}" in env_override:
                redirect_url = env_override.replace("{provider}", provider_name)
            else:
                redirect_url = env_override
        logger.info(
            "OIDC provider '%s' redirect_url=%s", provider_name, redirect_url
        )

        provider_router = create_onyx_oauth_router(
            oauth_client=oidc_client,
            backend=auth_backend,
            state_secret=USER_AUTH_SECRET,
            redirect_url=redirect_url,
            associate_by_email=True,
            is_verified_by_default=True,
        )
        oidc_router.include_router(provider_router, prefix=f"/{provider_name}")

    application.include_router(
        fastapi_users.get_logout_router(auth_backend), prefix="/auth"
    )
    application.include_router(oidc_router, prefix="/auth/oidc")
