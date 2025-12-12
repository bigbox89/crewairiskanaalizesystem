"""Проверка статусов физического лица."""

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
    name="check_person_status",
    description="""Проверка статусов физического лица.
Проверяет: статус самозанятого, является ли ИП, банкротство, недействительность ИНН, дисквалификацию.""",
)
async def check_person_status(
    inn: str = Field(..., description="ИНН физического лица (12 цифр)"),
    ctx: Context = None
) -> ToolResult:
    """Проверка статусов физлица через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("check_person_status") as span:
        span.set_attribute("inn", inn)
        span.set_attribute("mode", mode)
        
        await ctx.info("🔍 Начинаем проверку статусов физлица")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_fl_status()
            
            human_text = f"Статусы для ИНН: {inn}\n\n"
            
            korrektnost = mock_data.get("Корректность", {})
            if korrektnost:
                human_text += "Корректность ИНН:\n"
                human_text += f"  Контрольная сумма: {korrektnost.get('КонтрСумма', 'N/A')}\n"
                human_text += f"  Недействительный: {korrektnost.get('Недействительный', 'N/A')}\n\n"
            
            samozanyatost = mock_data.get("Самозанятость", {})
            if samozanyatost:
                human_text += "Самозанятость:\n"
                human_text += f"  Статус: {samozanyatost.get('Статус', 'N/A')}\n"
                human_text += f"  {samozanyatost.get('Текст', 'N/A')}\n\n"
            
            ip = mock_data.get("ИП", {})
            if ip:
                human_text += "Индивидуальный предприниматель:\n"
                human_text += f"  Статус: {ip.get('Статус', 'N/A')}\n"
                human_text += f"  {ip.get('Текст', 'N/A')}\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Проверка завершена (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "inn": inn}
            )
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                params = {
                    "inn": inn,
                    "key": token
                }
                
                url = "https://api-fns.ru/api/fl_status"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            human_text = f"Статусы для ИНН: {inn}\n\n"
            
            korrektnost = result.get("Корректность", {})
            if korrektnost:
                human_text += "Корректность ИНН:\n"
                human_text += f"  Контрольная сумма: {korrektnost.get('КонтрСумма', 'N/A')}\n"
                human_text += f"  Недействительный: {korrektnost.get('Недействительный', 'N/A')}\n\n"
            
            samozanyatost = result.get("Самозанятость", {})
            if samozanyatost:
                human_text += "Самозанятость:\n"
                human_text += f"  Статус: {samozanyatost.get('Статус', 'N/A')}\n"
                human_text += f"  {samozanyatost.get('Текст', 'N/A')}\n\n"
            
            ip = result.get("ИП", {})
            if ip:
                human_text += "Индивидуальный предприниматель:\n"
                human_text += f"  Статус: {ip.get('Статус', 'N/A')}\n"
                human_text += f"  {ip.get('Текст', 'N/A')}\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Проверка завершена успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "inn": inn}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось проверить статусы физлица"))

