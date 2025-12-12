"""Получение полных данных о компании из ЕГРЮЛ/ЕГРИП."""

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
    name="get_company_data",
    description="""Получение всех актуальных и исторических данных о компании из ЕГРЮЛ/ЕГРИП.
Включает информацию об учредителях, руководителях, видах деятельности, адресах, лицензиях и истории изменений.""",
)
async def get_company_data(
    req: str = Field(..., description="ОГРН или ИНН компании (юридического лица или ИП)"),
    ctx: Context = None
) -> ToolResult:
    """Получение данных о компании через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("get_company_data") as span:
        span.set_attribute("req", req)
        span.set_attribute("mode", mode)
        
        await ctx.info("📋 Начинаем получение данных о компании")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_egr()
            
            items = mock_data.get("items", [])
            if items:
                item = items[0]
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text = f"Данные о компании:\n\n"
                    human_text += f"Наименование: {ul.get('НаимПолнЮЛ', 'N/A')}\n"
                    human_text += f"Краткое: {ul.get('НаимСокрЮЛ', 'N/A')}\n"
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, КПП: {ul.get('КПП', 'N/A')}\n"
                    human_text += f"ОГРН: {ul.get('ОГРН', 'N/A')}\n"
                    human_text += f"Дата регистрации: {ul.get('ДатаРег', 'N/A')}\n"
                    human_text += f"Статус: {ul.get('Статус', 'N/A')}\n"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text = f"Данные об ИП:\n\n"
                    human_text += f"ФИО: {ip.get('ФИОПолн', 'N/A')}\n"
                    human_text += f"ИНН: {ip.get('ИННФЛ', 'N/A')}\n"
                    human_text += f"ОГРН: {ip.get('ОГРНИП', 'N/A')}\n"
                    human_text += f"Дата регистрации: {ip.get('ДатаРег', 'N/A')}\n"
                    human_text += f"Статус: {ip.get('Статус', 'N/A')}\n"
            else:
                human_text = "Данные не найдены"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Данные получены (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "req": req}
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
                
                url = "https://api-fns.ru/api/egr"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            items = result.get("items", [])
            if items:
                item = items[0]
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text = f"Данные о компании:\n\n"
                    human_text += f"Наименование: {ul.get('НаимПолнЮЛ', 'N/A')}\n"
                    human_text += f"Краткое: {ul.get('НаимСокрЮЛ', 'N/A')}\n"
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, КПП: {ul.get('КПП', 'N/A')}\n"
                    human_text += f"ОГРН: {ul.get('ОГРН', 'N/A')}\n"
                    human_text += f"Дата регистрации: {ul.get('ДатаРег', 'N/A')}\n"
                    human_text += f"Статус: {ul.get('Статус', 'N/A')}\n"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text = f"Данные об ИП:\n\n"
                    human_text += f"ФИО: {ip.get('ФИОПолн', 'N/A')}\n"
                    human_text += f"ИНН: {ip.get('ИННФЛ', 'N/A')}\n"
                    human_text += f"ОГРН: {ip.get('ОГРНИП', 'N/A')}\n"
                    human_text += f"Дата регистрации: {ip.get('ДатаРег', 'N/A')}\n"
                    human_text += f"Статус: {ip.get('Статус', 'N/A')}\n"
            else:
                human_text = "Данные не найдены"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Данные получены успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "req": req}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось получить данные о компании"))

