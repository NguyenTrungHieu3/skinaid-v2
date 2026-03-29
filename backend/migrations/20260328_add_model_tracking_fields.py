"""
Add activated_at and previously_active_version_id to ai_models table

Revision ID: 20260328_add_model_tracking_fields
Revises: migration_complete_ai_models
Create Date: 2026-03-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260328_add_model_tracking_fields'
down_revision = 'migration_complete_ai_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add tracking fields for model activation history:
    1. activated_at: timestamp when version was activated
    2. previously_active_version_id: FK to previous active version (for rollback)
    3. Add unique constraint on (model_type, version_tag)
    """
    
    # Step 1: Add activated_at column
    # This tracks when a version became active (different from created_at)
    op.add_column(
        'ai_models',
        sa.Column(
            'activated_at',
            sa.DateTime(),
            nullable=True,
            comment='When this version was activated'
        )
    )
    
    # Step 2: Add previously_active_version_id column (self-referential FK)
    # This enables rollback by tracking which version was active before
    op.add_column(
        'ai_models',
        sa.Column(
            'previously_active_version_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='ID of the previously active version (for rollback tracking)'
        )
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_ai_models_previously_active',
        'ai_models',  # child table
        'ai_models',  # parent table (self-reference)
        'previously_active_version_id',  # child column
        'model_id',  # parent column
        ondelete='SET NULL'
    )
    
    # Step 3: Add unique constraint on (model_type, version_tag)
    # This prevents duplicate version tags within the same model type
    op.create_unique_constraint(
        'uq_ai_models_type_version',
        'ai_models',
        ['model_type', 'version_tag']
    )
    
    # Step 4: Create index on activated_at for performance
    op.create_index(
        'ix_ai_models_activated_at',
        'ai_models',
        ['activated_at'],
        unique=False
    )
    
    # Step 5: Create index on previously_active_version_id for joins
    op.create_index(
        'ix_ai_models_prev_active',
        'ai_models',
        ['previously_active_version_id'],
        unique=False
    )


def downgrade() -> None:
    """
    Remove tracking fields.
    Note: This will lose activation history data.
    """
    
    # Drop indexes
    op.drop_index('ix_ai_models_prev_active', table_name='ai_models')
    op.drop_index('ix_ai_models_activated_at', table_name='ai_models')
    
    # Drop unique constraint
    op.drop_constraint('uq_ai_models_type_version', 'ai_models', type_='unique')
    
    # Drop foreign key
    op.drop_constraint('fk_ai_models_previously_active', 'ai_models', type_='foreignkey')
    
    # Drop columns
    op.drop_column('ai_models', 'previously_active_version_id')
    op.drop_column('ai_models', 'activated_at')
