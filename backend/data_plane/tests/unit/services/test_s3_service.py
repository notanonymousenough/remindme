import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock, ANY # ANY полезен для проверки некоторых аргументов
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError # Для симуляции ошибок boto3

# Импортируем тестируемый класс
from backend.data_plane.services.s3_service import YandexStorageService

# Применяем маркеры
pytestmark = [pytest.mark.unit] # Не используем asyncio здесь, так как boto3 синхронный

# ----- Тесты для YandexStorageService -----

def test_s3_service_initialization(mock_settings, mock_boto3_s3_client):
    """Тест проверяет правильную инициализацию клиента boto3."""

    # Инициализируем сервис (фикстуры уже применили патчи)
    service = YandexStorageService()

    # Проверяем, что конструктор Session был вызван
    mock_boto3_s3_client["session_constructor"].assert_called_once()

    # Проверяем, что метод client был вызван с правильными параметрами
    mock_boto3_s3_client["session_instance"].client.assert_called_once_with(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=mock_settings.YANDEX_CLOUD_S3_KEY_ID,
        aws_secret_access_key=mock_settings.YANDEX_CLOUD_S3_SECRET,
        config=ANY  # Проверяем, что объект Config был передан
    )
    # Дополнительно можно проверить тип и параметры Config, если это критично
    args, kwargs = mock_boto3_s3_client["session_instance"].client.call_args
    assert isinstance(kwargs['config'], Config)
    assert kwargs['config'].signature_version == 's3v4'

    # Проверяем, что имя бакета установлено
    assert service.bucket_name == mock_settings.YANDEX_CLOUD_S3_BUCKET_NAME
    # Проверяем, что s3 клиент установлен
    assert service.s3 is mock_boto3_s3_client["s3_client"]


def test_save_image_success(mock_settings, mock_boto3_s3_client, mock_datetime_uuid):
    """Тест успешного сохранения изображения."""
    service = YandexStorageService()
    image_bytes = b"test_image_data"
    prefix = "test_prefix"
    content_type = "image/png"
    extension = "png"

    # Ожидаемое имя объекта на основе замоканных datetime и uuid
    expected_object_name = f"{prefix}/{mock_datetime_uuid['timestamp']}_{mock_datetime_uuid['uuid_hex_short']}.{extension}"
    # Ожидаемый публичный URL
    expected_public_url = f"https://{service.bucket_name}.storage.yandexcloud.net/{expected_object_name}"

    # Вызываем метод
    public_url = service.save_image(image_bytes, prefix, content_type, extension)

    # Проверяем результат
    assert public_url == expected_public_url

    # Проверяем вызов put_object
    mock_boto3_s3_client["s3_client"].put_object.assert_called_once_with(
        Bucket=service.bucket_name,
        Key=expected_object_name,
        Body=image_bytes,
        ContentType=content_type,
        ACL='public-read'
    )


def test_save_image_exception(mock_settings, mock_boto3_s3_client, mock_datetime_uuid):
    """Тест обработки исключения при сохранении изображения."""
    service = YandexStorageService()
    image_bytes = b"error_data"
    error_message = "Failed to put object"

    # Настраиваем мок put_object на выброс исключения
    mock_boto3_s3_client["s3_client"].put_object.side_effect = ClientError(
        error_response={'Error': {'Code': 'SomeError', 'Message': error_message}},
        operation_name='PutObject'
    )

    # Проверяем, что исключение пробрасывается дальше
    with pytest.raises(ClientError) as excinfo:
        service.save_image(image_bytes)

    # Опционально: проверить сообщение об ошибке
    assert error_message in str(excinfo.value)
    # Проверяем, что вызов put_object все равно был
    mock_boto3_s3_client["s3_client"].put_object.assert_called_once()


def test_delete_file_success(mock_settings, mock_boto3_s3_client):
    """Тест успешного удаления файла."""
    service = YandexStorageService()
    object_key = "images/some_file_to_delete.jpg"

    # Вызываем метод
    result = service.delete_file(object_key)

    # Проверяем результат
    assert result is True

    # Проверяем вызов delete_object
    mock_boto3_s3_client["s3_client"].delete_object.assert_called_once_with(
        Bucket=service.bucket_name,
        Key=object_key
    )


def test_delete_file_exception(mock_settings, mock_boto3_s3_client):
    """Тест обработки исключения при удалении файла."""
    service = YandexStorageService()
    object_key = "images/error_delete.txt"
    error_message = "Failed to delete object"

    # Настраиваем мок delete_object на выброс исключения
    mock_boto3_s3_client["s3_client"].delete_object.side_effect = ClientError(
         error_response={'Error': {'Code': 'SomeError', 'Message': error_message}},
        operation_name='DeleteObject'
    )

    # Вызываем метод
    result = service.delete_file(object_key)

    # Проверяем результат (должен вернуть False)
    assert result is False

    # Проверяем, что вызов delete_object был
    mock_boto3_s3_client["s3_client"].delete_object.assert_called_once_with(
        Bucket=service.bucket_name,
        Key=object_key
    )


def test_generate_presigned_url_success(mock_settings, mock_boto3_s3_client):
    """Тест успешной генерации presigned URL."""
    service = YandexStorageService()
    object_key = "private/data.zip"
    expires_in = 1800
    http_method = 'get_object'
    expected_url = "https://presigned.url/test_object" # Задано в фикстуре

    # Вызываем метод
    url = service.generate_presigned_url(object_key, expires_in, http_method)

    # Проверяем результат
    assert url == expected_url

    # Проверяем вызов generate_presigned_url
    mock_boto3_s3_client["s3_client"].generate_presigned_url.assert_called_once_with(
        ClientMethod=http_method,
        Params={
            'Bucket': service.bucket_name,
            'Key': object_key
        },
        ExpiresIn=expires_in
    )


def test_generate_presigned_url_exception(mock_settings, mock_boto3_s3_client):
    """Тест обработки исключения при генерации presigned URL."""
    service = YandexStorageService()
    object_key = "private/error_url.dat"
    error_message = "Failed to generate URL"

    # Настраиваем мок generate_presigned_url на выброс исключения
    mock_boto3_s3_client["s3_client"].generate_presigned_url.side_effect = ClientError(
         error_response={'Error': {'Code': 'SomeError', 'Message': error_message}},
        operation_name='GeneratePresignedUrl'
    )

    # Вызываем метод
    url = service.generate_presigned_url(object_key)

    # Проверяем результат (должен вернуть None)
    assert url is None

    # Проверяем, что вызов generate_presigned_url был
    mock_boto3_s3_client["s3_client"].generate_presigned_url.assert_called_once()
