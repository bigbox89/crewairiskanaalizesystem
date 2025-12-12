"""Получение реквизитов группы компаний."""

import os
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
    name="multinfo_companies",
    description="""Получение базовых данных сразу о нескольких компаниях (до 100).
Включает контактные данные, статус, адрес, виды деятельности, реестр МСП.""",
)
async def multinfo_companies(
    req: str = Field(..., description="ОГРН или ИНН компаний, разделенные запятыми (до 100 компаний)"),
    ctx: Context = None
) -> ToolResult:
    """Получение данных о группе компаний через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("multinfo_companies") as span:
        span.set_attribute("req", req)
        span.set_attribute("mode", mode)
        
        await ctx.info("📋 Начинаем получение данных о группе компаний")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_multinfo()
            
            items = mock_data.get("items", [])
            human_text = f"Найдено компаний: {len(items)}\n\n"
            
            for item in items:
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text += f"ЮЛ: {ul.get('НаимСокрЮЛ', 'N/A')}\n"
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, ОГРН: {ul.get('ОГРН', 'N/A')}\n"
                    human_text += f"Статус: {ul.get('Статус', 'N/A')}\n"
                    if "Контакты" in ul:
                        human_text += f"Контакты: {ul.get('Контакты', 'N/A')}\n"
                    human_text += "\n"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text += f"ИП: {ip.get('ФИОПолн', 'N/A')}\n"
                    human_text += f"ИНН: {ip.get('ИННФЛ', 'N/A')}, ОГРН: {ip.get('ОГРНИП', 'N/A')}\n"
                    human_text += f"Статус: {ip.get('Статус', 'N/A')}\n"
                    if "Контакты" in ip:
                        human_text += f"Контакты: {ip.get('Контакты', 'N/A')}\n"
                    human_text += "\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Данные получены (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "req": req, "count": len(items)}
            )
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                params = {
                    "req": req,
                    "key": token
                }
                
                url = "https://api-fns.ru/api/multinfo"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            items = result.get("items", [])
            human_text = f"Найдено компаний: {len(items)}\n\n"
            
            for item in items:
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text += f"ЮЛ: {ul.get('НаимСокрЮЛ', 'N/A')}\n"
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, ОГРН: {ul.get('ОГРН', 'N/A')}\n"
                    human_text += f"Статус: {ul.get('Статус', 'N/A')}\n"
                    if "Контакты" in ul:
                        human_text += f"Контакты: {ul.get('Контакты', 'N/A')}\n"
                    human_text += "\n"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text += f"ИП: {ip.get('ФИОПолн', 'N/A')}\n"
                    human_text += f"ИНН: {ip.get('ИННФЛ', 'N/A')}, ОГРН: {ip.get('ОГРНИП', 'N/A')}\n"
                    human_text += f"Статус: {ip.get('Статус', 'N/A')}\n"
                    if "Контакты" in ip:
                        human_text += f"Контакты: {ip.get('Контакты', 'N/A')}\n"
                    human_text += "\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Данные получены успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "req": req, "count": len(items)}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось получить данные о группе компаний"))

