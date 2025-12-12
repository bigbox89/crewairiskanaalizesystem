"""Получение бухгалтерской отчетности."""

import os
import base64
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
    name="get_accounting_report",
    description="""Получение бухгалтерской отчетности организации (только юридические лица).
Отчетность приведена начиная с 2019 года. Доступна по формам 1 (Баланс), 2 (Отчет о прибылях и убытках), 3, 4.""",
)
async def get_accounting_report(
    req: str = Field(..., description="ОГРН или ИНН компании (юридического лица)"),
    ctx: Context = None
) -> ToolResult:
    """Получение бухгалтерской отчетности через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("get_accounting_report") as span:
        span.set_attribute("req", req)
        span.set_attribute("mode", mode)
        
        await ctx.info("📊 Начинаем получение бухгалтерской отчетности")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_bo()
            
            human_text = f"Бухгалтерская отчетность для: {req}\n\n"
            
            # Формируем текст из структуры данных
            for inn_ogrn, years_data in mock_data.items():
                human_text += f"ИНН/ОГРН: {inn_ogrn}\n\n"
                for year, codes_data in years_data.items():
                    human_text += f"Год: {year}\n"
                    for code, value in list(codes_data.items())[:5]:  # Показываем первые 5 строк
                        human_text += f"  Строка {code}: {value} тыс. руб.\n"
                    human_text += "\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Отчетность получена (тестовый режим)")
            
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
                
                url = "https://api-fns.ru/api/bo"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            human_text = f"Бухгалтерская отчетность для: {req}\n\n"
            
            # Формируем текст из структуры данных
            for inn_ogrn, years_data in result.items():
                human_text += f"ИНН/ОГРН: {inn_ogrn}\n\n"
                for year, codes_data in years_data.items():
                    human_text += f"Год: {year}\n"
                    for code, value in list(codes_data.items())[:5]:  # Показываем первые 5 строк
                        human_text += f"  Строка {code}: {value} тыс. руб.\n"
                    human_text += "\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Отчетность получена успешно")
            
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
            raise McpError(ErrorData(code=-32603, message="Не удалось получить бухгалтерскую отчетность"))


@mcp.tool(
    name="get_accounting_report_file",
    description="""Получение бухгалтерской отчетности в виде файла.
Возвращает отчетность в формате PDF или ZIP (XLS), заверенную подписью ФНС.""",
)
async def get_accounting_report_file(
    req: str = Field(..., description="ОГРН или ИНН компании (юридического лица)"),
    year: int = Field(..., description="Год отчетности"),
    xls: Optional[bool] = Field(False, description="Если True - возвращает XLS в ZIP, иначе PDF с подписью"),
    ctx: Context = None
) -> ToolResult:
    """Получение бухгалтерской отчетности в виде файла через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("get_accounting_report_file") as span:
        span.set_attribute("req", req)
        span.set_attribute("year", year)
        span.set_attribute("mode", mode)
        
        await ctx.info("📊 Начинаем получение файла отчетности")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            file_base64 = mocks.mock_file_base64()
            
            file_type = "zip" if xls else "pdf"
            human_text = f"Бухгалтерская отчетность для: {req}\n"
            human_text += f"Год: {year}\n"
            human_text += f"Формат: {file_type.upper()}\n"
            human_text += "Размер: тестовый файл"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Файл получен (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content={
                    "file_base64": file_base64,
                    "file_type": file_type,
                    "req": req,
                    "year": year
                },
                meta={"mode": "test", "req": req, "year": year}
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
                    "year": year,
                    "key": token
                }
                if xls:
                    params["xls"] = 1
                
                url = "https://api-fns.ru/api/bo_file"
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                # Получаем бинарные данные
                file_data = response.content
                file_base64 = base64.b64encode(file_data).decode('utf-8')
                file_type = "zip" if xls else "pdf"
            
            await ctx.report_progress(progress=100, total=100)
            
            human_text = f"Бухгалтерская отчетность для: {req}\n"
            human_text += f"Год: {year}\n"
            human_text += f"Формат: {file_type.upper()}\n"
            human_text += f"Размер: {len(file_data)} байт"
            
            await ctx.info("✅ Файл получен успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content={
                    "file_base64": file_base64,
                    "file_type": file_type,
                    "req": req,
                    "year": year,
                    "size_bytes": len(file_data)
                },
                meta={"mode": "prod", "req": req, "year": year}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось получить файл отчетности"))

