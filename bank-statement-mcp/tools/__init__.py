"""
Tools для bank-statement-mcp.
Экспорт всех tools для регистрации в MCP-сервере.
"""
# CHANGE: Импорт tool для автоматической регистрации
# WHY: FastMCP автоматически регистрирует декорированные функции при импорте
# REF: Стандарт Cloud.ru
from .get_bank_statement import get_bank_statement  # noqa: F401

__all__ = ["get_bank_statement"]

