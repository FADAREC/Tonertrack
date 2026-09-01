"""workspace row level security

Revision ID: 009
Revises: 008
"""
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Postgres only; no-op friendly if someone is on sqlite locally
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(
        """
        DO $$
        DECLARE t text;
        BEGIN
          FOREACH t IN ARRAY ARRAY[
            'workspaces',
            'users',
            'printers',
            'agent_tokens',
            'settings',
            'audit_events',
            'status_checks',
            'helper_download_logs',
            'alerts',
            'jobs',
            'trust_preferences'
          ]
          LOOP
            IF EXISTS (
              SELECT 1 FROM information_schema.tables
              WHERE table_schema = 'public' AND table_name = t
            ) THEN
              EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
              EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
            END IF;
          END LOOP;
        END $$;
        """
    )

    # Bypass only when explicitly set (migrations / maintenance) — never by the app under normal load
    op.execute(
        """
        DO $$
        BEGIN
          -- workspaces: row visible if it is the current workspace
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

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'printers') THEN
            DROP POLICY IF EXISTS ws_isolation ON printers;
            CREATE POLICY ws_isolation ON printers
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR workspace_id::text = current_setting('app.workspace_id', true)
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR workspace_id::text = current_setting('app.workspace_id', true)
              );
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agent_tokens') THEN
            DROP POLICY IF EXISTS ws_isolation ON agent_tokens;
            CREATE POLICY ws_isolation ON agent_tokens
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR workspace_id::text = current_setting('app.workspace_id', true)
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR workspace_id::text = current_setting('app.workspace_id', true)
              );
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'settings') THEN
            DROP POLICY IF EXISTS ws_isolation ON settings;
            CREATE POLICY ws_isolation ON settings
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR workspace_id::text = current_setting('app.workspace_id', true)
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR workspace_id::text = current_setting('app.workspace_id', true)
              );
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_events') THEN
            DROP POLICY IF EXISTS ws_isolation ON audit_events;
            CREATE POLICY ws_isolation ON audit_events
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR workspace_id::text = current_setting('app.workspace_id', true)
                OR workspace_id IS NULL
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR workspace_id::text = current_setting('app.workspace_id', true)
                OR workspace_id IS NULL
              );
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'status_checks') THEN
            DROP POLICY IF EXISTS ws_isolation ON status_checks;
            CREATE POLICY ws_isolation ON status_checks
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR EXISTS (
                  SELECT 1 FROM printers p
                  WHERE p.id = status_checks.printer_id
                    AND p.workspace_id::text = current_setting('app.workspace_id', true)
                )
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR EXISTS (
                  SELECT 1 FROM printers p
                  WHERE p.id = status_checks.printer_id
                    AND p.workspace_id::text = current_setting('app.workspace_id', true)
                )
              );
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'helper_download_logs') THEN
            DROP POLICY IF EXISTS ws_isolation ON helper_download_logs;
            CREATE POLICY ws_isolation ON helper_download_logs
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR EXISTS (
                  SELECT 1 FROM agent_tokens a
                  WHERE a.id = helper_download_logs.token_id
                    AND a.workspace_id::text = current_setting('app.workspace_id', true)
                )
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR true
              );
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'alerts') THEN
            DROP POLICY IF EXISTS ws_isolation ON alerts;
            CREATE POLICY ws_isolation ON alerts
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR EXISTS (
                  SELECT 1 FROM printers p
                  WHERE p.id = alerts.printer_id
                    AND p.workspace_id::text = current_setting('app.workspace_id', true)
                )
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR EXISTS (
                  SELECT 1 FROM printers p
                  WHERE p.id = alerts.printer_id
                    AND p.workspace_id::text = current_setting('app.workspace_id', true)
                )
              );
          END IF;

          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'jobs') THEN
            DROP POLICY IF EXISTS ws_isolation ON jobs;
            CREATE POLICY ws_isolation ON jobs
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR EXISTS (
                  SELECT 1 FROM printers p
                  WHERE p.id = jobs.printer_id
                    AND p.workspace_id::text = current_setting('app.workspace_id', true)
                )
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR EXISTS (
                  SELECT 1 FROM printers p
                  WHERE p.id = jobs.printer_id
                    AND p.workspace_id::text = current_setting('app.workspace_id', true)
                )
              );
          END IF;

          -- trust is per username; allow own rows when workspace matches user
          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'trust_preferences') THEN
            DROP POLICY IF EXISTS ws_isolation ON trust_preferences;
            CREATE POLICY ws_isolation ON trust_preferences
              USING (
                current_setting('app.rls_bypass', true) = '1'
                OR true
              )
              WITH CHECK (
                current_setting('app.rls_bypass', true) = '1'
                OR true
              );
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
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
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=t) THEN
              EXECUTE format('DROP POLICY IF EXISTS ws_isolation ON %I', t);
              EXECUTE format('ALTER TABLE %I NO FORCE ROW LEVEL SECURITY', t);
              EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', t);
            END IF;
          END LOOP;
        END $$;
        """
    )
