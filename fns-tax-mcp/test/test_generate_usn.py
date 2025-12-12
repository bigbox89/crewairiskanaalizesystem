"""Тесты для generate_usn_declaration."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.generate_usn_declaration import generate_usn_declaration
from tools.utils import ToolResult
from mcp.shared.exceptions import McpError
from fastmcp import Context


@pytest.mark.asyncio
async def test_generate_usn_declaration_success():
    """Тест успешной генерации УСН декларации."""
    ctx = MagicMock(spec=Context)
    ctx.info = AsyncMock()
    ctx.report_progress = AsyncMock()
    ctx.error = AsyncMock()
    
    result = await generate_usn_declaration.fn(
        inn="123456789012",
        period="Q1",
        year=2025,
        income=500000.0,
        expenses=0.0,
        tax_rate=6,
        ctx=ctx
    )
    
    assert isinstance(result, ToolResult)
    assert result.structured_content["inn"] == "123456789012"
    assert result.structured_content["tax_rate"] == 6
    assert result.structured_content["tax_amount"] == 30000.0
    assert result.structured_content["status"] == "generated"
    assert "declaration_xml" in result.structured_content


@pytest.mark.asyncio
async def test_generate_usn_declaration_invalid_inn():
    """Тест валидации ИНН."""
    ctx = MagicMock(spec=Context)
    
    with pytest.raises(McpError) as exc_info:
        await generate_usn_declaration.fn(
            inn="invalid",
            period="Q1",
            year=2025,
            income=500000.0,
            expenses=0.0,
            tax_rate=6,
            ctx=ctx
        )
    
    assert "ИНН должен содержать" in str(exc_info.value)

