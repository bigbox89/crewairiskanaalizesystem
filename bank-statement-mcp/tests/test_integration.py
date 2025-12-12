"""
Интеграционные тесты для bank-statement-mcp.
"""
import asyncio
import pytest
import os
from unittest.mock import patch


@pytest.mark.asyncio
async def test_mcp_server_initialization():
    """Тест инициализации MCP-сервера."""
    # CHANGE: Проверка импорта и регистрации tools
    # WHY: Интеграционный тест проверяет, что сервер корректно инициализируется
    # REF: Стандарт тестирования
    from mcp_instance import mcp
    import tools  # noqa: F401

    # Проверка, что mcp экземпляр создан
    assert mcp is not None
    assert mcp.name == "bank-statement-mcp"


@pytest.mark.asyncio
async def test_tool_registration():
    """Тест регистрации tool в MCP."""
    from mcp_instance import mcp
    import tools  # noqa: F401

    # CHANGE: Унифицированная проверка реестра tools с учётом разных API FastMCP
    # WHY: В FastMCP 2.0+ публичного атрибута tools может не быть, используем безопасные источники
    # REF: План обновления FastMCP до 2.0
    registry_attr = getattr(mcp, "tools", None) or getattr(mcp, "_tools", {})
    registry_names = set(registry_attr.keys()) if isinstance(registry_attr, dict) else set()
    if not registry_names and hasattr(mcp, "get_tools"):
        maybe_tools = mcp.get_tools()
        if asyncio.iscoroutine(maybe_tools):
            maybe_tools = await maybe_tools
        registry_names = {
            tool if isinstance(tool, str) else getattr(tool, "name", "")
            for tool in maybe_tools
        }
        registry_names.discard("")

    assert "get_bank_statement" in registry_names


def test_env_options_structure():
    """Тест структуры env_options.json."""
    import json

    with open("env_options.json", "r", encoding="utf-8") as f:
        env_options = json.load(f)

    # Проверка структуры
    assert "rawEnvs" in env_options
    assert "secretEnvs" in env_options
    assert "BANK_PROVIDER" in env_options["rawEnvs"]
    assert "MODULBANK_SANDBOX_TOKEN" in env_options["rawEnvs"]
    assert "T_BANK_TOKEN" in env_options["secretEnvs"]
    assert "MODULBANK_TOKEN" in env_options["secretEnvs"]
    assert "ALFA_TOKEN" in env_options["secretEnvs"]


def test_catalog_yaml_structure():
    """Тест структуры mcp-server-catalog.yaml."""
    import yaml

    with open("mcp-server-catalog.yaml", "r", encoding="utf-8") as f:
        catalog = yaml.safe_load(f)

    # Проверка обязательных полей
    assert catalog["id"] == "bank-statement-mcp"
    assert "tools" in catalog
    assert "rawEnvs" in catalog
    assert "secretEnvs" in catalog
    assert len(catalog["tools"]) == 1
    assert catalog["tools"][0]["name"] == "get_bank_statement"


def test_mcp_tools_json_structure():
    """Тест структуры mcp_tools.json."""
    import json

    with open("mcp_tools.json", "r", encoding="utf-8") as f:
        tools_json = json.load(f)

    # Проверка структуры
    assert "tools" in tools_json
    assert len(tools_json["tools"]) == 1
    assert tools_json["tools"][0]["name"] == "get_bank_statement"
    assert "inputSchema" in tools_json["tools"][0]

