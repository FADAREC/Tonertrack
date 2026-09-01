"""local Windows printer name for USB/local checks

Revision ID: 010
Revises: 009
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if "printers" not in set(insp.get_table_names()):
        return
    cols = {c["name"] for c in insp.get_columns("printers")}
    if "local_name" not in cols:
        op.add_column("printers", sa.Column("local_name", sa.String(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if "printers" not in set(insp.get_table_names()):
        return
    cols = {c["name"] for c in insp.get_columns("printers")}
    if "local_name" in cols:
        op.drop_column("printers", "local_name")
