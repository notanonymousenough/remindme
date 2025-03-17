import asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine  # Изменено: импорт async engine

from alembic import context

# ... (остальные импорты из вашего env.py, например, модели) ...

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# ... (настройка логирования, если есть) ...

# добавьте импорт ваших моделей здесь, чтобы autogenerate работал правильно
# from yourapp import models
# target_metadata = models.Base.metadata
from backend.control_plane.db.engine import Base  # Пример, замените на ваши модели
target_metadata = Base.metadata


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


def do_run_migrations(connection): # Изменено: убрали async
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None: # Изменено: добавили async
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_async_engine(  # Изменено: используем async engine
        config.get_main_option("sqlalchemy.url"), poolclass=pool.NullPool
    )

    async with connectable.connect() as connection: # Изменено: async with и await
        await connection.run_sync(do_run_migrations) # Изменено: await и run_sync

    await connectable.dispose() # Добавлено: закрытие async engine


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online()) # Изменено: запускаем async функцию через asyncio.run()