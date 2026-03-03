"""merge heads

Revision ID: 1828fd946d29
Revises: 9da4fdea2721, cc34e0c2349c
Create Date: 2026-03-03 15:10:42.874589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1828fd946d29'
down_revision: Union[str, Sequence[str], None] = ('9da4fdea2721', 'cc34e0c2349c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
