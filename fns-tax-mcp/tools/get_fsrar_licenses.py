"""Получение лицензий ФСРАР."""

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
    name="get_fsrar_licenses",
    description="""Получение лицензий ФСРАР для компании.
Возвращает информацию о лицензиях на производство, оборот этилового спирта, алкогольной и спиртосодержащей продукции.""",
)
async def get_fsrar_licenses(
    inn: str = Field(..., description="ИНН компании"),
    status: Optional[str] = Field(None, description="Статус лицензии: действующая, аннулирована, срок действия истек и т.д. (необязательно)"),
    kpp: Optional[str] = Field(None, description="КПП компании (необязательно)"),
    ctx: Context = None
) -> ToolResult:
    """Получение лицензий ФСРАР через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("get_fsrar_licenses") as span:
        span.set_attribute("inn", inn)
        span.set_attribute("mode", mode)
        
        await ctx.info("🔍 Начинаем получение лицензий ФСРАР")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_fsrar()
            
            items = mock_data.get("items", [])
            human_text = f"Лицензии ФСРАР для ИНН: {inn}\n\n"
            
            if items:
                for lic in items:
                    human_text += f"Номер лицензии: {lic.get('Номер лицензии', 'N/A')}\n"
                    human_text += f"Вид лицензии: {lic.get('Вид лицензии', 'N/A')}\n"
                    human_text += f"Дата выдачи: {lic.get('Дата выдачи', 'N/A')}\n"
                    human_text += f"Дата окончания: {lic.get('Дата окончания', 'N/A')}\n"
                    human_text += f"Статус: {lic.get('Статус лицензии', 'N/A')}\n\n"
            else:
                human_text += "Лицензий не найдено"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Лицензии получены (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "inn": inn, "count": len(items)}
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
                if status:
                    params["status"] = status
                if kpp:
                    params["kpp"] = kpp
                
                url = "https://api-fns.ru/api/fsrar"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            items = result.get("items", [])
            human_text = f"Лицензии ФСРАР для ИНН: {inn}\n\n"
            
            if items:
                for lic in items:
                    human_text += f"Номер лицензии: {lic.get('Номер лицензии', 'N/A')}\n"
                    human_text += f"Вид лицензии: {lic.get('Вид лицензии', 'N/A')}\n"
                    human_text += f"Дата выдачи: {lic.get('Дата выдачи', 'N/A')}\n"
                    human_text += f"Дата окончания: {lic.get('Дата окончания', 'N/A')}\n"
                    human_text += f"Статус: {lic.get('Статус лицензии', 'N/A')}\n\n"
            else:
                human_text += "Лицензий не найдено"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Лицензии получены успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "inn": inn, "count": len(items)}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось получить лицензии ФСРАР"))

