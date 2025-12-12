"""Узнать ИНН физического лица по паспортным данным."""

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
    name="get_inn_by_passport",
    description="""Узнать ИНН физического лица по паспортным данным.
Требует ФИО, дату рождения и данные документа, удостоверяющего личность.""",
)
async def get_inn_by_passport(
    fam: str = Field(..., description="Фамилия"),
    nam: str = Field(..., description="Имя"),
    otch: str = Field(..., description="Отчество (если отсутствует - укажите 'нет')"),
    bdate: str = Field(..., description="Дата рождения в формате ДД.ММ.ГГГГ"),
    docno: str = Field(..., description="Серия и номер документа (можно с пробелами или без)"),
    doctype: Optional[str] = Field("21", description="Вид документа: 21 - Паспорт РФ (по умолчанию), 01 - Паспорт СССР, 03 - Свидетельство о рождении и т.д."),
    ctx: Context = None
) -> ToolResult:
    """Получение ИНН по паспорту через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("get_inn_by_passport") as span:
        span.set_attribute("fam", fam)
        span.set_attribute("mode", mode)
        
        await ctx.info("🔍 Начинаем поиск ИНН по паспорту")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_innfl()
            
            items = mock_data.get("items", [])
            if items and "ИНН" in items[0]:
                inn = items[0]["ИНН"]
                human_text = f"ИНН найден:\n\n"
                human_text += f"ФИО: {fam} {nam} {otch}\n"
                human_text += f"Дата рождения: {bdate}\n"
                human_text += f"Документ: {docno}\n"
                human_text += f"ИНН: {inn}"
            elif items and "error" in items[0]:
                human_text = f"Ошибка: {items[0]['error']}"
            else:
                human_text = "ИНН не найден"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Поиск завершен (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "fam": fam, "nam": nam}
            )
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                params = {
                    "fam": fam,
                    "nam": nam,
                    "otch": otch,
                    "bdate": bdate,
                    "docno": docno.replace(" ", ""),  # Убираем пробелы
                    "doctype": doctype or "21",
                    "key": token
                }
                
                url = "https://api-fns.ru/api/innfl"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            items = result.get("items", [])
            if items and "ИНН" in items[0]:
                inn = items[0]["ИНН"]
                human_text = f"ИНН найден:\n\n"
                human_text += f"ФИО: {fam} {nam} {otch}\n"
                human_text += f"Дата рождения: {bdate}\n"
                human_text += f"Документ: {docno}\n"
                human_text += f"ИНН: {inn}"
            elif items and "error" in items[0]:
                human_text = f"Ошибка: {items[0]['error']}"
            else:
                human_text = "ИНН не найден"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Поиск завершен успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "fam": fam, "nam": nam}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось найти ИНН"))

