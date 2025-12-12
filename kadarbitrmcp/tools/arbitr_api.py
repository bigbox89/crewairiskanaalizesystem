"""MCP tools for kad.arbitr.ru via api-assist.com."""

import time
from typing import Optional

from fastmcp import Context
from mcp.types import TextContent
from mcp.shared.exceptions import McpError, ErrorData
from opentelemetry import trace
from pydantic import Field

from config import get_settings
from metrics import observe_duration, record_tool_call
from mcp_instance import mcp
from .arbitr_client import ArbitrApiClient, ArbitrApiError
from .arbitr_stubs import (
    stub_details_by_id,
    stub_details_by_number,
    stub_pdf_download,
    stub_search_cases,
)

tracer = trace.get_tracer(__name__)


async def _ctx_info(ctx: Optional[Context], message: str) -> None:
    if ctx:
        try:
            await ctx.info(message)
        except Exception:
            pass


async def _ctx_progress(ctx: Optional[Context], progress: int, total: int = 100) -> None:
    if ctx:
        try:
            await ctx.report_progress(progress=progress, total=total)
        except Exception:
            pass


@mcp.tool(
    name="arbitr_search_cases",
    description="Поиск арбитражных дел на kad.arbitr.ru через api-assist. Поддерживает фильтры по ИНН/названию, роли, датам, суду и типу дела.",
)
async def search_cases(
    page: Optional[int] = Field(None, description="Номер страницы (начиная с 1)."),
    Inn: Optional[str] = Field(None, description="ИНН или наименование участника процесса."),
    InnType: Optional[str] = Field("Any", description="Any, Plaintiff, Respondent, Third, Other."),
    DateFrom: Optional[str] = Field(None, description="Дата начала поиска YYYY-MM-DD."),
    DateTo: Optional[str] = Field(None, description="Дата окончания поиска YYYY-MM-DD."),
    Court: Optional[str] = Field(None, description="Наименование суда как на kad.arbitr.ru."),
    CaseType: Optional[str] = Field(None, description="Тип дела: A, B, G."),
    ctx: Context = None,
) -> dict:
    """Search cases on kad.arbitr.ru via api-assist."""

    start = time.perf_counter()
    settings = get_settings()
    mode = settings.mode
    tool_name = "arbitr_search_cases"

    await _ctx_info(ctx, "🔍 Запуск поиска дел")
    await _ctx_progress(ctx, 5)

    try:
        with tracer.start_as_current_span(tool_name) as span:
            span.set_attribute("mode", mode)
            span.set_attribute("case_mode", "search")

            if mode == "test":
                data = stub_search_cases()
            else:
                client = ArbitrApiClient(settings)
                data = await client.search_cases(
                    page=page,
                    Inn=Inn,
                    InnType=InnType,
                    DateFrom=DateFrom,
                    DateTo=DateTo,
                    Court=Court,
                    CaseType=CaseType,
                )

            cases = data.get("Cases", []) if isinstance(data, dict) else []
            pages = data.get("PagesCount") if isinstance(data, dict) else None

            summary_lines = [f"Найдено дел: {len(cases)}"]
            if pages:
                summary_lines.append(f"Всего страниц: {pages}")

            for case in cases[:5]:
                summary_lines.append(f"№ {case.get('CaseNumber')} — {case.get('Court')} ({case.get('CaseType')})")

            await _ctx_progress(ctx, 100)
            record_tool_call(tool_name, "ok", mode)

            return {
                "content": [TextContent(type="text", text="\n".join(summary_lines))],
                "structured_content": data,
                "meta": {"mode": mode, "pages": pages, "returned": len(cases)},
            }
    except ArbitrApiError as exc:
        record_tool_call(tool_name, "fail", mode)
        raise McpError(ErrorData(code=-32603, message=str(exc)))
    except Exception as exc:
        record_tool_call(tool_name, "fail", mode)
        raise McpError(ErrorData(code=-32603, message=f"Failed to search cases: {exc}"))
    finally:
        observe_duration(tool_name, mode, time.perf_counter() - start)


@mcp.tool(
    name="arbitr_details_by_number",
    description="Получить детальную информацию по номеру дела на kad.arbitr.ru.",
)
async def get_case_by_number(
    CaseNumber: str = Field(..., description="Номер дела, например А71-1202/2015"),
    ctx: Context = None,
) -> dict:
    """Fetch detailed case info by case number."""

    start = time.perf_counter()
    settings = get_settings()
    mode = settings.mode
    tool_name = "arbitr_details_by_number"

    await _ctx_info(ctx, f"ℹ️ Запрос деталей по делу {CaseNumber}")
    await _ctx_progress(ctx, 5)

    try:
        with tracer.start_as_current_span(tool_name) as span:
            span.set_attribute("mode", mode)
            span.set_attribute("case_number", CaseNumber)

            if mode == "test":
                data = stub_details_by_number()
            else:
                client = ArbitrApiClient(settings)
                data = await client.details_by_number(CaseNumber)

            cases = data.get("Cases", []) if isinstance(data, dict) else []
            title = cases[0].get("CaseNumber") if cases else CaseNumber
            status = cases[0].get("State") if cases else "—"

            human_text = f"Дело {title}\nСтатус: {status}\nИнстанций: {len(cases[0].get('CaseInstances', [])) if cases else 0}"

            await _ctx_progress(ctx, 100)
            record_tool_call(tool_name, "ok", mode)

            return {
                "content": [TextContent(type="text", text=human_text)],
                "structured_content": data,
                "meta": {"mode": mode, "case_number": CaseNumber},
            }
    except ArbitrApiError as exc:
        record_tool_call(tool_name, "fail", mode)
        raise McpError(ErrorData(code=-32603, message=str(exc)))
    except Exception as exc:
        record_tool_call(tool_name, "fail", mode)
        raise McpError(ErrorData(code=-32603, message=f"Failed to fetch case by number: {exc}"))
    finally:
        observe_duration(tool_name, mode, time.perf_counter() - start)


@mcp.tool(
    name="arbitr_details_by_id",
    description="Получить детальную информацию по ID дела на kad.arbitr.ru.",
)
async def get_case_by_id(
    CaseId: str = Field(..., description="UUID дела, например b82051d4-9713-4dcd-8de5-ef6d18d8ac66"),
    ctx: Context = None,
) -> dict:
    """Fetch detailed case info by case ID."""

    start = time.perf_counter()
    settings = get_settings()
    mode = settings.mode
    tool_name = "arbitr_details_by_id"

    await _ctx_info(ctx, f"ℹ️ Запрос деталей по ID дела {CaseId}")
    await _ctx_progress(ctx, 5)

    try:
        with tracer.start_as_current_span(tool_name) as span:
            span.set_attribute("mode", mode)
            span.set_attribute("case_id", CaseId)

            if mode == "test":
                data = stub_details_by_id()
            else:
                client = ArbitrApiClient(settings)
                data = await client.details_by_id(CaseId)

            cases = data.get("Cases", []) if isinstance(data, dict) else []
            title = cases[0].get("CaseNumber") if cases else CaseId
            status = cases[0].get("State") if cases else "—"

            human_text = f"Дело {title}\nСтатус: {status}\nID: {CaseId}"

            await _ctx_progress(ctx, 100)
            record_tool_call(tool_name, "ok", mode)

            return {
                "content": [TextContent(type="text", text=human_text)],
                "structured_content": data,
                "meta": {"mode": mode, "case_id": CaseId},
            }
    except ArbitrApiError as exc:
        record_tool_call(tool_name, "fail", mode)
        raise McpError(ErrorData(code=-32603, message=str(exc)))
    except Exception as exc:
        record_tool_call(tool_name, "fail", mode)
        raise McpError(ErrorData(code=-32603, message=f"Failed to fetch case by id: {exc}"))
    finally:
        observe_duration(tool_name, mode, time.perf_counter() - start)


@mcp.tool(
    name="arbitr_download_pdf",
    description="Скачать PDF судебного документа по прямой ссылке с kad.arbitr.ru через api-assist.",
)
async def download_case_pdf(
    url: str = Field(..., description="Полный URL PDF файла с kad.arbitr.ru"),
    ctx: Context = None,
) -> dict:
    """Download PDF content (base64) by URL."""

    start = time.perf_counter()
    settings = get_settings()
    mode = settings.mode
    tool_name = "arbitr_download_pdf"

    await _ctx_info(ctx, "📥 Скачивание PDF документа")
    await _ctx_progress(ctx, 5)

    try:
        with tracer.start_as_current_span(tool_name) as span:
            span.set_attribute("mode", mode)
            span.set_attribute("url", url)

            if mode == "test":
                data = stub_pdf_download()
            else:
                client = ArbitrApiClient(settings)
                data = await client.download_pdf(url)

            pdf_content = data.get("pdfContent")
            length = len(pdf_content or "")
            human_text = "PDF не найден" if not pdf_content else f"Получен PDF (base64), длина: {length} символов"

            await _ctx_progress(ctx, 100)
            record_tool_call(tool_name, "ok", mode)

            return {
                "content": [TextContent(type="text", text=human_text)],
                "structured_content": data,
                "meta": {"mode": mode, "has_pdf": bool(pdf_content), "length": length},
            }
    except ArbitrApiError as exc:
        record_tool_call(tool_name, "fail", mode)
        raise McpError(ErrorData(code=-32603, message=str(exc)))
    except Exception as exc:
        record_tool_call(tool_name, "fail", mode)
        raise McpError(ErrorData(code=-32603, message=f"Failed to download PDF: {exc}"))
    finally:
        observe_duration(tool_name, mode, time.perf_counter() - start)


