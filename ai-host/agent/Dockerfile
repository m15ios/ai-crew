FROM python:3.9-alpine

WORKDIR /app

# Устанавливаем зависимости
RUN apk add --no-cache bash

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все Python файлы
COPY *.py ./

# Создаем папку для конфигов
RUN mkdir -p /app/config

CMD ["python", "-u", "agent.py"]