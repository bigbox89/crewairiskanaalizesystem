"""Отслеживание изменений параметров компании."""

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
    name="track_changes",
    description="""Отслеживание изменений параметров компании в ЕГРЮЛ/ЕГРИП.
Возвращает хронологию изменений данных о компании, начиная с указанной даты.""",
)
async def track_changes(
    req: str = Field(..., description="ОГРН или ИНН компании (юридического лица или ИП)"),
    dat: Optional[str] = Field(None, description="Дата в формате YYYY-MM-DD, начиная с которой вывести изменения (необязательно)"),
    ctx: Context = None
) -> ToolResult:
    """Отслеживание изменений через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("track_changes") as span:
        span.set_attribute("req", req)
        span.set_attribute("dat", dat or "all")
        span.set_attribute("mode", mode)
        
        await ctx.info("📋 Начинаем отслеживание изменений")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_changes()
            
            items = mock_data.get("items", [])
            if items:
                item = items[0]
                human_text = f"Изменения для компании:\n\n"
                
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, ОГРН: {ul.get('ОГРН', 'N/A')}\n\n"
                    izmeneniya = ul.get("Изменения", [])
                    if izmeneniya:
                        human_text += "История изменений:\n"
                        for izm in izmeneniya[:10]:  # Показываем первые 10
                            human_text += f"  - {izm.get('Дата', 'N/A')}: {izm.get('Тип', 'N/A')} - {izm.get('Текст', 'N/A')}\n"
                    else:
                        human_text += "Изменений не найдено"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text += f"ИНН: {ip.get('ИННФЛ', 'N/A')}, ОГРН: {ip.get('ОГРНИП', 'N/A')}\n\n"
                    izmeneniya = ip.get("Изменения", [])
                    if izmeneniya and isinstance(izmeneniya, list):
                        human_text += "История изменений:\n"
                        for izm in izmeneniya[:10]:
                            human_text += f"  - {izm.get('Дата', 'N/A')}: {izm.get('Тип', 'N/A')} - {izm.get('Текст', 'N/A')}\n"
                    elif izmeneniya and isinstance(izmeneniya, dict):
                        # Если это словарь, выводим его содержимое
                        human_text += "История изменений:\n"
                        for key, value in list(izmeneniya.items())[:10]:
                            human_text += f"  - {key}: {value}\n"
                    else:
                        human_text += "Изменений не найдено"
            else:
                human_text = "Данные не найдены"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Отслеживание завершено (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "req": req, "dat": dat}
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
                if dat:
                    params["dat"] = dat
                
                url = "https://api-fns.ru/api/changes"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            items = result.get("items", [])
            if items:
                item = items[0]
                human_text = f"Изменения для компании:\n\n"
                
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, ОГРН: {ul.get('ОГРН', 'N/A')}\n\n"
                    izmeneniya = ul.get("Изменения", [])
                    if izmeneniya and isinstance(izmeneniya, list):
                        human_text += "История изменений:\n"
                        for izm in izmeneniya[:10]:
                            human_text += f"  - {izm.get('Дата', 'N/A')}: {izm.get('Тип', 'N/A')} - {izm.get('Текст', 'N/A')}\n"
                    elif izmeneniya and isinstance(izmeneniya, dict):
                        # Если это словарь, выводим его содержимое
                        human_text += "История изменений:\n"
                        for key, value in list(izmeneniya.items())[:10]:
                            human_text += f"  - {key}: {value}\n"
                    else:
                        human_text += "Изменений не найдено"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text += f"ИНН: {ip.get('ИННФЛ', 'N/A')}, ОГРН: {ip.get('ОГРНИП', 'N/A')}\n\n"
                    izmeneniya = ip.get("Изменения", [])
                    if izmeneniya and isinstance(izmeneniya, list):
                        human_text += "История изменений:\n"
                        for izm in izmeneniya[:10]:
                            human_text += f"  - {izm.get('Дата', 'N/A')}: {izm.get('Тип', 'N/A')} - {izm.get('Текст', 'N/A')}\n"
                    elif izmeneniya and isinstance(izmeneniya, dict):
                        # Если это словарь, выводим его содержимое
                        human_text += "История изменений:\n"
                        for key, value in list(izmeneniya.items())[:10]:
                            human_text += f"  - {key}: {value}\n"
                    else:
                        human_text += "Изменений не найдено"
            else:
                human_text = "Данные не найдены"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Отслеживание завершено успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "req": req, "dat": dat}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось отследить изменения"))

