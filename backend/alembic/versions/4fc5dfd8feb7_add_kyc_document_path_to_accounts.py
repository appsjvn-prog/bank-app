"""add kyc_document_path to accounts

Revision ID: 707abc123def
Revises: 60638000617e
Create Date: 2026-02-08 18:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '707abc123def'
down_revision = '60638000617e'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('accounts', sa.Column('kyc_document_path', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('accounts', 'kyc_document_path')
