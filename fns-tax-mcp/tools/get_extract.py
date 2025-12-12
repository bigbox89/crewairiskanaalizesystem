"""Получение выписок из ЕГРЮЛ/ЕГРИП."""

import os
import base64
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
    name="get_extract",
    description="""Получение официальной выписки ФНС из ЕГРЮЛ или ЕГРИП.
Возвращает выписку в формате PDF, заверенную подписью ФНС.""",
)
async def get_extract(
    req: str = Field(..., description="ОГРН или ИНН компании (юридического лица или ИП)"),
    ctx: Context = None
) -> ToolResult:
    """Получение выписки через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("get_extract") as span:
        span.set_attribute("req", req)
        span.set_attribute("mode", mode)
        
        await ctx.info("📄 Начинаем получение выписки")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            file_base64 = mocks.mock_file_base64()
            
            human_text = f"Выписка из ЕГРЮЛ/ЕГРИП для: {req}\n"
            human_text += "Формат: PDF (заверен подписью ФНС)\n"
            human_text += "Размер: тестовый файл"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Выписка получена (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content={
                    "file_base64": file_base64,
                    "file_type": "pdf",
                    "req": req
                },
                meta={"mode": "test", "req": req}
            )
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                params = {
                    "req": req,
                    "key": token
                }
                
                url = "https://api-fns.ru/api/vyp"
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                # Получаем бинарные данные
                file_data = response.content
                file_base64 = base64.b64encode(file_data).decode('utf-8')
            
            await ctx.report_progress(progress=100, total=100)
            
            human_text = f"Выписка из ЕГРЮЛ/ЕГРИП для: {req}\n"
            human_text += "Формат: PDF (заверен подписью ФНС)\n"
            human_text += f"Размер: {len(file_data)} байт"
            
            await ctx.info("✅ Выписка получена успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content={
                    "file_base64": file_base64,
                    "file_type": "pdf",
                    "req": req,
                    "size_bytes": len(file_data)
                },
                meta={"mode": "prod", "req": req}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось получить выписку"))


@mcp.tool(
    name="get_msp_extract",
    description="""Получение выписки из реестра МСП.
Возвращает выписку в формате PDF: сведения из Единого реестра субъектов малого и среднего предпринимательства.""",
)
async def get_msp_extract(
    req: str = Field(..., description="ОГРН или ИНН компании (юридического лица или ИП)"),
    type: str = Field("report", description="Тип выписки: report (обычная), periods (периоды), pp-report (получатель поддержки)"),
    ctx: Context = None
) -> ToolResult:
    """Получение выписки МСП через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("get_msp_extract") as span:
        span.set_attribute("req", req)
        span.set_attribute("mode", mode)
        
        await ctx.info("📄 Начинаем получение выписки МСП")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            file_base64 = mocks.mock_file_base64()
            
            human_text = f"Выписка МСП для: {req}\n"
            human_text += f"Тип: {type}\n"
            human_text += "Формат: PDF\n"
            human_text += "Размер: тестовый файл"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Выписка получена (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content={
                    "file_base64": file_base64,
                    "file_type": "pdf",
                    "req": req,
                    "type": type
                },
                meta={"mode": "test", "req": req}
            )
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                params = {
                    "req": req,
                    "type": type,
                    "key": token
                }
                
                url = "https://api-fns.ru/api/mspinfo_file"
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                # Получаем бинарные данные
                file_data = response.content
                file_base64 = base64.b64encode(file_data).decode('utf-8')
            
            await ctx.report_progress(progress=100, total=100)
            
            human_text = f"Выписка МСП для: {req}\n"
            human_text += f"Тип: {type}\n"
            human_text += "Формат: PDF\n"
            human_text += f"Размер: {len(file_data)} байт"
            
            await ctx.info("✅ Выписка получена успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content={
                    "file_base64": file_base64,
                    "file_type": "pdf",
                    "req": req,
                    "type": type,
                    "size_bytes": len(file_data)
                },
                meta={"mode": "prod", "req": req}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось получить выписку МСП"))

