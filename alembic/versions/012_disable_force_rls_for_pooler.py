"""disable FORCE RLS so Supabase pooler signups can attach workspaces

App-level workspace_id filters remain the isolation boundary.
Revision ID: 012
Revises: 011
"""
from typing import Sequence, Union
from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(
        """
        DO $$
        DECLARE t text;
        BEGIN
          FOREACH t IN ARRAY ARRAY[
            'workspaces','users','printers','agent_tokens','settings','audit_events',
            'status_checks','helper_download_logs','alerts','jobs','trust_preferences'
          ]
          LOOP
            IF EXISTS (
              SELECT 1 FROM information_schema.tables
              WHERE table_schema = 'public' AND table_name = t
            ) THEN
              EXECUTE format('DROP POLICY IF EXISTS ws_isolation ON %I', t);
              EXECUTE format('ALTER TABLE %I NO FORCE ROW LEVEL SECURITY', t);
              EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', t);
            END IF;
          END LOOP;
        END $$;
        """
    )
    # Backfill any users still missing workspace
    op.execute(
        """
        DO $$
        DECLARE r RECORD;
          new_ws INT;
        BEGIN
          FOR r IN SELECT id, username FROM users WHERE workspace_id IS NULL
          LOOP
            INSERT INTO workspaces (name) VALUES (COALESCE(r.username, 'user') || '''s office')
              RETURNING id INTO new_ws;
            UPDATE users
              SET workspace_id = new_ws,
                  role = CASE WHEN role IS NULL OR role = '' THEN 'admin' ELSE role END
              WHERE id = r.id;
          END LOOP;
        END $$;
        """
    )


def downgrade() -> None:
    pass
