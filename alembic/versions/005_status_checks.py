"""status_checks trail

Revision ID: 005
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if "status_checks" not in set(insp.get_table_names()):
        op.create_table(
            "status_checks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("printer_id", sa.Integer(), sa.ForeignKey("printers.id"), nullable=False),
            sa.Column("source", sa.String(), nullable=True),
            sa.Column("ok", sa.Boolean(), nullable=True),
            sa.Column("status", sa.String(), nullable=True),
            sa.Column("toner_level", sa.Integer(), nullable=True),
            sa.Column("status_detail", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_status_checks_printer_id", "status_checks", ["printer_id"])
        op.create_index("ix_status_checks_created_at", "status_checks", ["created_at"])


def downgrade() -> None:
    op.drop_table("status_checks")
