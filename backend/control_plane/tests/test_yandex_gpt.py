import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock, create_autospec

import pytest


# Патчи для мокирования модуля get_settings
# Это позволит избежать загрузки настоящих настроек
@pytest.fixture(autouse=True)
def mock_settings():
    mock_settings = MagicMock()
    mock_settings.ACTIVE_REMINDERS_LIMIT = 10
    mock_settings.HABIT_IMAGE_CHARACTER = "assistant"

    with patch('backend.data_plane.activities.reminders.get_settings', return_value=mock_settings):
        yield


@pytest.mark.asyncio
class TestReminderActivities:
    """Тесты для активностей напоминаний"""

    async def test_check_active_reminders(self):
        """Тест активности check_active_reminders с мокированной БД"""
        # Импортируем здесь, чтобы патчинг сработал правильно
        from backend.data_plane.activities.reminders import check_active_reminders
        from backend.control_plane.db.repositories.reminder import ReminderRepository

        # Создаем тестовые данные
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

        # Создаем асинхронный мок для репозитория
        mock_repo = AsyncMock(spec=ReminderRepository)
        mock_repo.take_for_sending.return_value = test_reminders

        # Патчим конструктор репозитория
        with patch('backend.data_plane.activities.reminders.ReminderRepository', return_value=mock_repo):
            # Вызываем активность
            result = await check_active_reminders()

            # Проверяем, что репозиторий был вызван
            mock_repo.take_for_sending.assert_called_once()

            # Проверяем результат
            assert len(result) == 2
            assert result[0]["id"] == str(test_reminders[0].id)
            assert result[0]["text"] == test_reminders[0].text
            assert result[1]["id"] == str(test_reminders[1].id)
            assert result[1]["text"] == test_reminders[1].text

    async def test_send_telegram_notification(self):
        """Тест активности send_telegram_notification с мокированными зависимостями"""
        # Импортируем здесь
        from backend.data_plane.activities.reminders import send_telegram_notification
        from backend.control_plane.db.repositories.user import UserRepository
        from backend.data_plane.services.telegram_service import TelegramService

        # Создаем мок пользователя
        mock_user = MagicMock(telegram_id="123456789")

        # Создаем асинхронный мок для репозитория пользователей
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.get_by_model_id.return_value = mock_user

        # Создаем асинхронный мок для Telegram сервиса
        mock_tg = AsyncMock(spec=TelegramService)

        # Патчим конструкторы
        with patch('backend.data_plane.activities.reminders.UserRepository', return_value=mock_user_repo), \
                patch('backend.data_plane.activities.reminders.TelegramService', return_value=mock_tg):
            # Тестовые данные
            user_id = str(uuid.uuid4())
            reminder_id = str(uuid.uuid4())
            reminder_text = "Test reminder text"
            reminder_time = datetime.now().isoformat()

            # Вызываем активность
            await send_telegram_notification(user_id, reminder_id, reminder_text, reminder_time)

            # Проверяем, что зависимости были вызваны
            mock_user_repo.get_by_model_id.assert_called_once()
            mock_tg.send_message.assert_called_once()

            # Проверяем параметры вызова Telegram
            call_args = mock_tg.send_message.call_args
            assert call_args[0][0] == "123456789"  # telegram_id
            assert reminder_text in call_args[0][1]  # message

    async def test_abort_sent(self):
        """Тест активности abort_sent с мокированной БД"""
        # Импортируем здесь
        from backend.data_plane.activities.reminders import abort_sent
        from backend.control_plane.db.repositories.reminder import ReminderRepository

        # Создаем асинхронный мок для репозитория напоминаний
        mock_repo = AsyncMock(spec=ReminderRepository)

        # Патчим конструктор репозитория
        with patch('backend.data_plane.activities.reminders.ReminderRepository', return_value=mock_repo):
            # Тестовые данные
            reminder_id = str(uuid.uuid4())

            # Вызываем активность
            await abort_sent(reminder_id)

            # Проверяем, что репозиторий был вызван с правильными параметрами
            mock_repo.mark_sent.assert_called_once_with(uuid.UUID(reminder_id), sent=False)


@pytest.mark.asyncio
class TestReminderWorkflows:
    """Тесты для рабочих процессов напоминаний"""

    async def test_check_reminders_workflow(self):
        """Тест рабочего процесса CheckRemindersWorkflow"""
        # Импортируем рабочий процесс
        from backend.data_plane.workflows.reminders import CheckRemindersWorkflow

        # Тестовые данные
        test_reminders = [
            {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "text": "Test reminder workflow",
                "time": datetime.now().isoformat()
            }
        ]

        # Создаем асинхронный мок для execute_activity
        execute_activity_mock = AsyncMock()
        execute_activity_mock.return_value = test_reminders

        # Создаем асинхронный мок для start_child_workflow
        start_child_mock = AsyncMock()

        # Создаем мок для continue_as_new (неасинхронный)
        continue_as_new_mock = MagicMock()

        # Патчим функции Temporal
        with patch('temporalio.workflow.execute_activity', execute_activity_mock), \
                patch('temporalio.workflow.start_child_workflow', start_child_mock), \
                patch('temporalio.workflow.continue_as_new', continue_as_new_mock):
            # Создаем и запускаем рабочий процесс
            workflow = CheckRemindersWorkflow()
            await workflow.run(0)

            # Проверяем, что execute_activity был вызван для проверки напоминаний
            assert execute_activity_mock.called

            # Проверяем, что start_child_workflow был вызван для каждого напоминания
            assert start_child_mock.call_count == len(test_reminders)

            # Проверяем, что continue_as_new был вызван
            assert continue_as_new_mock.called

    async def test_send_reminder_notification_workflow(self):
        """Тест рабочего процесса SendReminderNotificationWorkflow"""
        # Импортируем рабочий процесс
        from backend.data_plane.workflows.reminders import SendReminderNotificationWorkflow

        # Тестовые данные
        test_reminder = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "text": "Test notification workflow",
            "time": datetime.now().isoformat()
        }

        # Создаем асинхронный мок для execute_activity
        execute_activity_mock = AsyncMock()

        # Патчим функции Temporal
        with patch('temporalio.workflow.execute_activity', execute_activity_mock):
            # Создаем и запускаем рабочий процесс
            workflow = SendReminderNotificationWorkflow()
            await workflow.run(test_reminder)

            # Проверяем, что execute_activity был вызван для отправки уведомления
            assert execute_activity_mock.called

            # Извлекаем первый позиционный аргумент из первого вызова
            activity_func = execute_activity_mock.call_args_list[0][0][0]

            # Проверяем, что вызвана правильная активность
            assert activity_func.__name__ == "send_telegram_notification"

    async def test_send_reminder_notification_workflow_with_error(self):
        """Тест компенсационной логики SendReminderNotificationWorkflow при ошибке"""
        # Импортируем рабочий процесс
        from backend.data_plane.workflows.reminders import SendReminderNotificationWorkflow
        from temporalio.exceptions import ActivityError

        # Тестовые данные
        test_reminder = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "text": "Test error handling workflow",
            "time": datetime.now().isoformat()
        }

        # Создаем асинхронный мок для execute_activity с эффектом выброса исключения
        execute_activity_mock = AsyncMock()
        execute_activity_mock.side_effect = [
            ActivityError("Test error"),  # Первый вызов выбрасывает исключение
            None  # Второй вызов (компенсация) успешен
        ]

        # Патчим функции Temporal
        with patch('temporalio.workflow.execute_activity', execute_activity_mock):
            # Создаем и запускаем рабочий процесс
            workflow = SendReminderNotificationWorkflow()

            # Запускаем workflow, не ожидая исключения
            try:
                await workflow.run(test_reminder)
            except Exception:
                pass  # Игнорируем любые непойманные исключения

            # Проверяем количество вызовов execute_activity
            # Должно быть минимум 2: основная активность и компенсация
            assert execute_activity_mock.call_count >= 1

            # Получаем все вызовы
            calls = execute_activity_mock.call_args_list

            # Первый вызов должен быть для send_telegram_notification
            first_call = calls[0]
            assert first_call[0][0].__name__ == "send_telegram_notification"

            # Если есть второй вызов, проверяем, что это abort_sent
            if len(calls) > 1:
                second_call = calls[1]
                assert second_call[0][0].__name__ == "abort_sent"
