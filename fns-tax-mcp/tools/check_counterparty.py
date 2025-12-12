"""Проверка контрагента на признаки недобросовестности."""

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
    name="check_counterparty",
    description="""Проверка контрагента на признаки недобросовестности.
Возвращает аналитическую информацию: негативные и позитивные факторы, наличие в реестрах ФНС,
отметки о недостоверных данных, признаки массового директора/учредителя и т.д.""",
)
async def check_counterparty(
    req: str = Field(..., description="ОГРН или ИНН компании (юридического лица или ИП)"),
    ctx: Context = None
) -> ToolResult:
    """Проверка контрагента через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("check_counterparty") as span:
        span.set_attribute("req", req)
        span.set_attribute("mode", mode)
        
        await ctx.info("🔍 Начинаем проверку контрагента")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_check()
            
            items = mock_data.get("items", [])
            if items:
                item = items[0]
                human_text = "Результаты проверки контрагента:\n\n"
                
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, ОГРН: {ul.get('ОГРН', 'N/A')}\n\n"
                    
                    pozitiv = ul.get("Позитив", {})
                    negativ = ul.get("Негатив", {})
                    
                    if pozitiv:
                        human_text += "✅ Позитивные факторы:\n"
                        for key, value in pozitiv.items():
                            human_text += f"  - {key}: {value}\n"
                    
                    if negativ:
                        human_text += "\n❌ Негативные факторы:\n"
                        for key, value in negativ.items():
                            human_text += f"  - {key}: {value}\n"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text += f"ИНН: {ip.get('ИННФЛ', 'N/A')}, ОГРН: {ip.get('ОГРНИП', 'N/A')}\n\n"
                    
                    pozitiv = ip.get("Позитив", {})
                    negativ = ip.get("Негатив", {})
                    
                    if pozitiv:
                        human_text += "✅ Позитивные факторы:\n"
                        for key, value in pozitiv.items():
                            human_text += f"  - {key}: {value}\n"
                    
                    if negativ:
                        human_text += "\n❌ Негативные факторы:\n"
                        for key, value in negativ.items():
                            human_text += f"  - {key}: {value}\n"
            else:
                human_text = "Данные не найдены"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Проверка завершена (тестовый режим)")
            
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
                
                url = "https://api-fns.ru/api/check"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            items = result.get("items", [])
            if items:
                item = items[0]
                human_text = "Результаты проверки контрагента:\n\n"
                
                if "ЮЛ" in item:
                    ul = item["ЮЛ"]
                    human_text += f"ИНН: {ul.get('ИНН', 'N/A')}, ОГРН: {ul.get('ОГРН', 'N/A')}\n\n"
                    
                    pozitiv = ul.get("Позитив", {})
                    negativ = ul.get("Негатив", {})
                    
                    if pozitiv:
                        human_text += "✅ Позитивные факторы:\n"
                        for key, value in pozitiv.items():
                            human_text += f"  - {key}: {value}\n"
                    
                    if negativ:
                        human_text += "\n❌ Негативные факторы:\n"
                        for key, value in negativ.items():
                            human_text += f"  - {key}: {value}\n"
                elif "ИП" in item:
                    ip = item["ИП"]
                    human_text += f"ИНН: {ip.get('ИННФЛ', 'N/A')}, ОГРН: {ip.get('ОГРНИП', 'N/A')}\n\n"
                    
                    pozitiv = ip.get("Позитив", {})
                    negativ = ip.get("Негатив", {})
                    
                    if pozitiv:
                        human_text += "✅ Позитивные факторы:\n"
                        for key, value in pozitiv.items():
                            human_text += f"  - {key}: {value}\n"
                    
                    if negativ:
                        human_text += "\n❌ Негативные факторы:\n"
                        for key, value in negativ.items():
                            human_text += f"  - {key}: {value}\n"
            else:
                human_text = "Данные не найдены"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Проверка завершена успешно")
            
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
            raise McpError(ErrorData(code=-32603, message="Не удалось проверить контрагента"))

