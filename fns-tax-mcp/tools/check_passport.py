"""Проверка паспорта на недействительность."""

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
    name="check_passport",
    description="""Проверка паспорта на недействительность.
Проверяет серию и номер паспорта по списку недействительных российских паспортов.""",
)
async def check_passport(
    docno: str = Field(..., description="Серия и номер паспорта (можно с пробелами или без)"),
    ctx: Context = None
) -> ToolResult:
    """Проверка паспорта через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("check_passport") as span:
        span.set_attribute("docno", docno)
        span.set_attribute("mode", mode)
        
        await ctx.info("🔍 Начинаем проверку паспорта")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_mvdpass()
            
            result_text = mock_data.get("result", "Cреди недействительных не значится")
            human_text = f"Проверка паспорта: {docno}\n\n"
            human_text += f"Результат: {result_text}"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Проверка завершена (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "docno": docno}
            )
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                params = {
                    "docno": docno.replace(" ", ""),  # Убираем пробелы
                    "key": token
                }
                
                url = "https://api-fns.ru/api/mvdpass"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            result_text = result.get("result", "Cреди недействительных не значится")
            human_text = f"Проверка паспорта: {docno}\n\n"
            human_text += f"Результат: {result_text}"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Проверка завершена успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "docno": docno}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось проверить паспорт"))


@mcp.tool(
    name="check_passport_info",
    description="""Информация о паспорте с причиной недействительности.
Возвращает причину недействительности, если паспорт найден в списке недействительных.""",
)
async def check_passport_info(
    docno: str = Field(..., description="Серия и номер паспорта (можно с пробелами или без)"),
    ctx: Context = None
) -> ToolResult:
    """Проверка паспорта с информацией через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("check_passport_info") as span:
        span.set_attribute("docno", docno)
        span.set_attribute("mode", mode)
        
        await ctx.info("🔍 Начинаем проверку паспорта с информацией")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_mvdinfo()
            
            result_text = mock_data.get("result", "Cреди недействительных не значится")
            human_text = f"Проверка паспорта: {docno}\n\n"
            human_text += f"Результат: {result_text}"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Проверка завершена (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "docno": docno}
            )
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                params = {
                    "docno": docno.replace(" ", ""),  # Убираем пробелы
                    "key": token
                }
                
                url = "https://api-fns.ru/api/mvdinfo"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            result_text = result.get("result", "Cреди недействительных не значится")
            human_text = f"Проверка паспорта: {docno}\n\n"
            human_text += f"Результат: {result_text}"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Проверка завершена успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "docno": docno}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось проверить паспорт"))

