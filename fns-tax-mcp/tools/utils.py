"""Общие утилиты для tools."""
from typing import Any, Dict, List, Set
from mcp.types import TextContent
from dataclasses import dataclass
import os
from mcp.shared.exceptions import McpError, ErrorData


@dataclass
class ToolResult:
    """Результат выполнения tool с человекочитаемым и структурированным контентом."""
    
    content: List[TextContent]
    structured_content: Dict[str, Any]
    meta: Dict[str, Any]


def validate_inn(inn: str) -> bool:
    """Валидация ИНН (10 или 12 цифр)."""
    
    if not inn:
        return False
    
    # Убираем пробелы и проверяем, что все символы - цифры
    inn_clean = inn.strip().replace(" ", "")
    if not inn_clean.isdigit():
        return False
    
    # Проверяем длину
    return len(inn_clean) in (10, 12)


def format_tax_amount(amount: float) -> str:
    """Форматирование суммы налога для отображения."""
    
    return f"{amount:,.2f} ₽"


# CHANGE: Добавлена поддержка режима free и централизованного allowlist
# WHY: В free-режиме FNS API доступен ограниченный набор методов; нужно блокировать недоступные
# QUOTE(TЗ): "добавь новый free режим в котором будут вызываться только методы доступные на free ключе"
# REF: user message 2025-12-10
FREE_ALLOWED_TOOLS: Set[str] = {
    # Поиск и базовые проверки
    "search_companies",
    "autocomplete",
    "get_company_data",
    "multinfo_companies",
    "multcheck_companies",
    "check_counterparty",
    "track_changes",
    "monitor_companies",
    # Выписки и отчетность
    "get_extract",
    "get_accounting_report",
    "get_accounting_report_file",
    # Физлица / паспорта / статусы
    "get_inn_by_passport",
    "check_passport",
    "check_passport_info",
    "check_person_status",
    # Лицензии и статистика
    "get_fsrar_licenses",
    "get_api_statistics",
    # Декларации (должны работать в free по требованию)
    "generate_usn_declaration",
    "generate_osno_declaration",
    "generate_nds_declaration",
    "generate_6ndfl_declaration",
}


def get_fns_mode() -> str:
    """Возвращает режим FNS: test | prod | free."""
    return os.getenv("FNS_MODE", "test").lower()


async def ensure_allowed_in_free(tool_name: str, ctx) -> None:
    """
    Блокирует вызов tool в режиме free, если метод не входит в allowlist.
    Возвращает None, но бросает McpError при нарушении.
    """
    mode = get_fns_mode()
    if mode != "free":
        return
    if tool_name in FREE_ALLOWED_TOOLS:
        return
    await ctx.error(f"❌ Метод {tool_name} недоступен в режиме free ключа FNS")
    raise McpError(
        ErrorData(
            code=-32603,
            message=f"Метод {tool_name} недоступен в free режиме FNS ключа",
        )
    )

