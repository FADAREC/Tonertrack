"""site visits table

Revision ID: 004
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if "site_visits" not in set(insp.get_table_names()):
        op.create_table(
            "site_visits",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("path", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_site_visits_path", "site_visits", ["path"])
        op.create_index("ix_site_visits_created_at", "site_visits", ["created_at"])


def downgrade() -> None:
    op.drop_table("site_visits")
