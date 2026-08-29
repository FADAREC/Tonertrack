"""index printers by workspace for fast lists

Revision ID: 008
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = set(insp.get_table_names())
    if "printers" not in tables:
        return
    # Hide orphan rows with null workspace from every tenant (no owner)
    # (filter is in app; index speeds workspace lists)
    try:
        op.create_index(
            "ix_printers_workspace_id_id",
            "printers",
            ["workspace_id", "id"],
            unique=False,
        )
    except Exception:
        pass
    try:
        op.create_index(
            "ix_users_workspace_id",
            "users",
            ["workspace_id"],
            unique=False,
        )
    except Exception:
        pass


def downgrade() -> None:
    pass
