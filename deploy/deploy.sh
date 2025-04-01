#!/bin/bash
# Скрипт для полного деплоя всех компонентов приложения

set -e

# Загружаем переменные окружения
cd /opt/remind-me
if [ -f .env ]; then
    source .env
else
    echo "Файл .env не найден. Используем .env.example"
    cp deploy/.env.example .env
    source .env
fi

# Устанавливаем тег, если не задан
TAG=${TAG:-latest}
echo "Используем тег: $TAG"

# Обновляем образы из реестра
echo "Обновление образов..."
docker pull ghcr.io/${GITHUB_REPO}/bot:$TAG
docker pull ghcr.io/${GITHUB_REPO}/control-plane:$TAG
docker pull ghcr.io/${GITHUB_REPO}/data-plane:$TAG
docker pull ghcr.io/${GITHUB_REPO}/frontend:$TAG

# Обновляем docker-compose.yml
echo "Обновление docker-compose.yml с тегом $TAG..."
sed -i "s/\${TAG}/$TAG/g" deploy/docker-compose.yml

# Запускаем docker-compose
echo "Запуск контейнеров..."
cd deploy
docker-compose down --remove-orphans
docker-compose up -d

# Ждем запуска БД и запускаем миграции
echo "Ожидание запуска базы данных..."
sleep 10

echo "Запуск миграций..."
docker-compose exec control-plane python -m db.migrate upgrade

# Проверка работоспособности сервисов
echo "Проверка работоспособности сервисов..."
curl -s --head http://localhost:8000/v1/health || echo "Control Plane не доступен!"
curl -s --head http://localhost:3000/ || echo "Frontend не доступен!"

echo "Деплой успешно завершен!"
