"""
Единый экземпляр FastMCP для bank-statement-mcp.
Соответствует стандарту Cloud.ru: один экземпляр на весь сервер.
"""
from fastmcp import FastMCP

# CHANGE: Создание единого экземпляра FastMCP
# WHY: Стандарт Cloud.ru требует единый экземпляр в mcp_instance.py
# QUOTE(TЗ): "Единый экземпляр FastMCP в mcp_instance.py"
# REF: ТЗ раздел 3, стандарт Cloud.ru
mcp = FastMCP("bank-statement-mcp")

