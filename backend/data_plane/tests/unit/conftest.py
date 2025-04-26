import asyncio
import uuid
import warnings
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import boto3
import pytest

# Глобальные настройки и подавление предупреждений
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")
warnings.filterwarnings("ignore", message="Support for class-based `config` is deprecated")

# Применяем маркер к юнит-тестам
pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всех асинхронных тестов"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Мокирует настройки приложения"""
    settings = MagicMock()
    settings.ACTIVE_REMINDERS_LIMIT = 10
    settings.HABIT_IMAGE_CHARACTER = "assistant"
    settings.TELEGRAM_API_URL = "https://api.telegram.org/bot"
    settings.TELEGRAM_BOT_TOKEN = "test_token"
    settings.DATABASE_URI = "postgresql+asyncpg://test:test@localhost:5432/test_db"
    settings.YANDEX_CLOUD_S3_KEY_ID = "test_key_id"
    settings.YANDEX_CLOUD_S3_SECRET = "test_secret_key"
    settings.YANDEX_CLOUD_S3_BUCKET_NAME = "test-bucket"

    patches = [
        patch('backend.data_plane.services.telegram_service.get_settings', return_value=settings, create=True),
        patch('backend.data_plane.services.s3_service.get_settings', return_value=settings, create=True),
        patch('backend.config.get_settings', return_value=settings)
    ]

    from contextlib import ExitStack
    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        yield settings


@pytest.fixture
def mock_db_session():
    """Мокирует сессию SQLAlchemy для всех тестов"""
    session = AsyncMock()
    session.__aenter__.return_value = session
    session.__aexit__.return_value = None

    # Настройка execute для возврата результатов запросов
    execute_result = AsyncMock()
    execute_result.scalars.return_value.all.return_value = []
    execute_result.scalars.return_value.first.return_value = None
    execute_result.scalars.return_value.one_or_none.return_value = None
    session.execute.return_value = execute_result

    with patch('backend.control_plane.db.engine.get_async_session',
               return_value=session):
        yield session


@pytest.fixture
def mock_reminder_repo(mock_db_session):
    """Мокирует репозиторий напоминаний"""

    async def mock_take_for_sending(*args, **kwargs):
        """Возвращает тестовые напоминания"""
        return []

    async def mock_mark_sent(*args, **kwargs):
        """Имитирует пометку напоминания как отправленного"""
        return MagicMock(id=uuid.uuid4(), notification_sent=kwargs.get('sent', True))

    # Создаем и настраиваем репозиторий
    with patch('backend.control_plane.db.repositories.reminder.ReminderRepository.take_for_sending',
               side_effect=mock_take_for_sending) as take_mock, \
            patch('backend.control_plane.db.repositories.reminder.ReminderRepository.mark_sent',
                  side_effect=mock_mark_sent) as mark_mock:
        yield {
            'take_for_sending': take_mock,
            'mark_sent': mark_mock
        }


@pytest.fixture
def mock_user_repo(mock_db_session):
    """Мокирует репозиторий пользователей"""

    async def mock_get_by_model_id(*args, **kwargs):
        """Возвращает тестового пользователя"""
        return MagicMock(
            id=uuid.uuid4(),
            telegram_id="123456789",
            created_at=datetime.now()
        )

    # Создаем и настраиваем репозиторий
    with patch('backend.control_plane.db.repositories.user.UserRepository.get_by_model_id',
               side_effect=mock_get_by_model_id) as get_mock, \
            patch('backend.control_plane.db.repositories.user.UserRepository.get_all_models',
                  return_value=[]) as all_mock:
        yield {
            'get_by_model_id': get_mock,
            'get_all_models': all_mock
        }


@pytest.fixture
def mock_telegram_service():
    """Мокирует Telegram сервис"""

    async def mock_send_message(*args, **kwargs):
        """Имитирует отправку сообщения в Telegram"""
        return True

    with patch('backend.data_plane.services.telegram_service.TelegramService.send_message',
               side_effect=mock_send_message) as send_mock:
        yield send_mock


@pytest.fixture
def mock_s3_service():
    """Мокирует S3 сервис"""

    def mock_save_image(*args, **kwargs):
        """Имитирует сохранение изображения в S3"""
        return f"https://storage.example.com/images/{uuid.uuid4()}.jpg"

    with patch('backend.data_plane.services.s3_service.YandexStorageService.save_image',
               side_effect=mock_save_image) as save_mock:
        yield save_mock


@pytest.fixture
def mock_temporal():
    """Мокирует APIs Temporal для тестирования воркфлоу"""

    async def mock_execute_activity(*args, **kwargs):
        """Имитирует выполнение активности"""
        # Первый аргумент - это функция активности
        activity_name = args[0].__name__ if args else "unknown"

        # Различные ответы в зависимости от активности
        if activity_name == "check_active_reminders":
            return []
        elif activity_name == "send_telegram_notification":
            return True
        return None

    async def mock_start_child_workflow(*args, **kwargs):
        """Имитирует запуск дочернего воркфлоу"""
        return None

    # Патчим все необходимые API Temporal
    with patch('temporalio.workflow.execute_activity',
               side_effect=mock_execute_activity) as execute_mock, \
            patch('temporalio.workflow.start_child_workflow',
                  side_effect=mock_start_child_workflow) as start_child_mock, \
            patch('temporalio.workflow.continue_as_new') as continue_mock, \
            patch('asyncio.sleep', return_value=None) as sleep_mock:

        yield {
            'execute_activity': execute_mock,
            'start_child_workflow': start_child_mock,
            'continue_as_new': continue_mock,
            'sleep': sleep_mock
        }

@pytest.fixture
def mock_boto3_s3_client():
    """Мокирует boto3 S3 клиент и его методы."""
    # Создаем мок для клиента S3
    mock_s3 = MagicMock(spec=boto3.client('s3'))
    # Настраиваем возвращаемое значение для generate_presigned_url
    mock_s3.generate_presigned_url.return_value = "https://presigned.url/test_object"

    # Мокируем фабрику клиента, чтобы она возвращала наш мок-клиент
    mock_session_instance = MagicMock()
    mock_session_instance.client.return_value = mock_s3

    # Патчим Session() чтобы возвращал мок сессии
    with patch('backend.data_plane.services.s3_service.boto3.session.Session', return_value=mock_session_instance) as mock_session_constructor:
        yield {
            "s3_client": mock_s3,
            "session_constructor": mock_session_constructor,
            "session_instance": mock_session_instance
        }

@pytest.fixture
def mock_datetime_uuid():
    """Мокирует datetime.now и uuid.uuid4 для предсказуемых имен файлов."""
    fixed_datetime = datetime(2023, 10, 27, 10, 30, 0)
    fixed_uuid = uuid.UUID('12345678123456781234567812345678') # hex: 12345678123456781234567812345678
    fixed_uuid_hex_short = fixed_uuid.hex[:8] # '12345678'
    fixed_timestamp = fixed_datetime.strftime("%Y%m%d-%H%M%S") # '20231027-103000'

    with patch('backend.data_plane.services.s3_service.datetime') as mock_dt, \
         patch('backend.data_plane.services.s3_service.uuid') as mock_uuid:
        mock_dt.now.return_value = fixed_datetime
        mock_uuid.uuid4.return_value = fixed_uuid
        yield {
            "datetime": mock_dt,
            "uuid": mock_uuid,
            "timestamp": fixed_timestamp,
            "uuid_hex_short": fixed_uuid_hex_short
        }
