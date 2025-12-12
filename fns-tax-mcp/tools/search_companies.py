"""Поиск компаний по различным параметрам."""

import os
from typing import Optional
from fastmcp import Context
from mcp.types import TextContent
from opentelemetry import trace
from pydantic import Field
from mcp_instance import mcp
from .utils import ToolResult
from mcp.shared.exceptions import McpError, ErrorData
import httpx
from . import mocks

tracer = trace.get_tracer(__name__)


@mcp.tool(
    name="search_companies",
    description="""Поиск компаний, ИП и физических лиц в ЕГРЮЛ/ЕГРИП.
Поддерживает поиск по ИНН, ОГРН, ФИО, названию организации, адресу, контактам.
Возвращает список найденных организаций с основными реквизитами.""",
)
async def search_companies(
    q: str = Field(..., description="Поисковая строка: ИНН, ОГРН, ФИО, название, адрес и т.д."),
    page: Optional[int] = Field(None, description="Номер страницы (по умолчанию 1)"),
    filter: Optional[str] = Field(None, description="Фильтры: active, onlyul, onlyip, okved, region и т.д. (разделять +)"),
    ctx: Context = None
) -> ToolResult:
    """Поиск компаний через API-ФНС."""
    
    mode = os.getenv("FNS_MODE", "test").lower()
    
    
    with tracer.start_as_current_span("search_companies") as span:
        span.set_attribute("query", q)
        span.set_attribute("page", page or 1)
        span.set_attribute("mode", mode)
        
        await ctx.info("🔍 Начинаем поиск компаний")
        await ctx.report_progress(progress=0, total=100)
        
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_search()
            
            # Формируем человекочитаемый текст
            items_count = len(mock_data.get("items", []))
            human_text = f"Найдено компаний: {items_count}\n\n"
            
            for item in mock_data.get("items", [])[:5]:  # Показываем первые 5
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text += f"ЮЛ: {ul.get('НаимСокрЮЛ', 'N/A')}\n"
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, ОГРН: {ul.get('ОГРН', 'N/A')}\n"
                    human_text += f"Статус: {ul.get('Статус', 'N/A')}\n\n"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text += f"ИП: {ip.get('ФИОПолн', 'N/A')}\n"
                    human_text += f"ИНН: {ip.get('ИНН', 'N/A')}, ОГРН: {ip.get('ОГРН', 'N/A')}\n"
                    human_text += f"Статус: {ip.get('Статус', 'N/A')}\n\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Поиск завершен (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "query": q, "count": items_count}
            )
        
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                params = {
                    "q": q,
                    "key": token
                }
                if page:
                    params["page"] = page
                if filter:
                    params["filter"] = filter
                
                url = "https://api-fns.ru/api/search"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            # Формируем человекочитаемый текст
            items = result.get("items", [])
            count = result.get("Count", len(items))
            human_text = f"Найдено компаний: {count}\n\n"
            
            for item in items[:5]:  # Показываем первые 5
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text += f"ЮЛ: {ul.get('НаимСокрЮЛ', 'N/A')}\n"
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, ОГРН: {ul.get('ОГРН', 'N/A')}\n"
                    human_text += f"Статус: {ul.get('Статус', 'N/A')}\n\n"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text += f"ИП: {ip.get('ФИОПолн', 'N/A')}\n"
                    human_text += f"ИНН: {ip.get('ИНН', 'N/A')}, ОГРН: {ip.get('ОГРН', 'N/A')}\n"
                    human_text += f"Статус: {ip.get('Статус', 'N/A')}\n\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Поиск завершен успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "query": q, "count": count, "page": page or 1}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось выполнить поиск"))

