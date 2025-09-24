from typing import Dict, List, Optional
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

from onyx.db.models import Base

class OIDCProviderConfig(Base):
    __tablename__ = "oidc_provider_config"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    display_name = Column(String, nullable=False)
    client_id = Column(String, nullable=False)
    client_secret = Column(String, nullable=False)
    openid_config_url = Column(String, nullable=False)
    icon_url = Column(String, nullable=True)
    scopes = Column(JSONB, nullable=False, default=list)
    additional_params = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
