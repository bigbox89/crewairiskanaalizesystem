"""
HTTP-сервер для bank-statement-mcp с streamable-http транспортом.
Соответствует стандарту Cloud.ru: единый FastMCP, OpenTelemetry, health-check.
Использует FastMCP 2.0 с mcp.run() и @mcp.custom_route().
"""
# CHANGE: Импорты стандартной библиотеки
# WHY: Необходимо для загрузки env и корректного запуска
# QUOTE(TЗ): "Используйте переменные окружения с дефолтами"
# REF: user-message
import os
from typing import Dict

from dotenv import load_dotenv, find_dotenv
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from mcp_instance import mcp

# CHANGE: Загрузка переменных окружения
# WHY: Требуется для HOST/PORT и OTEL конфигурации
# QUOTE(TЗ): "Загрузка env через dotenv"
# REF: user-message
load_dotenv(find_dotenv())

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
OTEL_ENDPOINT = os.getenv("OTEL_ENDPOINT")
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "bank-statement-mcp")

# CHANGE: Настройка OpenTelemetry
# WHY: Стандарт Cloud.ru требует трейсинг
# QUOTE(TЗ): "OpenTelemetry спаны внутри каждого tool"
# REF: user-message
resource = Resource.create({"service.name": OTEL_SERVICE_NAME})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
if OTEL_ENDPOINT:
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT)))
trace.set_tracer_provider(provider)
HTTPXClientInstrumentor().instrument()

# CHANGE: Импорт tools для регистрации
# WHY: FastMCP регистрирует декорированные функции при импорте
# QUOTE(TЗ): "Каждый tool — отдельный файл в tools/"
# REF: user-message
import tools  # noqa: E402,F401

# CHANGE: Добавление кастомных endpoints через @mcp.custom_route()
# WHY: FastMCP 2.0 поддерживает кастомные routes через декоратор
# QUOTE(TЗ): "Использовать mcp.run(transport=\"streamable-http\") и @mcp.custom_route()"
# REF: План обновления FastMCP до 2.0
@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> PlainTextResponse:
    """Health-check endpoint."""
    return PlainTextResponse("ok")


@mcp.custom_route("/", methods=["GET"])
async def info(request: Request) -> JSONResponse:
    """
    Возвращает информацию о сервисе.
    """
    # CHANGE: Упрощенный endpoint без доступа к tools
    # WHY: FastMCP 2.0 не предоставляет прямой доступ к mcp.tools, список tools доступен через /mcp endpoint
    # REF: План обновления FastMCP до 2.0, исправление AttributeError
    # CHANGE: Безопасный доступ к mcp.name
    # WHY: FastMCP 2.0 может иметь другую структуру атрибутов
    # REF: План обновления FastMCP до 2.0, исправление AttributeError
    try:
        server_name = mcp.name if hasattr(mcp, "name") else "bank-statement-mcp"
    except Exception:
        server_name = "bank-statement-mcp"
    
    payload: Dict[str, object] = {
        "name": server_name,
        "transport": "streamable-http",
        "mcp_endpoint": "/mcp",
        "description": "MCP server для получения банковских выписок",
        "tools_endpoint": "POST /mcp с method: tools/list",
    }
    return JSONResponse(payload)


# CHANGE: Использование mcp.run() вместо uvicorn.run() с FastAPI app
# WHY: FastMCP 2.0 поддерживает прямой запуск через mcp.run() с streamable-http транспортом
# QUOTE(TЗ): "mcp.run(transport=\"streamable-http\", host=HOST, port=PORT)"
# REF: План обновления FastMCP до 2.0
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=HOST, port=PORT)

