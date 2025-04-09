import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import os

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
section = config.config_ini_section

print("--- Alembic env.py Debug Info ---")
print(f"Current working directory (os.getcwd()): {os.getcwd()}")
print(f"Path to env.py (os.path.abspath(__file__)): {os.path.abspath(__file__)}")

current_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Directory of env.py (current_dir): {current_dir}")

# ИЗМЕНЕНИЕ ЗДЕСЬ: Поднимаемся на два уровня вверх, чтобы получить 'remindme/'
# current_dir = .../remindme/backend/alembic
# os.path.join(current_dir, "..") = .../remindme/backend
# os.path.join(current_dir, "..", "..") = .../remindme
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
print(f"Calculated project root (project_root): {project_root}")

# Добавляем корневую директорию проекта (remindme/) в sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added '{project_root}' to sys.path.")
else:
    print(f"'{project_root}' already in sys.path.")

print("\n--- sys.path AFTER modification ---")
for p in sys.path:
    print(f"  - {p}")
print("----------------------------------\n")

# Подставляем значения из переменных окружения
config.set_section_option(section, "DB_USER", os.environ.get("POSTGRES_USER", "postgres"))
config.set_section_option(section, "DB_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "postgres"))
config.set_section_option(section, "DB_HOST", os.environ.get("POSTGRES_ADDRESS", "localhost"))
config.set_section_option(section, "DB_PORT", os.environ.get("POSTGRES_PORT", "5432"))
config.set_section_option(section, "DB_NAME", os.environ.get("POSTGRES_DB", "remind_me"))


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

from backend.control_plane.db.models import BaseModel
target_metadata = BaseModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
