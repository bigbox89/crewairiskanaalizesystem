"""Проверка блокировок счета."""

import os
import base64
from fastmcp import Context
from mcp.types import TextContent
from opentelemetry import trace
from pydantic import Field
from mcp_instance import mcp
from .utils import ToolResult, ensure_allowed_in_free, get_fns_mode
from mcp.shared.exceptions import McpError, ErrorData
import httpx
from . import mocks

tracer = trace.get_tracer(__name__)


@mcp.tool(
    name="check_account_blocks",
    description="""Проверка блокировок счета компании.
Возвращает информацию о действующих решениях ФНС о приостановлении операций по счетам.""",
)
async def check_account_blocks(
    inn: str = Field(..., description="ИНН компании (юридического лица или ИП)"),
    ctx: Context = None
) -> ToolResult:
    """Проверка блокировок счета через API-ФНС."""
    mode = get_fns_mode()
    
    with tracer.start_as_current_span("check_account_blocks") as span:
        span.set_attribute("inn", inn)
        span.set_attribute("mode", mode)
        
        await ctx.info("🔍 Начинаем проверку блокировок счета")
        await ctx.report_progress(progress=0, total=100)
        await ensure_allowed_in_free("check_account_blocks", ctx)
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_nalogbi()
            
            items = mock_data.get("items", [])
            if items:
                item = items[0]
                human_text = f"Проверка блокировок счета для ИНН: {inn}\n\n"
                
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    negativ = ul.get("Негатив", {})
                    if negativ:
                        blokirovki = negativ.get("БлокировкиСчетов", [])
                        if blokirovki:
                            human_text += "❌ Найдены блокировки счетов:\n"
                            for blok in blokirovki:
                                human_text += f"  - {blok}\n"
                        else:
                            human_text += "✅ Блокировок счетов не найдено"
                    else:
                        human_text += "✅ Блокировок счетов не найдено"
                elif "ИП" in item:
                    ip = item["ИП"]
                    negativ = ip.get("Негатив", {})
                    if negativ:
                        blokirovki = negativ.get("БлокировкиСчетов", [])
                        if blokirovki:
                            human_text += "❌ Найдены блокировки счетов:\n"
                            for blok in blokirovki:
                                human_text += f"  - {blok}\n"
                        else:
                            human_text += "✅ Блокировок счетов не найдено"
                    else:
                        human_text += "✅ Блокировок счетов не найдено"
            else:
                human_text = "Данные не найдены"
            
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
                
                url = "https://api-fns.ru/api/nalogbi"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            items = result.get("items", [])
            if items:
                item = items[0]
                human_text = f"Проверка блокировок счета для ИНН: {inn}\n\n"
                
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    negativ = ul.get("Негатив", {})
                    if negativ:
                        blokirovki = negativ.get("БлокировкиСчетов", [])
                        if blokirovki:
                            human_text += "❌ Найдены блокировки счетов:\n"
                            for blok in blokirovki:
                                human_text += f"  - {blok}\n"
                        else:
                            human_text += "✅ Блокировок счетов не найдено"
                    else:
                        human_text += "✅ Блокировок счетов не найдено"
                elif "ИП" in item:
                    ip = item["ИП"]
                    negativ = ip.get("Негатив", {})
                    if negativ:
                        blokirovki = negativ.get("БлокировкиСчетов", [])
                        if blokirovki:
                            human_text += "❌ Найдены блокировки счетов:\n"
                            for blok in blokirovki:
                                human_text += f"  - {blok}\n"
                        else:
                            human_text += "✅ Блокировок счетов не найдено"
                    else:
                        human_text += "✅ Блокировок счетов не найдено"
            else:
                human_text = "Данные не найдены"
            
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
            raise McpError(ErrorData(code=-32603, message="Не удалось проверить блокировки счета"))


@mcp.tool(
    name="check_account_blocks_file",
    description="""Проверка блокировок счета в виде файла.
Возвращает ZIP файл с PDF и подписью ФНС.""",
)
async def check_account_blocks_file(
    inn: str = Field(..., description="ИНН компании (юридического лица или ИП)"),
    bik: str = Field(None, description="БИК банка, выполняющего запрос (необязательно)"),
    ctx: Context = None
) -> ToolResult:
    """Проверка блокировок счета в виде файла через API-ФНС."""
    mode = get_fns_mode()
    
    with tracer.start_as_current_span("check_account_blocks_file") as span:
        span.set_attribute("inn", inn)
        span.set_attribute("mode", mode)
        
        await ctx.info("🔍 Начинаем получение файла блокировок счета")
        await ctx.report_progress(progress=0, total=100)
        await ensure_allowed_in_free("check_account_blocks_file", ctx)
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            file_base64 = mocks.mock_file_base64()
            
            human_text = f"Файл блокировок счета для ИНН: {inn}\n"
            human_text += "Формат: ZIP (содержит PDF и подпись SIG)\n"
            human_text += "Размер: тестовый файл"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Файл получен (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content={
                    "file_base64": file_base64,
                    "file_type": "zip",
                    "inn": inn
                },
                meta={"mode": "test", "inn": inn}
            )
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                params = {
                    "inn": inn,
                    "key": token
                }
                if bik:
                    params["bik"] = bik
                
                url = "https://api-fns.ru/api/nalogbi_file"
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                # Получаем бинарные данные
                file_data = response.content
                file_base64 = base64.b64encode(file_data).decode('utf-8')
            
            await ctx.report_progress(progress=100, total=100)
            
            human_text = f"Файл блокировок счета для ИНН: {inn}\n"
            human_text += "Формат: ZIP (содержит PDF и подпись SIG)\n"
            human_text += f"Размер: {len(file_data)} байт"
            
            await ctx.info("✅ Файл получен успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content={
                    "file_base64": file_base64,
                    "file_type": "zip",
                    "inn": inn,
                    "size_bytes": len(file_data)
                },
                meta={"mode": "prod", "inn": inn}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось получить файл блокировок счета"))

