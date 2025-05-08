import logging
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio # Используем pytest_asyncio для асинхронных фикстур
import asyncio
import os
from pathlib import Path
from unittest.mock import patch, AsyncMock

import temporalio
from sqlalchemy import create_engine
from temporalio.bridge.temporal_sdk_bridge import start_dev_server
from temporalio.bridge.testing import DevServerConfig
from temporalio.workflow import instance
# --- Database Setup (using testcontainers) ---
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

# --- Temporal Setup ---
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

# --- Project Imports (Adjust paths as needed) ---
# Import workflows and activities to register them with the worker
from backend.data_plane.workflows.reminders import CheckRemindersWorkflow, SendReminderNotificationWorkflow
from backend.data_plane.activities.reminders import check_active_reminders, send_telegram_notification, abort_sent
from backend.control_plane.db.models.base import BaseModel as SQLAlchemyBaseModel # Import your SQLAlchemy Base
from backend.config import get_settings # We might need original settings for DB connection

# --- Configuration ---
# Find the root directory of your project (assuming conftest.py is in tests/integration)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"
print(Path(__file__))
print(PROJECT_ROOT)
print(ALEMBIC_INI_PATH)
# --- Настроим логирование для temporalio ---
logging.getLogger("temporalio").setLevel(logging.INFO)
logging.getLogger("temporalio.activity").setLevel(logging.DEBUG) # Включим дебаг для активностей
logging.getLogger("temporalio.worker").setLevel(logging.DEBUG) # И для воркера
logging.getLogger("temporalio.client").setLevel(logging.INFO)
logging.getLogger("temporalio.service").setLevel(logging.INFO)

# --- Database Fixture ---
@pytest_asyncio.fixture(scope="session")
async def test_database_container():
    """Запускает контейнер PostgreSQL для сессии тестов."""
    # Ensure the image is specified if not using default 'postgres'
    pg_container = PostgresContainer("postgres:15")
    with pg_container as postgres:
        yield postgres # Yield the container object

@pytest_asyncio.fixture(scope="session")
async def test_db_engine(test_database_container):
    """
    Создает ASYNC SQLAlchemy engine для тестов и применяет миграции Alembic,
    используя ВРЕМЕННОЕ СИНХРОННОЕ соединение для самого Alembic.
    """
    # --- Создаем ASYNC engine для использования в тестах ---
    async_db_url = test_database_container.get_connection_url().replace("psycopg2", "asyncpg")
    async_engine = create_async_engine(async_db_url, echo=False)

    # --- Создаем СИНХРОННЫЙ URL и engine ТОЛЬКО для Alembic ---
    # Заменяем asyncpg обратно на psycopg2 (или другой синхронный драйвер)
    sync_db_url = test_database_container.get_connection_url()
    # Убедимся, что используется стандартный psycopg2 или pg8000, если они указаны в get_connection_url()
    if 'asyncpg' in sync_db_url: # На всякий случай, если get_connection_url отдаст asyncpg
        sync_db_url = sync_db_url.replace('asyncpg', 'psycopg2')
    sync_engine = create_engine(sync_db_url) # Используем синхронный create_engine

    # --- Запускаем миграции Alembic с СИНХРОННЫМ engine ---
    class TestSettings: # Эта заглушка может и не понадобиться, если env.py не используется Alembic напрямую
        DATABASE_URI = sync_db_url # Теоретически, для Alembic важен sync URL

    # Патч get_settings (если ваш env.py его использует)
    # Лучше патчить там, где он используется в alembic/env.py, если это возможно
    with patch('backend.config.get_settings', return_value=TestSettings(), create=True):
        print(f"Loading Alembic config from: {ALEMBIC_INI_PATH}")
        alembic_cfg = Config(str(ALEMBIC_INI_PATH))

        # --- ГЛАВНОЕ ИЗМЕНЕНИЕ: Передаем СИНХРОННЫЙ URL в Alembic ---
        print(f"Setting Alembic sqlalchemy.url to SYNCHRONOUS: {sync_db_url}")
        alembic_cfg.set_main_option("sqlalchemy.url", sync_db_url)
        # -------------------------------------------------------------

        print(f"Running Alembic migrations up to head using synchronous connection...")
        try:
            # Выполняем команду upgrade - она синхронная
            command.upgrade(alembic_cfg, "head")
            print("Alembic migrations applied successfully using synchronous connection.")
        except Exception as e:
            print(f"Error running Alembic migrations: {e}")
            # Можно добавить вывод списка ревизий для диагностики
            # try: command.history(alembic_cfg)
            # except Exception as he: print(f"Could not get Alembic history: {he}")
            raise
        finally:
            # Закрываем синхронное соединение после миграций
            sync_engine.dispose()

    # --- Возвращаем ASYNC engine для использования в тестах ---
    yield async_engine

    # Teardown: Освобождаем ресурсы асинхронного движка
    await async_engine.dispose()

@pytest.fixture(scope="session")
def test_session_maker(test_db_engine):
    """Создает async_sessionmaker, привязанную к тестовому движку."""
    # Используйте async_sessionmaker вместо старого sessionmaker
    return async_sessionmaker(
        bind=test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

@pytest_asyncio.fixture(scope="function")
async def db_session(test_session_maker): # Используем новую фабрику
    """Создает сессию SQLAlchemy для теста (с транзакцией и откатом)."""
    async with test_session_maker() as session:
        # Начинаем транзакцию явно, чтобы управлять ею
        await session.begin()
        try:
            yield session
        finally:
            # Откатываем транзакцию после теста
            await session.rollback()
            # Сессия закроется автоматически благодаря async with

# --- Temporal Fixture ---
# @pytest_asyncio.fixture(scope="session")
# async def temporal_test_environment():
#     """Запускает локальное тестовое окружение Temporal."""
#     # Uses Ephemeral Server (in-memory) by default
#     # Or use start_local() to run temporalite if needed
#     # env = await WorkflowEnvironment.start_local()
#     env = await WorkflowEnvironment.start_time_skipping() # Time skipping is useful!
#     yield env
#     # Teardown is handled by WorkflowEnvironment context manager (if used with 'async with')
#     # or explicitly if needed: await env.shutdown()

@pytest_asyncio.fixture(scope="session")
async def temporal_dev_server():
    print("\nStarting Temporal dev server (temporalite)...")
    server = None
    try:
        # исправлено!
        runtime = instance()
        config = DevServerConfig()  # Можно указать порт, namespace и т.д.
        server = await start_dev_server(runtime, config)
        print(f"Temporal dev server started:")
        print(f"  Target:    {server.target_host}")
        print(f"  Namespace: {server.namespace}")
        ui_port = 8233 if ':7233' in server.target_host else 'N/A'
        if ui_port != 'N/A':
            print(f"  Likely UI: http://localhost:{ui_port}")
        else:
            print(f"  UI port cannot be determined automatically.")
        yield server
    except Exception as e:
        import traceback
        traceback.print_exc()
        pytest.fail(f"Could not start Temporal dev server: {e}")
    finally:
        if server:
            print("\nShutting down Temporal dev server...")
            await server.close()
            print("Temporal dev server closed.")

@pytest_asyncio.fixture(scope="session")
async def temporal_client(temporal_dev_server):
    client = await Client.connect(
        temporal_dev_server.target_host,
        namespace=temporal_dev_server.namespace,
    )
    try:
        yield client
    finally:
        await client.close()

### Воркер ###
@pytest_asyncio.fixture(scope="function")
async def reminder_worker(
    temporal_client,
    test_session_maker,
    mock_telegram_service_integration
):
    """
    Запускает воркер Temporal с патчем сессии БД.
    """
    patch_target = 'backend.control_plane.db.engine.get_async_session'
    @asynccontextmanager
    async def patched_get_session():
        async with test_session_maker() as session:
            yield session

    print(f"\nAttempting to patch DB session getter: {patch_target}")
    worker = None
    worker_task = None
    try:
        with patch(patch_target, new=patched_get_session, create=True):
            print(f"Successfully patched {patch_target}")

            worker = Worker(
                temporal_client,
                task_queue="integration-test-reminders-queue",
                workflows=[CheckRemindersWorkflow, SendReminderNotificationWorkflow],
                activities=[check_active_reminders, send_telegram_notification, abort_sent],
            )
            worker_task = asyncio.create_task(worker.run())
            print("Temporal worker started.")
            yield worker

    except (ImportError, AttributeError, TypeError) as e:
        print(f"ERROR patching '{patch_target}': {e}")
        pytest.fail(f"Failed to patch DB session getter at '{patch_target}': {e}", pytrace=False)
    finally:
        if worker and worker_task:
            print("\nAttempting to shut down temporal worker...")
            await worker.shutdown()
            print("Worker shutdown signal sent, awaiting task completion...")
            try:
                await asyncio.wait_for(worker_task, timeout=10.0)
                print("Temporal worker task completed successfully.")
            except asyncio.CancelledError:
                print("Temporal worker task cancelled.")
            except asyncio.TimeoutError:
                print("ERROR: Timeout waiting for temporal worker task!")
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    print("Worker task forcefully cancelled.")
            except Exception as e:
                print(f"Error awaiting worker task: {e}")
            print("Worker shutdown sequence finished.")

# --- Mock Telegram Service Fixture ---
@pytest_asyncio.fixture(scope="function")
def mock_telegram_service_integration():
    """Мокирует TelegramService для интеграционных тестов."""
    # Создаем AsyncMock для имитации асинхронного метода
    mock_send = AsyncMock(return_value=True)
    # Патчим метод send_message в том месте, где он используется активностью
    with patch(
        'backend.data_plane.activities.reminders.TelegramService.send_message',
        new=mock_send
        ) as mock:
          yield mock # Возвращаем сам мок, чтобы можно было проверить вызовы
