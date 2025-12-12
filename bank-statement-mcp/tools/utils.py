"""
Утилиты для tools: ToolResult, обработка ошибок, форматирование.
"""
# CHANGE: Используем dataclass для строгой типизации результата
# WHY: Стандарт Cloud.ru требует формализацию и строгую типизацию
# QUOTE(TЗ): "Код рождается только после доказуемого понимания задачи"
# REF: user-message
from dataclasses import dataclass
from typing import Dict, List

from mcp.shared.exceptions import ErrorData, McpError
from mcp.types import TextContent


@dataclass
class ToolResult:
    """
    Стандартизированный результат выполнения tool.

    Attributes:
        content: Список TextContent для человекочитаемого вывода
        structured_content: JSON-структура для программной обработки
        meta: Метаданные (total_operations, bank, mode)
    """

    content: List[TextContent]
    structured_content: Dict[str, object]
    meta: Dict[str, object]


def format_error(message: str, code: int = -32603) -> McpError:
    """
    Форматирует ошибку в McpError.

    Args:
        message: Текст ошибки
        code: Код ошибки MCP (-32602 для валидации, -32603 для серверных ошибок)

    Returns:
        McpError с указанным кодом и сообщением
    """
    # CHANGE: Единая фабрика ошибок
    # WHY: Единообразная обработка ошибок
    # QUOTE(TЗ): "Обработка ошибок через McpError"
    # REF: user-message
    return McpError(ErrorData(code=code, message=message))


def require_env_vars(var_names: List[str]) -> Dict[str, str]:
    """
    Проверяет наличие обязательных переменных окружения и возвращает их.

    Args:
        var_names: Имена переменных окружения для проверки

    Returns:
        Словарь {name: value}

    Raises:
        McpError: Если хотя бы одна переменная отсутствует
    """
    import os

    missing = [var for var in var_names if not os.getenv(var)]
    if missing:
        raise format_error(
            f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}",
            code=-32602,
        )
    return {var: os.getenv(var, "") for var in var_names}

