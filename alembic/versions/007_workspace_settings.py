"""per-workspace settings and audit

Revision ID: 007
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = set(insp.get_table_names())

    def cols(table):
        return {c["name"] for c in insp.get_columns(table)} if table in tables else set()

    if "settings" in tables:
        c = cols("settings")
        if "workspace_id" not in c:
            op.add_column("settings", sa.Column("workspace_id", sa.Integer(), nullable=True))
        # Drop global unique on key if present (best-effort)
        try:
            op.drop_constraint("settings_key_key", "settings", type_="unique")
        except Exception:
            pass
        try:
            op.create_index("ix_settings_workspace_key", "settings", ["workspace_id", "key"], unique=True)
        except Exception:
            pass

    if "audit_events" in tables:
        c = cols("audit_events")
        if "workspace_id" not in c:
            op.add_column("audit_events", sa.Column("workspace_id", sa.Integer(), nullable=True))

    # Attach orphan settings to first workspace if any
    conn.execute(sa.text(
        "UPDATE settings SET workspace_id = (SELECT id FROM workspaces ORDER BY id LIMIT 1) "
        "WHERE workspace_id IS NULL AND EXISTS (SELECT 1 FROM workspaces LIMIT 1)"
    ))


def downgrade() -> None:
    pass
