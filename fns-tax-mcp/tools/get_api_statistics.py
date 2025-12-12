"""Получение статистики использования API ключа."""

import os
from fastmcp import Context
from mcp.types import TextContent
from opentelemetry import trace
from mcp_instance import mcp
from .utils import ToolResult
from mcp.shared.exceptions import McpError, ErrorData
import httpx
from . import mocks

tracer = trace.get_tracer(__name__)


@mcp.tool(
    name="get_api_statistics",
    description="""Получение статистики использования API ключа.
Возвращает информацию о количестве использованных и доступных запросов по каждому методу.""",
)
async def get_api_statistics(
    ctx: Context = None
) -> ToolResult:
    """Получение статистики через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("get_api_statistics") as span:
        span.set_attribute("mode", mode)
        
        await ctx.info("📊 Начинаем получение статистики")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            mock_data = mocks.mock_stat()
            
            human_text = f"Статистика использования API:\n\n"
            human_text += f"Период: {mock_data.get('ДатаНач', 'N/A')} - {mock_data.get('ДатаОконч', 'N/A')}\n"
            human_text += f"Статус: {mock_data.get('Статус', 'N/A')}\n\n"
            human_text += "Методы:\n"
            
            metody = mock_data.get("Методы", {})
            for method_name, method_data in metody.items():
                limit = method_data.get("Лимит", "N/A")
                used = method_data.get("Истрачено", "N/A")
                human_text += f"  {method_name}: использовано {used} из {limit}\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Статистика получена (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test"}
            )
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                params = {
                    "key": token
                }
                
                url = "https://api-fns.ru/api/stat"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            human_text = f"Статистика использования API:\n\n"
            human_text += f"Период: {result.get('ДатаНач', 'N/A')} - {result.get('ДатаОконч', 'N/A')}\n"
            human_text += f"Статус: {result.get('Статус', 'N/A')}\n\n"
            human_text += "Методы:\n"
            
            metody = result.get("Методы", {})
            for method_name, method_data in metody.items():
                limit = method_data.get("Лимит", "N/A")
                used = method_data.get("Истрачено", "N/A")
                human_text += f"  {method_name}: использовано {used} из {limit}\n"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Статистика получена успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod"}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось получить статистику"))

