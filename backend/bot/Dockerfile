FROM python:3.13-slim

WORKDIR /app/backend/bot

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Точка входа - запуск бота
CMD ["python", "main.py"]
