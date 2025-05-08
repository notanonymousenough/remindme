import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Применяем маркеры
pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestReminderActivities:
    """Тесты для активностей напоминаний"""

    async def test_check_active_reminders(self, mock_reminder_repo):
        """Тестирует получение активных напоминаний"""
        # Настраиваем тестовые данные
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

        # Устанавливаем возвращаемое значение мока
        async def return_test_reminders(*args, **kwargs):
            return test_reminders

        mock_reminder_repo['take_for_sending'].side_effect = return_test_reminders

        # Импортируем активность здесь, чтобы использовать моки
        from backend.data_plane.activities.reminders import check_active_reminders

        # Вызываем активность
        result = await check_active_reminders()

        # Проверяем результат
        assert len(result) == 2
        assert result[0]["id"] == str(test_reminders[0].id)
        assert result[0]["text"] == test_reminders[0].text
        assert result[1]["id"] == str(test_reminders[1].id)
        assert result[1]["text"] == test_reminders[1].text

        # Проверяем вызов репозитория
        assert mock_reminder_repo['take_for_sending'].called

    async def test_check_active_reminders_empty(self, mock_reminder_repo):
        """Тестирует отсутствие активных напоминаний"""

        # Устанавливаем пустой список напоминаний
        async def return_empty_list(*args, **kwargs):
            return []

        mock_reminder_repo['take_for_sending'].side_effect = return_empty_list

        # Импортируем активность здесь
        from backend.data_plane.activities.reminders import check_active_reminders

        # Вызываем активность
        result = await check_active_reminders()

        # Проверяем результат
        assert isinstance(result, list)
        assert len(result) == 0

        # Проверяем вызов репозитория
        assert mock_reminder_repo['take_for_sending'].called

    async def test_send_telegram_notification(self, mock_user_repo, mock_telegram_service, mock_settings):
        """Тестирует отправку уведомления через Telegram"""
        # Тестовые данные
        user_id = str(uuid.uuid4())
        reminder_id = str(uuid.uuid4())
        reminder_text = "Test reminder text"
        reminder_time = datetime.now().isoformat()

        # Создаем мок пользователя
        mock_user = MagicMock(telegram_id="123456789")

        async def return_mock_user(*args, **kwargs):
            return mock_user

        mock_user_repo['get_by_model_id'].side_effect = return_mock_user

        # Импортируем активность здесь
        from backend.data_plane.activities.reminders import send_telegram_notification

        # Вызываем активность
        await send_telegram_notification(user_id, reminder_id, reminder_text, reminder_time)

        # Проверяем вызов сервиса Telegram
        assert mock_telegram_service.called
        call_args = mock_telegram_service.call_args
        assert call_args[0][0] == "123456789"  # telegram_id пользователя
        assert reminder_text in call_args[0][1]  # текст напоминания в сообщении

        # Проверяем наличие кнопок в сообщении
        assert isinstance(call_args[1]["reply_markup"], dict)
        assert "inline_keyboard" in call_args[1]["reply_markup"]

        # Проверяем, что ID напоминания есть в callback_data кнопок
        buttons_data = call_args[1]["reply_markup"]
        assert reminder_id in str(buttons_data)

    async def test_send_telegram_notification_formats_time(self, mock_user_repo, mock_telegram_service):
        """Тестирует форматирование времени в сообщении"""
        # Тестовые данные с конкретным временем
        user_id = str(uuid.uuid4())
        reminder_id = str(uuid.uuid4())
        reminder_text = "Test reminder text"
        reminder_time = "2023-04-25T15:30:00+00:00"  # Конкретное время для проверки форматирования

        # Создаем мок пользователя
        mock_user = MagicMock(telegram_id="123456789")

        async def return_mock_user(*args, **kwargs):
            return mock_user

        mock_user_repo['get_by_model_id'].side_effect = return_mock_user

        # Импортируем активность здесь
        from backend.data_plane.activities.reminders import send_telegram_notification

        # Вызываем активность
        await send_telegram_notification(user_id, reminder_id, reminder_text, reminder_time)

        # Проверяем форматирование времени в сообщении
        assert mock_telegram_service.called
        message_text = mock_telegram_service.call_args[0][1]
        assert "15:30" in message_text  # Проверяем, что время корректно отображается

    async def test_abort_sent(self, mock_reminder_repo):
        """Тестирует отмену статуса отправки напоминания"""
        # Тестовые данные
        reminder_id = str(uuid.uuid4())

        # Создаем мок для mark_sent
        async def mock_mark_sent_impl(*args, **kwargs):
            return MagicMock(id=uuid.UUID(reminder_id), notification_sent=kwargs.get('sent', True))

        mock_reminder_repo['mark_sent'].side_effect = mock_mark_sent_impl

        # Импортируем активность здесь
        from backend.data_plane.activities.reminders import abort_sent

        # Вызываем активность
        await abort_sent(reminder_id)

        # Проверяем вызов метода репозитория
        assert mock_reminder_repo['mark_sent'].called
        call_args = mock_reminder_repo['mark_sent'].call_args
        assert call_args[0][0] == uuid.UUID(reminder_id)  # Проверяем UUID напоминания
        assert call_args[1]["sent"] == False  # Проверяем параметр sent=False
