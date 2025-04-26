import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio.exceptions import ActivityError

# Применяем маркеры
pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestReminderWorkflows:
    """Тесты для рабочих процессов напоминаний"""

    async def test_check_reminders_workflow_empty(self, mock_temporal):
        """Тестирует рабочий процесс CheckRemindersWorkflow без напоминаний"""

        # Настраиваем возвращаемое значение для execute_activity
        async def mock_execute_empty(*args, **kwargs):
            # Проверяем, какая активность вызывается
            activity_name = args[0].__name__ if args else "unknown"
            if activity_name == "check_active_reminders":
                return []  # Пустой список напоминаний
            return None

        mock_temporal['execute_activity'].side_effect = mock_execute_empty

        # Патчим asyncio.sleep, чтобы не ждать
        async def mock_sleep(*args, **kwargs):
            return None

        # Импортируем рабочий процесс
        from backend.data_plane.workflows.reminders import CheckRemindersWorkflow

        # Запускаем рабочий процесс
        workflow = CheckRemindersWorkflow()
        with patch('asyncio.sleep', side_effect=mock_sleep):
            await workflow.run(0)

        # Проверяем вызовы
        assert mock_temporal['execute_activity'].called
        assert mock_temporal['execute_activity'].call_count == 1  # Только check_active_reminders
        assert not mock_temporal['start_child_workflow'].called  # Не должен вызывать дочерние процессы
        assert mock_temporal['continue_as_new'].called  # Должен продолжить как новый

    async def test_check_reminders_workflow_with_reminders(self, mock_temporal):
        """Тестирует рабочий процесс CheckRemindersWorkflow с напоминаниями"""
        # Тестовые данные
        test_reminders = [
            {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "text": "Test reminder workflow",
                "time": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "text": "Another test reminder",
                "time": (datetime.now() + timedelta(minutes=30)).isoformat()
            }
        ]

        # Настраиваем возвращаемое значение для execute_activity
        async def mock_execute_with_data(*args, **kwargs):
            activity_name = args[0].__name__ if args else "unknown"
            if activity_name == "check_active_reminders":
                return test_reminders
            return None

        mock_temporal['execute_activity'].side_effect = mock_execute_with_data

        # Патчим asyncio.sleep
        async def mock_sleep(*args, **kwargs):
            return None

        # Импортируем рабочий процесс
        from backend.data_plane.workflows.reminders import CheckRemindersWorkflow

        # Запускаем рабочий процесс
        workflow = CheckRemindersWorkflow()
        with patch('asyncio.sleep', side_effect=mock_sleep):
            await workflow.run(0)

        # Проверяем вызовы
        assert mock_temporal['execute_activity'].called
        assert mock_temporal['start_child_workflow'].called
        assert mock_temporal['start_child_workflow'].call_count == len(test_reminders)
        assert mock_temporal['continue_as_new'].called

        # Проверяем аргументы вызова start_child_workflow
        call_args = mock_temporal['start_child_workflow'].call_args_list
        for i, call in enumerate(call_args):
            # Первый аргумент должен быть функцией run класса SendReminderNotificationWorkflow
            assert call[0][0].__name__ == "run"
            # Второй аргумент должен быть напоминанием
            assert call[0][1] == test_reminders[i]

    async def test_send_reminder_notification_workflow(self, mock_temporal):
        """Тестирует рабочий процесс SendReminderNotificationWorkflow"""
        # Тестовые данные
        test_reminder = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "text": "Test notification workflow",
            "time": datetime.now().isoformat()
        }

        # Настраиваем возвращаемые значения для execute_activity
        async def mock_execute_success(*args, **kwargs):
            return True

        mock_temporal['execute_activity'].side_effect = mock_execute_success

        # Импортируем рабочий процесс
        from backend.data_plane.workflows.reminders import SendReminderNotificationWorkflow

        # Запускаем рабочий процесс
        workflow = SendReminderNotificationWorkflow()
        await workflow.run(test_reminder)

        # Проверяем вызовы
        assert mock_temporal['execute_activity'].called
        assert mock_temporal['execute_activity'].call_count == 1

        # Проверяем аргументы вызова execute_activity
        call_args = mock_temporal['execute_activity'].call_args
        # Первый аргумент должен быть функцией send_telegram_notification
        assert call_args[0][0].__name__ == "send_telegram_notification"
        # Затем идут аргументы функции
        assert call_args[1]["args"][0] == test_reminder["user_id"]
        assert call_args[1]["args"][1] == test_reminder["id"]
        assert call_args[1]["args"][2] == test_reminder["text"]
        assert call_args[1]["args"][3] == test_reminder["time"]

    async def test_send_reminder_notification_workflow_with_error(self, mock_temporal):
        """Тестирует обработку ошибок в SendReminderNotificationWorkflow"""
        # Тестовые данные
        test_reminder = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "text": "Test error handling workflow",
            "time": datetime.now().isoformat()
        }

        # Счетчик вызовов
        call_count = 0
        called_activities = []

        # Настраиваем возвращаемые значения для execute_activity с ошибкой на первом вызове
        async def mock_execute_with_error(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            activity_name = args[0].__name__ if args else "unknown"
            called_activities.append(activity_name)

            if call_count == 1:
                # Первый вызов (send_telegram_notification) выбрасывает исключение
                raise Exception("Test error")

            # Все последующие вызовы успешны
            return None

        mock_temporal['execute_activity'].side_effect = mock_execute_with_error

        # Импортируем рабочий процесс
        from backend.data_plane.workflows.reminders import SendReminderNotificationWorkflow

        # Запускаем рабочий процесс, ожидая исключение
        workflow = SendReminderNotificationWorkflow()
        with pytest.raises(Exception):
            await workflow.run(test_reminder)

        # Проверяем, что активности были вызваны
        assert call_count >= 1
        # Проверяем, что первым вызовом был send_telegram_notification
        assert called_activities[0] == "send_telegram_notification"

    async def test_workflow_retry_policy(self, mock_temporal):
        """Тестирует настройки политики повторных попыток"""
        # Импортируем рабочие процессы
        from backend.data_plane.workflows.reminders import (
            CheckRemindersWorkflow,
            SendReminderNotificationWorkflow
        )

        # Настраиваем мок для execute_activity, чтобы проверить параметры retry_policy
        async def capture_retry_policy(*args, **kwargs):
            # Запоминаем политику повторных попыток
            self.captured_retry_policy = kwargs.get('retry_policy')
            return []

        mock_temporal['execute_activity'].side_effect = capture_retry_policy

        # Патчим asyncio.sleep, чтобы не ждать
        async def mock_sleep(*args, **kwargs):
            return None

        # Запускаем рабочий процесс для проверки политики повторов
        workflow = CheckRemindersWorkflow()
        with patch('asyncio.sleep', side_effect=mock_sleep):
            await workflow.run(0)

        # Проверяем настройки политики повторов
        assert hasattr(self, 'captured_retry_policy')
        assert self.captured_retry_policy is not None
        assert hasattr(self.captured_retry_policy, 'maximum_attempts')
        assert self.captured_retry_policy.maximum_attempts > 0  # Должно быть больше 0
