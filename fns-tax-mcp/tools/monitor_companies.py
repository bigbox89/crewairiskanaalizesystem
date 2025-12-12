"""Мониторинг изменений по списку компаний."""

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
    name="monitor_companies",
    description="""Мониторинг изменений по списку компаний.
Поддерживает команды: list (список), add (добавить), del (удалить), chd (проверка изменений), chbo (проверка отчетности).""",
)
async def monitor_companies(
    cmd: str = Field(..., description="Команда: list, add, del, chd, chbo"),
    req: Optional[str] = Field(None, description="ОГРН или ИНН компаний через запятую (для add, del)"),
    dat: Optional[str] = Field(None, description="Дата в формате DD.MM.YYYY или YYYY-MM-DD (для chd)"),
    year: Optional[int] = Field(None, description="Год отчетности (для chbo)"),
    type: Optional[str] = Field(None, description="Фильтр по типу изменений через запятую (для chd)"),
    page: Optional[int] = Field(None, description="Номер страницы (для list)"),
    ctx: Context = None
) -> ToolResult:
    """Мониторинг изменений через API-ФНС."""
    mode = os.getenv("FNS_MODE", "test").lower()
    
    with tracer.start_as_current_span("monitor_companies") as span:
        span.set_attribute("cmd", cmd)
        span.set_attribute("mode", mode)
        
        await ctx.info(f"📋 Начинаем выполнение команды: {cmd}")
        await ctx.report_progress(progress=0, total=100)
        
        if mode == "test":
            await ctx.info("📋 Используем тестовую заглушку")
            
            if cmd == "list":
                mock_data = mocks.mock_mon_list()
                items = mock_data.get("items", [])
                human_text = f"Список компаний на мониторинге: {len(items)}\n\n"
                for item in items[:10]:
                    human_text += f"ОГРН: {item.get('ОГРН', 'N/A')}, ИНН: {item.get('ИНН', 'N/A')}\n"
            elif cmd == "add":
                mock_data = mocks.mock_mon_add()
                items = mock_data.get("items", [])
                human_text = "Результат добавления:\n\n"
                for item in items:
                    human_text += f"ОГРН: {item.get('ОГРН', 'N/A')}\n"
                    human_text += f"Результат: {item.get('Результат', 'N/A')}\n"
            elif cmd == "chd":
                mock_data = mocks.mock_mon_chd()
                items = mock_data.get("items", [])
                human_text = f"Изменения на дату {dat or 'N/A'}:\n\n"
                for item in items:
                    human_text += f"ОГРН: {item.get('ОГРН', 'N/A')}\n"
                    human_text += f"Тип: {item.get('Тип', 'N/A')}\n"
                    human_text += f"Текст: {item.get('Текст', 'N/A')}\n\n"
            else:
                mock_data = {"items": []}
                human_text = f"Команда {cmd} выполнена"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Команда выполнена (тестовый режим)")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=mock_data,
                meta={"mode": "test", "cmd": cmd}
            )
        
        token = os.getenv("FNS_API_TOKEN")
        if not token:
            raise McpError(ErrorData(code=-32602, message="Не указан FNS_API_TOKEN"))
        
        await ctx.report_progress(progress=30, total=100)
        await ctx.info("📤 Отправка запроса в API-ФНС")
        
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                params = {
                    "cmd": cmd,
                    "key": token
                }
                if req:
                    params["req"] = req
                if dat:
                    params["dat"] = dat
                if year:
                    params["year"] = year
                if type:
                    params["type"] = type
                if page:
                    params["page"] = page
                
                url = "https://api-fns.ru/api/mon"
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            await ctx.report_progress(progress=80, total=100)
            
            items = result.get("items", [])
            if cmd == "list":
                human_text = f"Список компаний на мониторинге: {len(items)}\n\n"
                for item in items[:10]:
                    human_text += f"ОГРН: {item.get('ОГРН', 'N/A')}, ИНН: {item.get('ИНН', 'N/A')}\n"
            elif cmd == "add":
                human_text = "Результат добавления:\n\n"
                for item in items:
                    human_text += f"ОГРН: {item.get('ОГРН', 'N/A')}\n"
                    human_text += f"Результат: {item.get('Результат', 'N/A')}\n"
            elif cmd == "chd":
                human_text = f"Изменения на дату {dat or 'N/A'}:\n\n"
                for item in items:
                    human_text += f"ОГРН: {item.get('ОГРН', 'N/A')}\n"
                    human_text += f"Тип: {item.get('Тип', 'N/A')}\n"
                    human_text += f"Текст: {item.get('Текст', 'N/A')}\n\n"
            else:
                human_text = f"Команда {cmd} выполнена"
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Команда выполнена успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text.strip())],
                structured_content=result,
                meta={"mode": "prod", "cmd": cmd}
            )
        
        except httpx.HTTPStatusError as e:
            error_msg = f"API-ФНС вернула ошибку: {e.response.status_code}"
            await ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg))
        except Exception as e:
            await ctx.error(f"❌ Неизвестная ошибка: {e}")
            raise McpError(ErrorData(code=-32603, message="Не удалось выполнить команду мониторинга"))

