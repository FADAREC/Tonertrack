"""two clock status fields on printers

Revision ID: 001
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = {c["name"] for c in insp.get_columns("printers")} if "printers" in insp.get_table_names() else set()

    def add(col, coltype):
        if col not in cols:
            op.add_column("printers", sa.Column(col, coltype, nullable=True))

    add("status_detail", sa.String())
    add("last_verified_at", sa.DateTime())
    add("last_attempt_at", sa.DateTime())
    if "fail_streak" not in cols:
        op.add_column("printers", sa.Column("fail_streak", sa.Integer(), server_default="0", nullable=False))

    # Backfill from contaminated last_checked - known imperfect
    if "last_checked" in cols:
        op.execute(
            sa.text(
                "UPDATE printers SET last_verified_at = last_checked "
                "WHERE last_verified_at IS NULL AND last_checked IS NOT NULL"
            )
        )
        op.execute(
            sa.text(
                "UPDATE printers SET last_attempt_at = last_checked "
                "WHERE last_attempt_at IS NULL AND last_checked IS NOT NULL"
            )
        )

    # Allow null last_checked going forward (best-effort; SQLite limited)
    try:
        op.alter_column("printers", "last_checked", existing_type=sa.DateTime(), nullable=True)
    except Exception:
        pass

    alert_cols = set()
    if "alerts" in insp.get_table_names():
        alert_cols = {c["name"] for c in insp.get_columns("alerts")}
    if "alerts" in insp.get_table_names() and "alert_type" not in alert_cols:
        op.add_column("alerts", sa.Column("alert_type", sa.String(), server_default="low_toner", nullable=True))


def downgrade() -> None:
    # Non-destructive downgrade omitted for pilot
    pass
