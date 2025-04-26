import asyncio
import uuid
import warnings
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

# Подавляем предупреждения
warnings.filterwarnings("ignore", category=DeprecationWarning)  # Игнорируем устаревшие функции
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")  # Игнорируем protobuf предупреждения
warnings.filterwarnings("ignore", message="Support for class-based `config` is deprecated")  # Pydantic предупреждения

# Применяем маркер asyncio ко всем тестам в модуле
pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def mock_settings():
    """Мокирует настройки для всех тестов"""
    settings = MagicMock()
    settings.ACTIVE_REMINDERS_LIMIT = 10
    with patch('backend.data_plane.activities.reminders.get_settings', return_value=settings):
        yield


class TestReminderActivities:
    """Тесты для активностей напоминаний"""

    async def test_check_active_reminders(self):
        """Тест активности check_active_reminders"""
        # Тестовые данные
        test_reminders = [
            MagicMock(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                text="Test reminder 1",
                time=datetime.now(),
                notification_sent=False
            ),
            MagicMock(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                text="Test reminder 2",
                time=datetime.now() + timedelta(minutes=5),
                notification_sent=False
            )
        ]

        # Создаем асинхронные моки правильно
        async def mock_take_for_sending(*args, **kwargs):
            return test_reminders

        # Патчим сам метод репозитория, а не конструктор
        with patch('backend.control_plane.db.repositories.reminder.ReminderRepository.take_for_sending',
                   side_effect=mock_take_for_sending):
            # Импортируем активность
            from backend.data_plane.activities.reminders import check_active_reminders

            # Вызываем активность
            result = await check_active_reminders()

            # Проверяем результат
            assert len(result) == 2
            assert result[0]["id"] == str(test_reminders[0].id)
            assert result[0]["text"] == test_reminders[0].text
            assert result[1]["id"] == str(test_reminders[1].id)
            assert result[1]["text"] == test_reminders[1].text

    async def test_send_telegram_notification(self):
        """Тест активности send_telegram_notification"""
        # Тестовые данные
        user_id = str(uuid.uuid4())
        reminder_id = str(uuid.uuid4())
        reminder_text = "Test reminder text"
        reminder_time = datetime.now().isoformat()

        # Создаем мок пользователя
        mock_user = MagicMock(telegram_id="123456789")

        # Создаем асинхронные моки правильно
        async def mock_get_by_model_id(*args, **kwargs):
            return mock_user

        async def mock_send_message(*args, **kwargs):
            return True

        # Патчим методы, а не классы
        with patch('backend.control_plane.db.repositories.user.UserRepository.get_by_model_id',
                   side_effect=mock_get_by_model_id), \
                patch('backend.data_plane.services.telegram_service.TelegramService.send_message',
                      side_effect=mock_send_message) as mock_send:
            # Импортируем активность
            from backend.data_plane.activities.reminders import send_telegram_notification

            # Вызываем активность
            await send_telegram_notification(user_id, reminder_id, reminder_text, reminder_time)

            # Проверяем вызов Telegram
            assert mock_send.called
            call_args = mock_send.call_args
            assert call_args[0][0] == "123456789"  # telegram_id
            assert reminder_text in call_args[0][1]  # message

    async def test_abort_sent(self):
        """Тест активности abort_sent"""
        # Тестовые данные
        reminder_id = str(uuid.uuid4())

        # Создаем асинхронный мок
        async def mock_mark_sent(*args, **kwargs):
            return MagicMock()

        # Патчим метод
        with patch('backend.control_plane.db.repositories.reminder.ReminderRepository.mark_sent',
                   side_effect=mock_mark_sent) as mock_mark:
            # Импортируем активность
            from backend.data_plane.activities.reminders import abort_sent

            # Вызываем активность
            await abort_sent(reminder_id)

            # Проверяем вызов метода с правильными параметрами
            assert mock_mark.called
            call_args = mock_mark.call_args
            assert call_args[0][0] == uuid.UUID(reminder_id)
            assert call_args[1]["sent"] == False


class TestReminderWorkflows:
    """Тесты для рабочих процессов напоминаний"""

    async def test_check_reminders_workflow(self):
        """Тест рабочего процесса CheckRemindersWorkflow"""
        # Тестовые данные
        test_reminders = [
            {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "text": "Test reminder workflow",
                "time": datetime.now().isoformat()
            }
        ]

        # Создаем асинхронные моки для активностей
        async def mock_execute(*args, **kwargs):
            return test_reminders

        async def mock_start_child(*args, **kwargs):
            return None

        # Мок для asyncio.sleep
        async def mock_sleep(*args, **kwargs):
            return None

        # Для continue_as_new не нужен асинхронный мок, так как эта функция не возвращает значение
        mock_continue = MagicMock()

        # Патчим функции Temporal и asyncio.sleep
        with patch('temporalio.workflow.execute_activity', side_effect=mock_execute) as mock_exec, \
                patch('temporalio.workflow.start_child_workflow', side_effect=mock_start_child) as mock_start, \
                patch('temporalio.workflow.continue_as_new', mock_continue), \
                patch('asyncio.sleep', side_effect=mock_sleep):  # Важное добавление!

            # Импортируем рабочий процесс
            from backend.data_plane.workflows.reminders import CheckRemindersWorkflow

            # Запускаем рабочий процесс с таймаутом
            workflow = CheckRemindersWorkflow()
            await asyncio.wait_for(workflow.run(0), timeout=5)  # 5 секунд таймаут

            # Проверяем вызовы
            assert mock_exec.called
            assert mock_start.called
            assert mock_continue.called

    async def test_send_reminder_notification_workflow(self):
        """Тест рабочего процесса SendReminderNotificationWorkflow"""
        # Тестовые данные
        test_reminder = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "text": "Test notification workflow",
            "time": datetime.now().isoformat()
        }

        # Создаем асинхронный мок
        async def mock_execute(*args, **kwargs):
            return None

        # Патчим функцию Temporal
        with patch('temporalio.workflow.execute_activity', side_effect=mock_execute) as mock_exec:
            # Импортируем рабочий процесс
            from backend.data_plane.workflows.reminders import SendReminderNotificationWorkflow

            # Запускаем рабочий процесс
            workflow = SendReminderNotificationWorkflow()
            await workflow.run(test_reminder)

            # Проверяем вызов
            assert mock_exec.called
            # Проверяем, что первый аргумент первого вызова - это функция send_telegram_notification
            assert mock_exec.call_args_list[0][0][0].__name__ == "send_telegram_notification"

    async def test_send_reminder_notification_workflow_with_error(self):
        """Тест обработки ошибки в SendReminderNotificationWorkflow"""
        # Тестовые данные
        test_reminder = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "text": "Test error handling workflow",
            "time": datetime.now().isoformat()
        }

        # Мокируем execute_activity, проверяя только первый вызов
        with patch('temporalio.workflow.execute_activity') as mock_execute:
            # Настраиваем мок так, чтобы он выбрасывал исключение
            mock_execute.side_effect = Exception("Test error")

            # Импортируем рабочий процесс
            from backend.data_plane.workflows.reminders import SendReminderNotificationWorkflow

            # Запускаем workflow и ожидаем исключение с таймаутом
            workflow = SendReminderNotificationWorkflow()
            with pytest.raises(Exception):
                await asyncio.wait_for(workflow.run(test_reminder), timeout=5)

            # Проверяем, что execute_activity был вызван хотя бы раз
            assert mock_execute.called

            # Проверяем, что первым вызовом был send_telegram_notification
            assert mock_execute.call_args_list[0][0][0].__name__ == "send_telegram_notification"
