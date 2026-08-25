"""helper download log and token download flag

Revision ID: 003
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = set(insp.get_table_names())
    cols = {c["name"] for c in insp.get_columns("agent_tokens")} if "agent_tokens" in tables else set()

    if "helper_download_enabled" not in cols and "agent_tokens" in tables:
        op.add_column(
            "agent_tokens",
            sa.Column("helper_download_enabled", sa.Boolean(), server_default="false", nullable=False),
        )

    if "helper_download_logs" not in tables:
        op.create_table(
            "helper_download_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("token_id", sa.Integer(), sa.ForeignKey("agent_tokens.id"), nullable=True),
            sa.Column("token_prefix", sa.String(), nullable=True),
            sa.Column("actor", sa.String(), nullable=True),
            sa.Column("success", sa.Boolean(), nullable=True),
            sa.Column("detail", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    pass
