FROM python:3.11-slim

WORKDIR /app

# CHANGE: Копируем минимальный набор перед установкой зависимостей (включая package dir)
# WHY: setup.py ищет пакет tools; нужно скопировать его до pip install .
# QUOTE(TЗ): "Контейнеризация с корректной установкой зависимостей"
# REF: user-message
COPY pyproject.toml README.md ./
COPY tools ./tools

# Установка зависимостей (не editable)
RUN pip install --no-cache-dir .

# Копируем остальной код
COPY . .

# Открытие порта
EXPOSE 8080

# CHANGE: Явно задаём переменные окружения по умолчанию
# WHY: Совместимость с Cloud.ru Container App
# QUOTE(TЗ): "Используйте переменные окружения с дефолтами"
# REF: user-message
ENV HOST=0.0.0.0 \
    PORT=8080 \
    MODE=test

# Запуск сервера
CMD ["python", "server.py"]

