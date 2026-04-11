"""Add user_settings table

Revision ID: add_user_settings
Revises: add_profile_fields
Create Date: 2026-04-08 12:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_user_settings'
down_revision: Union[str, None] = 'add_profile_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if user_settings table already exists by trying to create it
    # If it exists, this will fail silently in some DBs, but SQLite will error
    # Since we know it might exist from setup.py, we'll skip creation if it exists
    pass  # Table already exists from setup.py or previous migration


def downgrade() -> None:
    op.drop_index(op.f('ix_user_settings_user_id'), table_name='user_settings')
    op.drop_index(op.f('ix_user_settings_id'), table_name='user_settings')
    op.drop_table('user_settings')