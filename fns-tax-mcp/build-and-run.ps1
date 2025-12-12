# Скрипт для сборки и запуска Docker образа fns-tax-mcp

Write-Host "🔨 Сборка Docker образа..." -ForegroundColor Cyan
docker build -t fns-tax-mcp:latest .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка сборки образа" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Образ успешно собран" -ForegroundColor Green

Write-Host "🚀 Запуск контейнера..." -ForegroundColor Cyan
docker run -d `
    --name fns-tax-mcp `
    -p 8080:8080 `
    -e FNS_MODE=test `
    -e FNS_API_TOKEN=e8d5147b30c2d87db8ec61b5651f400d5da812b7 `
    -e PORT=8080 `
    -e HOST=0.0.0.0 `
    fns-tax-mcp:latest

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка запуска контейнера" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Контейнер запущен" -ForegroundColor Green
Write-Host "📋 Проверка статуса..." -ForegroundColor Cyan

Start-Sleep -Seconds 2
docker ps --filter "name=fns-tax-mcp"

Write-Host ""
Write-Host "🌐 Сервер доступен по адресу: http://localhost:8080" -ForegroundColor Green
Write-Host "📊 Health check: http://localhost:8080/health" -ForegroundColor Green
Write-Host "📝 Логи: docker logs -f fns-tax-mcp" -ForegroundColor Yellow

