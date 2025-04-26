import pytest
import docker


@pytest.fixture(scope="session")
async def test_database():
    """Запускает тестовую PostgreSQL в Docker"""
    # Настройка реальной тестовой БД


@pytest.fixture(scope="session")
async def temporal_environment():
    """Запускает тестовый Temporal сервер"""
    # Настройка тестового Temporal
