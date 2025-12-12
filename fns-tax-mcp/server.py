"""MCP сервер для генерации и отправки налоговых деклараций."""
# CHANGE: Переписан для использования FastMCP 2.0 с streamable-http транспортом
# WHY: Устаревший метод http_app() не работал с session ID, FastMCP 2.0 решает эту проблему
# REF: Требование обновления до FastMCP 2.0 для работы в AI agents
# SOURCE: FastMCP 2.0 документация - использование mcp.run(transport="streamable-http")

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastmcp import FastMCP

try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except ImportError:
    pass

from opentelemetry import trace
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastmcp.server.server import default_lifespan

from mcp_instance import mcp

from tools import (
    generate_usn_declaration,
    generate_osno_declaration,
    generate_nds_declaration,
    generate_6ndfl_declaration,
    search_companies,
    autocomplete,
    get_company_data,
    multinfo_companies,
    multcheck_companies,
    check_counterparty,
    check_account_blocks,
    check_account_blocks_file,
    track_changes,
    monitor_companies,
    get_extract,
    get_msp_extract,
    get_accounting_report,
    get_accounting_report_file,
    get_inn_by_passport,
    check_passport,
    check_passport_info,
    check_person_status,
    get_fsrar_licenses,
    get_api_statistics,
)

tracer = trace.get_tracer(__name__)
logger = logging.getLogger("uvicorn.error")

# CHANGE: Добавлен lifespan-хук для логирования внешнего IP на старте
# WHY: ФНС требует whitelisting исходящего IP перед запросами; лог нужен до первой обработки
# QUOTE(TЗ): "нужно в mcp добавить логирование его внешнего ip при запуске"
# REF: user message 2025-12-10
async def get_external_ip() -> str | None:
    """
    Надежно определяет внешний исходящий IPv4.
    Приоритет: cloud.ru metadata -> публичные сервисы.
    """
    metadata_urls = [
        "http://169.254.169.254/latest/meta-data/public-ipv4",
        "http://169.254.169.254/latest/meta-data/instance-network-interface/0/ip-address",
    ]
    public_urls = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://myexternalip.com/raw",
    ]

    async with httpx.AsyncClient(timeout=2.5) as client:
        for url in metadata_urls:
            try:
                response = await client.get(url, timeout=1.0)
                candidate = response.text.strip()
                if response.status_code == 200 and "." in candidate:
                    if candidate.startswith(("10.", "172.", "192.168.", "127.")):
                        continue
                    return candidate
            except Exception:
                continue

    async with httpx.AsyncClient(timeout=4.0) as client:
        for url in public_urls:
            try:
                response = await client.get(url, timeout=1.5)
                candidate = response.text.strip()
                if response.status_code == 200:
                    if len(candidate.split(".")) == 4 and not candidate.startswith("127."):
                        return candidate
            except Exception:
                continue

    return None


@asynccontextmanager
async def external_ip_lifespan(server: FastMCP):
    """
    Lifespan-хук: логирует внешний IP и затем выполняет базовый lifecycle FastMCP.
    """
    async with default_lifespan(server) as lifespan_state:
        try:
            ip = await asyncio.wait_for(get_external_ip(), timeout=6.0)
        except asyncio.TimeoutError:
            ip = None
        if ip:
            logger.warning(
                "MCP SERVER EXTERNAL IP DETECTED: %s | WHITELIST THIS IP IN FNS API",
                ip,
            )
            logger.info(
                "startup_external_ip",
                extra={"external_ip": ip, "action": "whitelist_in_fns"},
            )
        else:
            logger.error("FAILED TO DETECT EXTERNAL IP — FNS API WILL BLOCK REQUESTS")

        yield lifespan_state


# CHANGE: Подключаем кастомный lifespan к единственному экземпляру FastMCP
# WHY: Логирование IP должно выполниться один раз при старте HTTP-сервера
# QUOTE(TЗ): "нужно в mcp добавить логирование его внешнего ip при запуске"
# REF: user message 2025-12-10
mcp._lifespan = external_ip_lifespan

def init_tracing():
    pass

# CHANGE: Добавление кастомных endpoints через @mcp.custom_route()
# WHY: Требование из .cursorrules - обязательные endpoints /health и /
# REF: FastMCP 2.0 документация - использование custom_route для добавления маршрутов

@mcp.custom_route("/health", methods=["GET"])
async def health_handler(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "service": "fns-tax-mcp"})

@mcp.custom_route("/", methods=["GET"])
async def root_handler(request: Request) -> JSONResponse:
    """Root endpoint с информацией о сервисе и списком tools."""
    tools = await mcp.get_tools()
    return JSONResponse({
        "service": "fns-tax-mcp",
        "description": "MCP-сервер для генерации деклараций и работы с API-ФНС (24 tools)",
        "tools": [tool.name for tool in tools.values()]
    })

def main():
    PORT = int(os.getenv("PORT", "8080"))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    print("=" * 60)
    print("🌐 ЗАПУСК MCP СЕРВЕРА")
    print("=" * 60)
    print(f"🚀 MCP Server: http://{HOST}:{PORT}/mcp")
    print(f"📊 Health: http://{HOST}:{PORT}/health")
    print(f"📋 Info: http://{HOST}:{PORT}/")
    print("=" * 60)
    
    # CHANGE: Использование mcp.run() с streamable-http транспортом
    # WHY: FastMCP 2.0 автоматически обрабатывает session ID и MCP protocol
    # REF: Документация FastMCP 2.0 и инструкция для AI agents
    mcp.run(
        transport="streamable-http",
        host=HOST,
        port=PORT
    )

if __name__ == "__main__":
    init_tracing()
    main()
