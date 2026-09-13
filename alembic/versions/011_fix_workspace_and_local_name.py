"""ensure local_name column and workable RLS inserts

Revision ID: 011
Revises: 010
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "printers" in tables:
        cols = {c["name"] for c in insp.get_columns("printers")}
        if "local_name" not in cols:
            op.add_column("printers", sa.Column("local_name", sa.String(), nullable=True))

    if bind.dialect.name != "postgresql":
        return

    # Make workspace creation possible under FORCE RLS when bypass is set
    op.execute("SELECT set_config('app.rls_bypass', '1', true)")
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workspaces') THEN
            DROP POLICY IF EXISTS ws_isolation ON workspaces;
            CREATE POLICY ws_isolation ON workspaces
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR id::text = current_setting('app.workspace_id', true)
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR id::text = current_setting('app.workspace_id', true)
              );
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
            DROP POLICY IF EXISTS ws_isolation ON users;
            CREATE POLICY ws_isolation ON users
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR workspace_id::text = current_setting('app.workspace_id', true)
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR workspace_id::text = current_setting('app.workspace_id', true)
              );
          END IF;
        END $$;
        """
    )

    # Backfill users missing a workspace
    op.execute(
        """
        DO $$
        DECLARE r RECORD;
          new_ws INT;
        BEGIN
          FOR r IN SELECT id, username FROM users WHERE workspace_id IS NULL
          LOOP
            INSERT INTO workspaces (name) VALUES (r.username || '''s office') RETURNING id INTO new_ws;
            UPDATE users SET workspace_id = new_ws, role = COALESCE(NULLIF(role, ''), 'admin') WHERE id = r.id;
          END LOOP;
        END $$;
        """
    )


def downgrade() -> None:
    pass
