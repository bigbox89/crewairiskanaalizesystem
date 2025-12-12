#!/usr/bin/env bash
# CHANGE: Скрипт сборки и пуша образа в Cloud.ru registry
# WHY: Автоматизируем публикацию `{CLOUD_RU_REGISTRY}/bank-statement-mcp:latest`
# QUOTE(TЗ): "Добавить deploy скрипты для push в `{CLOUD_RU_REGISTRY}/bank-statement-mcp:latest`"
# REF: План, раздел Публикация образа

set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-bank-statement-mcp}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${CLOUD_RU_REGISTRY:?CLOUD_RU_REGISTRY is required}"
USERNAME="${CLOUD_RU_USERNAME:?CLOUD_RU_USERNAME is required}"
PASSWORD="${CLOUD_RU_PASSWORD:?CLOUD_RU_PASSWORD is required}"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "🔐 Login to registry ${REGISTRY}"
echo "${PASSWORD}" | docker login "${REGISTRY}" --username "${USERNAME}" --password-stdin

echo "🛠  Building image ${FULL_IMAGE}"
docker build -t "${FULL_IMAGE}" .

echo "📤 Pushing image ${FULL_IMAGE}"
docker push "${FULL_IMAGE}"

echo "✅ Done"

