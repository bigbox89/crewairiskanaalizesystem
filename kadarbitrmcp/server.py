"""Arbitr MCP server entrypoint."""

import os

try:
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv())
except ImportError:
    pass

from opentelemetry import trace
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, RedirectResponse

from config import get_settings
from metrics import metrics_handler
from mcp_instance import mcp
from tools import (
    arbitr_search_cases,
    arbitr_details_by_number,
    arbitr_details_by_id,
    arbitr_download_pdf,
)

tracer = trace.get_tracer(__name__)

AGENT_CARD = {
    "name": "arbitr-mcp",
    "description": "MCP сервер для kad.arbitr.ru через api-assist.com",
    "schema_version": "1.0",
}


@mcp.custom_route("/health", methods=["GET"])
async def health_handler(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "arbitr-mcp"})


@mcp.custom_route("/", methods=["GET"])
async def root_handler(request: Request) -> JSONResponse:
    tools = await mcp.get_tools()
    settings = get_settings()
    return JSONResponse(
        {
            "service": "arbitr-mcp",
            "description": "MCP сервер для kad.arbitr.ru через api-assist.com",
            "mode": settings.mode,
            "tools": [tool.name for tool in tools.values()],
        }
    )


@mcp.custom_route("/metrics", methods=["GET"])
async def metrics_route(request: Request) -> Response:
    return await metrics_handler()


@mcp.custom_route("/.well-known/agent-card.json", methods=["GET"])
async def agent_card(request: Request) -> JSONResponse:
    tools = await mcp.get_tools()
    return JSONResponse(
        {
            **AGENT_CARD,
            "tools": [
                {"name": tool.name, "description": tool.description}
                for tool in tools.values()
            ],
        }
    )


@mcp.custom_route("/.well-known/agent.json", methods=["GET"])
async def agent_json_deprecated(request: Request) -> Response:
    # Temporary shim to avoid warnings; remove when clients are updated
    return RedirectResponse("/.well-known/agent-card.json", status_code=307)


def main():
    settings = get_settings()
    HOST = settings.host
    PORT = settings.port

    print("=" * 60)
    print("🌐 ЗАПУСК MCP СЕРВЕРА (arbitr)")
    print("=" * 60)
    print(f"🚀 MCP Server: http://{HOST}:{PORT}/mcp")
    print(f"📊 Health: http://{HOST}:{PORT}/health")
    print(f"📋 Info: http://{HOST}:{PORT}/")
    print("=" * 60)

    mcp.run(
        transport="streamable-http",
        host=HOST,
        port=PORT,
    )


if __name__ == "__main__":
    main()


