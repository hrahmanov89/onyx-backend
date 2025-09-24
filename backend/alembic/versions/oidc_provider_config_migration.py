"""Add OIDC provider configuration table

Revision ID: oidc_provider_config
Revises: b558f51620b4
Create Date: 2025-08-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4


# revision identifiers, used by Alembic.
revision = 'oidc_provider_config'
down_revision = 'b558f51620b4'  # Current head revision ID
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'oidc_provider_config',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('client_secret', sa.String(), nullable=False),
        sa.Column('openid_config_url', sa.String(), nullable=False),
        sa.Column('icon_url', sa.String(), nullable=True),
        sa.Column('scopes', JSONB, nullable=False, default=list),
        sa.Column('additional_params', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )


def downgrade():
    op.drop_table('oidc_provider_config')
