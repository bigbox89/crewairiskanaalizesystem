# Arbitr MCP (kad.arbitr.ru via api-assist.com)

Чистый MCP-сервер в корне репо. Папку `fns-tax-mcp/` не трогаем — это пример.

## Возможности
- Поиск дел: `arbitr_search_cases`
- Детали по номеру: `arbitr_details_by_number`
- Детали по ID: `arbitr_details_by_id`
- Скачивание PDF: `arbitr_download_pdf`

## Установка и запуск
```bash
pip install -e ".[dev]"
export ARBITR_MODE=test            # или prod
# export ARBITR_API_KEY=your_key   # обязателен в prod
python server.py
```

Эндпоинты:
- MCP: `http://localhost:8080/mcp`
- Health: `http://localhost:8080/health`
- Metrics: `http://localhost:8080/metrics`

## Переменные окружения
- `ARBITR_MODE` — `test`/`prod` (default `test`)
- `ARBITR_API_KEY` — ключ api-assist.com (обязателен в prod)
- `ARBITR_BASE_URL` — базовый URL API (default `https://service.api-assist.com/parser/arbitr_api`)
- `ARBITR_TIMEOUT` — таймаут HTTP в секундах (default `15`)
- `HOST` / `PORT` — адрес и порт (default `0.0.0.0` / `8080`)
- `ENABLE_METRICS` — включить `/metrics` (default true)
- `OTEL_ENDPOINT`, `OTEL_SERVICE_NAME` — опционально

## Тесты
```bash
pytest test/test_arbitr_api.py -v
```

## Docker
```bash
docker buildx build --platform linux/amd64 -t mcp-arbitr .
docker run --rm -p 8080:8080 -e ARBITR_MODE=test mcp-arbitr
```

## Примечание
Сервер не использует файловую систему в рантайме (требование AI Agents cloud.ru). `fns-tax-mcp/` остается как есть.