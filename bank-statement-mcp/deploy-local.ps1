# CHANGE: Сборка и пуш Docker-образа в Cloud.ru registry (PowerShell)
# WHY: Удобный запуск на Windows, совместимый с переменными окружения
# QUOTE(TЗ): "Добавить deploy скрипты для push в `{CLOUD_RU_REGISTRY}/bank-statement-mcp:latest`"
# REF: План, раздел Публикация образа

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$IMAGE_NAME = $env:IMAGE_NAME
if ([string]::IsNullOrWhiteSpace($IMAGE_NAME)) { $IMAGE_NAME = "bank-statement-mcp" }
$IMAGE_TAG = $env:IMAGE_TAG
if ([string]::IsNullOrWhiteSpace($IMAGE_TAG)) { $IMAGE_TAG = "latest" }

$REGISTRY = $env:CLOUD_RU_REGISTRY
$USERNAME = $env:CLOUD_RU_USERNAME
$PASSWORD = $env:CLOUD_RU_PASSWORD

if (-not $REGISTRY) { throw "CLOUD_RU_REGISTRY is required" }
if (-not $USERNAME) { throw "CLOUD_RU_USERNAME is required" }
if (-not $PASSWORD) { throw "CLOUD_RU_PASSWORD is required" }

$FULL_IMAGE = "$($REGISTRY)/$($IMAGE_NAME):$($IMAGE_TAG)"

Write-Host "🔐 Login to registry $REGISTRY"
$PASSWORD | docker login $REGISTRY --username $USERNAME --password-stdin

Write-Host "🛠  Building image $FULL_IMAGE"
docker build -t $FULL_IMAGE .

Write-Host "📤 Pushing image $FULL_IMAGE"
docker push $FULL_IMAGE

Write-Host "✅ Done"

