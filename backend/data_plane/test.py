import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import UUID

from backend.data_plane.activities.reminders import check_active_reminders
from backend.control_plane.db.models.reminder import Reminder, ReminderStatus


@pytest.mark.asyncio
async def test_check_active_reminders():
    # Создаем мок-объекты для тестирования
    mock_reminder1 = MagicMock(spec=Reminder)
    mock_reminder1.id = UUID("11111111-1111-1111-1111-111111111111")
    mock_reminder1.user_id = UUID("22222222-2222-2222-2222-222222222222")
    mock_reminder1.text = "Test reminder 1"
    mock_reminder1.time = datetime.now(timezone.utc)

    mock_reminder2 = MagicMock(spec=Reminder)
    mock_reminder2.id = UUID("33333333-3333-3333-3333-333333333333")
    mock_reminder2.user_id = UUID("44444444-4444-4444-4444-444444444444")
    mock_reminder2.text = "Test reminder 2"
    mock_reminder2.time = datetime.now(timezone.utc)

    # Создаем мок для репозитория напоминаний
    mock_repository = AsyncMock()
    mock_repository.take_for_sending.return_value = [mock_reminder1, mock_reminder2]

    # Патчим функцию создания репозитория
    with patch('backend.data_plane.activities.reminders.ReminderRepository', return_value=mock_repository):
        # Вызываем тестируемую функцию
        result = await check_active_reminders()

        # Проверяем, что репозиторий был вызван
        mock_repository.take_for_sending.assert_called_once()

        # Проверяем результат
        assert len(result) == 2
        assert result[0]["id"] == str(mock_reminder1.id)
        assert result[0]["user_id"] == str(mock_reminder1.user_id)
        assert result[0]["text"] == mock_reminder1.text
        assert result[0]["time"] == mock_reminder1.time.isoformat()

        assert result[1]["id"] == str(mock_reminder2.id)
        assert result[1]["user_id"] == str(mock_reminder2.user_id)
        assert result[1]["text"] == mock_reminder2.text
        assert result[1]["time"] == mock_reminder2.time.isoformat()
