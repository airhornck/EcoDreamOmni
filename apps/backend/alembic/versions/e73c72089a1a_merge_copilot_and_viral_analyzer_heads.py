"""merge_copilot_and_viral_analyzer_heads

Revision ID: e73c72089a1a
Revises: 20260604addc, h3i4j5k6l7m8
Create Date: 2026-06-05 23:07:01.300634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e73c72089a1a'
down_revision: Union[str, Sequence[str], None] = ('20260604addc', 'h3i4j5k6l7m8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
