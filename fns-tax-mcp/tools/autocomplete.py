"""Автодополнение для поиска компаний."""

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
    name="autocomplete",
    description="""Автодополнение для поиска компаний и ИП.
Поддерживает поиск по первым буквам названия (более 2-х букв), полным названиям, ФИО ИП, цифрам ИНН (более 5-ти цифр).
Возвращает до 100 значений.""",
)
async def autocomplete(
    q: str = Field(..., description="Поисковая строка (первые буквы названия, ФИО ИП или ИНН)"),
    filter: Optional[str] = Field(None, description="Фильтры: active, onlyul, onlyip (разделять +)"),
    ctx: Context = None
) -> ToolResult:
    """Автодополнение через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("autocomplete") as span:
        span.set_attribute("query", q)
        span.set_attribute("mode", mode)
        
        await ctx.info("🔍 Начинаем автодополнение")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_ac()
            
            items = mock_data.get("items", [])
            human_text = f"Найдено вариантов: {len(items)}\n\n"
            
            for item in items[:10]:  # Показываем первые 10
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text += f"ЮЛ: {ul.get('НаимСокрЮЛ', 'N/A')}\n"
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, ОГРН: {ul.get('ОГРН', 'N/A')}\n\n"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text += f"ИП: {ip.get('ФИОПолн', 'N/A')}\n"
                    human_text += f"ИНН: {ip.get('ИННФЛ', 'N/A')}, ОГРН: {ip.get('ОГРНИП', 'N/A')}\n\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Автодополнение завершено (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "query": q, "count": len(items)}
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
                if filter and isinstance(filter, str):
                    params["filter"] = filter
                
                url = "https://api-fns.ru/api/ac"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            items = result.get("items", [])
            human_text = f"Найдено вариантов: {len(items)}\n\n"
            
            for item in items[:10]:
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text += f"ЮЛ: {ul.get('НаимСокрЮЛ', 'N/A')}\n"
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, ОГРН: {ul.get('ОГРН', 'N/A')}\n\n"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text += f"ИП: {ip.get('ФИОПолн', 'N/A')}\n"
                    human_text += f"ИНН: {ip.get('ИННФЛ', 'N/A')}, ОГРН: {ip.get('ОГРНИП', 'N/A')}\n\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Автодополнение завершено успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "query": q, "count": len(items)}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось выполнить автодополнение"))

