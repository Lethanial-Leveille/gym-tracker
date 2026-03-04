"""sessions add title and nullable workout_id

Revision ID: 7d22ef5ad7f2
Revises: 1828fd946d29
Create Date: 2026-03-03 19:41:40.587579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d22ef5ad7f2'
down_revision: Union[str, Sequence[str], None] = '1828fd946d29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Add column as nullable first
    op.add_column("workout_sessions", sa.Column("title", sa.String(), nullable=True))

    # 2) Backfill existing rows
    op.execute("UPDATE workout_sessions SET title = 'Workout' WHERE title IS NULL")

    # 3) Make it NOT NULL
    op.alter_column("workout_sessions", "title", nullable=False)

    # 4) Make workout_id nullable (autogen probably already did this part)
    op.alter_column("workout_sessions", "workout_id", existing_type=sa.INTEGER(), nullable=True)


def downgrade() -> None:
    # Put it back how it was
    op.alter_column("workout_sessions", "workout_id", existing_type=sa.INTEGER(), nullable=False)
    op.drop_column("workout_sessions", "title")
