"""workspaces and resource scoping

Revision ID: 006
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = set(insp.get_table_names())

    if "workspaces" not in tables:
        op.create_table(
            "workspaces",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False, server_default="My office"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    def add_col(table, col, coltype):
        cols = {c["name"] for c in insp.get_columns(table)}
        if col not in cols:
            op.add_column(table, sa.Column(col, coltype, nullable=True))

    if "users" in tables:
        add_col("users", "workspace_id", sa.Integer())
    if "printers" in tables:
        add_col("printers", "workspace_id", sa.Integer())
    if "agent_tokens" in tables:
        add_col("agent_tokens", "workspace_id", sa.Integer())

    # Backfill: one legacy workspace for existing rows
    conn.execute(
        sa.text(
            "INSERT INTO workspaces (name, created_at) "
            "SELECT 'Legacy office', CURRENT_TIMESTAMP "
            "WHERE NOT EXISTS (SELECT 1 FROM workspaces LIMIT 1)"
        )
    )
    conn.execute(sa.text(
        "UPDATE users SET workspace_id = (SELECT id FROM workspaces ORDER BY id LIMIT 1) "
        "WHERE workspace_id IS NULL"
    ))
    conn.execute(sa.text(
        "UPDATE printers SET workspace_id = (SELECT id FROM workspaces ORDER BY id LIMIT 1) "
        "WHERE workspace_id IS NULL"
    ))
    conn.execute(sa.text(
        "UPDATE agent_tokens SET workspace_id = (SELECT id FROM workspaces ORDER BY id LIMIT 1) "
        "WHERE workspace_id IS NULL"
    ))


def downgrade() -> None:
    pass
