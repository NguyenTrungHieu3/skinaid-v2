"""
Add last_active_at to users table

Revision ID: 20260401_add_last_active_at
Revises: 20260328_add_model_tracking_fields
Create Date: 2026-04-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260401_add_last_active_at'
down_revision = '20260328_add_model_tracking_fields'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add last_active_at column
    op.add_column(
        'users',
        sa.Column(
            'last_active_at',
            sa.DateTime(),
            nullable=True,
            comment='When this user was last active'
        )
    )

def downgrade() -> None:
    # Remove last_active_at column
    op.drop_column('users', 'last_active_at')
