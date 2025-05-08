# tests/unit/services/test_telegram_service.py

import pytest
import json
import aiohttp
import ssl
import certifi
from unittest.mock import patch, AsyncMock, MagicMock

from backend.data_plane.services.telegram_service import TelegramService, ssl_context

# Применяем маркеры ко всем тестам в этом файле
pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


@pytest.fixture
def mock_aiohttp_session():
    """Мокирует aiohttp.ClientSession для изоляции от реальных HTTP запросов."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock(spec=aiohttp.ClientResponse)
    mock_response.status = 200
    mock_response.text.return_value = '{"ok": true, "result": {}}' # Пример успешного ответа

    # Настраиваем context manager (__aenter__/__aexit__) для сессии
    async def session_context_manager(*args, **kwargs):
        return mock_session

    # Настраиваем context manager для post запроса
    async def post_context_manager(*args, **kwargs):
        return mock_response

    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    mock_session.post.return_value.__aenter__ = post_context_manager
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

    # Патчим ClientSession в модуле, где он используется (telegram_service)
    with patch('backend.data_plane.services.telegram_service.aiohttp.ClientSession', return_value=mock_session) as patched_session:
        yield {
            "session": mock_session,
            "response": mock_response,
            "patched_session": patched_session # Возвращаем сам патч, если нужно проверить его вызов
        }


def test_telegram_service_initialization(mock_settings): # mock_settings теперь просто дает объект
    """Тест проверяет правильную инициализацию URL API."""
    service = TelegramService()
    # Проверяем результат
    expected_url = f"{mock_settings.TELEGRAM_API_URL}{mock_settings.TELEGRAM_BOT_TOKEN}"
    assert service.api_url == expected_url


async def test_send_message_success_no_markup(mock_settings, mock_aiohttp_session):
    """
    Тест успешной отправки сообщения без клавиатуры.
    Проверяет вызов aiohttp.post с правильными параметрами.
    """
    service = TelegramService()
    chat_id = "12345"
    text = "Hello, <b>World</b>!"
    expected_url = f"{service.api_url}/sendMessage"
    expected_data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
        # reply_markup не должен быть здесь
    }

    result = await service.send_message(chat_id, text)

    assert result is True
    # Проверяем, что ClientSession был создан
    mock_aiohttp_session["patched_session"].assert_called_once()
    # Проверяем вызов post
    mock_aiohttp_session["session"].post.assert_called_once_with(
        expected_url,
        data=expected_data,
        ssl=ssl_context # Убеждаемся, что SSL контекст передается
    )


async def test_send_message_success_with_markup(mock_settings, mock_aiohttp_session):
    """
    Тест успешной отправки сообщения с клавиатурой.
    Проверяет правильную сериализацию reply_markup в JSON.
    """
    service = TelegramService()
    chat_id = "67890"
    text = "Choose an option:"
    reply_markup = {"inline_keyboard": [[{"text": "Option 1", "callback_data": "opt1"}]]}
    expected_url = f"{service.api_url}/sendMessage"
    expected_data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(reply_markup) # Проверяем JSON-строку
    }

    result = await service.send_message(chat_id, text, reply_markup=reply_markup)

    assert result is True
    mock_aiohttp_session["session"].post.assert_called_once_with(
        expected_url,
        data=expected_data,
        ssl=ssl_context
    )


async def test_send_message_failure_api_error(mock_settings, mock_aiohttp_session):
    """
    Тест обработки ошибки при отправке сообщения (не 200 статус от API).
    Проверяет, что выбрасывается ValueError с информацией об ошибке.
    """
    service = TelegramService()
    chat_id = "54321"
    text = "This will fail"
    error_status = 400
    error_text = '{"ok": false, "description": "Bad Request: chat not found"}'

    # Настраиваем мок ответа на ошибку
    mock_aiohttp_session["response"].status = error_status
    mock_aiohttp_session["response"].text = AsyncMock(return_value=error_text)

    expected_url = f"{service.api_url}/sendMessage"
    expected_data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    # Используем pytest.raises для проверки исключения
    with pytest.raises(ValueError) as excinfo:
        await service.send_message(chat_id, text)

    # Проверяем сообщение об ошибке
    assert f"Ошибка отправки сообщения в Telegram: {error_status} - {error_text}" in str(excinfo.value)

    # Проверяем, что post все равно был вызван
    mock_aiohttp_session["session"].post.assert_called_once_with(
        expected_url,
        data=expected_data,
        ssl=ssl_context
    )

async def test_send_message_uses_correct_ssl_context(mock_settings, mock_aiohttp_session):
    """
    Тест для явной проверки передачи правильного SSL контекста.
    """
    service = TelegramService()
    chat_id = "111"
    text = "SSL Test"

    await service.send_message(chat_id, text)

    call_args, call_kwargs = mock_aiohttp_session["session"].post.call_args
    # Проверяем, что ssl= был передан и это правильный объект контекста
    assert 'ssl' in call_kwargs
    # Используем 'is' для проверки идентичности объекта
    assert call_kwargs['ssl'] is ssl_context

