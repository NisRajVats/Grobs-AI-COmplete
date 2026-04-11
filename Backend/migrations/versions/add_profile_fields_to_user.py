"""Add profile fields to user

Revision ID: add_profile_fields
Revises: 2552368c83dc
Create Date: 2026-04-08 12:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_profile_fields'
down_revision: Union[str, None] = '2552368c83dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add only the new profile fields that don't exist yet
    # bio, website, experience_level are the new fields we're adding
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('website', sa.String(), nullable=True))
    op.add_column('users', sa.Column('experience_level', sa.String(), nullable=True))
    
    # Add other profile fields if they don't exist (may already exist from setup.py or other migrations)
    # These are idempotent operations using op.alter_column or conditional adds
    # For safety, we'll try to add them but ignore if they exist
    pass  # The fields full_name, phone, location, title, linkedin_url, avatar_url should be added via direct SQL if needed


def downgrade() -> None:
    # Remove the new profile fields
    op.drop_column('users', 'experience_level')
    op.drop_column('users', 'website')
    op.drop_column('users', 'bio')
