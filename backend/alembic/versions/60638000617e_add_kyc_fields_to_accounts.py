"""add kyc fields to accounts

Revision ID: 60638000617e
Revises: ce94b9dc1f64
Create Date: 2026-02-07 23:55:26.538450

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60638000617e'
down_revision: Union[str, Sequence[str], None] = 'ce94b9dc1f64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('accounts', sa.Column('aadhaar_hash', sa.String(255), nullable=True))
    op.add_column('accounts', sa.Column('aadhaar_masked', sa.String(20), nullable=True))
    op.add_column('accounts', sa.Column('pan_hash', sa.String(255), nullable=True))
    op.add_column('accounts', sa.Column('pan_masked', sa.String(20), nullable=True))
    op.add_column(
        'accounts',
        sa.Column(
            'kyc_status',
            sa.String(20),
            nullable=False,
            server_default='not_submitted'
        )
    )

def downgrade():
    op.drop_column('accounts', 'kyc_status')
    op.drop_column('accounts', 'pan_masked')
    op.drop_column('accounts', 'pan_hash')
    op.drop_column('accounts', 'aadhaar_masked')
    op.drop_column('accounts', 'aadhaar_hash')

