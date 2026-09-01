from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

load_dotenv()
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

url = os.getenv("DATABASE_URL", "sqlite:///./printers.db")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)
config.set_main_option("sqlalchemy.url", url)

from database import Base
import models  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # Migrations must see all rows even after FORCE RLS is enabled
        if connection.dialect.name == "postgresql":
            connection.exec_driver_sql("SELECT set_config('app.rls_bypass', '1', false)")
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
