#!/bin/bash

set -e

REGISTRY=${CLOUD_RU_REGISTRY:-${1:-""}}
IMAGE_NAME=${IMAGE_NAME:-"fns-tax-mcp"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
USERNAME=${CLOUD_RU_USERNAME:-${2:-""}}
PASSWORD=${CLOUD_RU_PASSWORD:-${3:-""}}

if [ -z "$REGISTRY" ]; then
    echo "❌ REGISTRY не указан. Установите переменную окружения CLOUD_RU_REGISTRY"
    exit 1
fi

if [ -z "$USERNAME" ]; then
    echo "❌ USERNAME не указан. Установите переменную окружения CLOUD_RU_USERNAME"
    exit 1
fi

if [ -z "$PASSWORD" ]; then
    echo "❌ PASSWORD не указан. Установите переменную окружения CLOUD_RU_PASSWORD"
    exit 1
fi

FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "🚀 Начинаем локальную сборку и публикацию образа..."
echo "Registry: $REGISTRY"
echo "Image: $FULL_IMAGE_NAME"

if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker"
    exit 1
fi

echo "✅ Docker найден"

echo "🔐 Вход в Cloud.ru registry..."
echo "$PASSWORD" | docker login "$REGISTRY" -u "$USERNAME" --password-stdin

echo "✅ Успешный вход в registry"

echo "🔨 Сборка Docker образа..."
docker build -t "$FULL_IMAGE_NAME" -f Dockerfile .

echo "✅ Образ успешно собран"

echo "📤 Публикация образа в Cloud.ru registry..."
docker push "$FULL_IMAGE_NAME"

echo "✅ Образ успешно опубликован: $FULL_IMAGE_NAME"
echo ""
echo "🎉 Деплой завершен успешно!"
echo "Следующий шаг: запустите workflow для деплоя в Container App"

