"""
Сервис для работы с Yandex Object Storage
"""
import boto3
from botocore.client import Config
import uuid
from datetime import datetime
import logging
from typing import Optional

from backend.config import get_settings

logger = logging.getLogger("storage_service")


class YandexStorageService:
    """Сервис для загрузки и хранения файлов в Yandex Object Storage"""

    def __init__(self):
        """Инициализация сервиса"""
        self.session = boto3.session.Session()
        self.s3 = self.session.client(
            service_name='s3',
            endpoint_url='https://storage.yandexcloud.net',
            aws_access_key_id=get_settings().YANDEX_CLOUD_S3_KEY_ID,
            aws_secret_access_key=get_settings().YANDEX_CLOUD_S3_SECRET,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = get_settings().YANDEX_CLOUD_S3_BUCKET_NAME

    def save_image(
            self,
            image_bytes: bytes,
            prefix: str = "images",
            content_type: str = "image/jpeg",
            extension: str = "jpeg"
    ) -> str:
        """
        Сохраняет изображение в Яндекс Object Storage с публичным доступом.

        Args:
            image_bytes: Байты изображения
            prefix: Префикс для пути к файлу (папка)
            content_type: MIME-тип содержимого
            extension: Расширение файла

        Returns:
            public_url: Постоянная публичная ссылка на изображение
        """
        try:
            # Генерируем уникальное имя файла
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            object_name = f"{prefix}/{timestamp}_{unique_id}.{extension}"

            # Загружаем объект с публичным доступом
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=image_bytes,
                ContentType=content_type,
                ACL='public-read'  # Устанавливаем публичный доступ
            )

            # Формируем постоянную публичную ссылку
            public_url = f"https://{self.bucket_name}.storage.yandexcloud.net/{object_name}"
            logger.info(f"Файл успешно загружен в хранилище: {object_name}")

            return public_url
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла в хранилище: {str(e)}")
            raise

    def delete_file(self, object_key: str) -> bool:
        """
        Удаляет файл из хранилища

        Args:
            object_key: Ключ объекта в хранилище

        Returns:
            bool: Успешность удаления
        """
        try:
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"Файл успешно удален из хранилища: {object_key}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении файла из хранилища: {str(e)}")
            return False

    def generate_presigned_url(
            self,
            object_key: str,
            expires_in: int = 3600,
            http_method: str = 'get_object'
    ) -> Optional[str]:
        """
        Создает временный URL-доступ к файлу

        Args:
            object_key: Ключ объекта в хранилище
            expires_in: Время жизни ссылки в секундах
            http_method: HTTP метод ('get_object', 'put_object', etc.)

        Returns:
            url: Временная ссылка на объект или None при ошибке
        """
        try:
            url = self.s3.generate_presigned_url(
                ClientMethod=http_method,
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Ошибка при создании временной ссылки: {str(e)}")
            return None
