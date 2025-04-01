FROM python:3.13-slim

WORKDIR /app/backend/data_plane

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Точка входа - запуск воркера Temporal
CMD ["python", "main.py"]
