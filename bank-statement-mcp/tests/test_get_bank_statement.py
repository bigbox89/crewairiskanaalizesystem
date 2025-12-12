"""
Unit-тесты для get_bank_statement tool.
"""
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from mcp.shared.exceptions import McpError
from tools.get_bank_statement import get_bank_statement
from tools.utils import ToolResult


@pytest.mark.asyncio
async def test_get_bank_statement_tbank_success():
    """Тест успешного получения выписки из T-Bank."""
    # CHANGE: Мокирование переменных окружения и HTTP запроса
    # WHY: Unit-тесты не должны делать реальные HTTP запросы
    # REF: Стандарт тестирования
    with patch.dict(
        os.environ, {"BANK_PROVIDER": "tbank", "T_BANK_TOKEN": "test_token", "MODE": "prod"}
    ), patch("httpx.AsyncClient") as mock_client:
        # Настройка мока HTTP ответа
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"operations": [{"id": "1", "amount": 1000}]}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Мок Context
        mock_ctx = AsyncMock()

        # Вызов функции
        result = await get_bank_statement.fn(
            from_date="2025-01-01", to_date="2025-01-31", ctx=mock_ctx
        )

        # Проверки
        assert isinstance(result, ToolResult)
        assert result.structured_content["bank"] == "tbank"
        assert len(result.structured_content["operations"]) == 1
        assert result.meta["total_operations"] == 1
        mock_ctx.info.assert_called()
        mock_ctx.report_progress.assert_called()


@pytest.mark.asyncio
async def test_get_bank_statement_invalid_provider():
    """Тест ошибки при неверном BANK_PROVIDER."""
    with patch.dict(os.environ, {"BANK_PROVIDER": "invalid"}):
        mock_ctx = AsyncMock()

        with pytest.raises(McpError) as exc_info:
            await get_bank_statement.fn(
                from_date="2025-01-01", to_date="2025-01-31", ctx=mock_ctx
            )

        assert exc_info.value.error.code == -32602
        assert "BANK_PROVIDER" in exc_info.value.error.message


@pytest.mark.asyncio
async def test_get_bank_statement_missing_token():
    """Тест ошибки при отсутствии токена."""
    with patch.dict(os.environ, {"BANK_PROVIDER": "tbank"}):
        mock_ctx = AsyncMock()

        with pytest.raises(McpError) as exc_info:
            await get_bank_statement.fn(
                from_date="2025-01-01", to_date="2025-01-31", ctx=mock_ctx
            )

        assert exc_info.value.error.code == -32602
        assert "T_BANK_TOKEN" in exc_info.value.error.message


@pytest.mark.asyncio
async def test_get_bank_statement_http_error():
    """Тест обработки HTTP ошибки от банка (Alfa)."""
    with patch.dict(
        os.environ, {"BANK_PROVIDER": "alfa", "ALFA_TOKEN": "test_token", "MODE": "prod"}
    ), patch("httpx.AsyncClient") as mock_client:
        # Настройка мока HTTP ошибки
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        mock_ctx = AsyncMock()

        with pytest.raises(McpError) as exc_info:
            await get_bank_statement.fn(
                from_date="2025-01-01", to_date="2025-01-31", ctx=mock_ctx
            )

        assert exc_info.value.error.code == -32603
        assert "ошибку" in exc_info.value.error.message.lower()


@pytest.mark.asyncio
async def test_get_bank_statement_all_banks_prod_mode():
    """Тест поддержки всех 3 банков в prod режиме."""
    banks = ["tbank", "modulbank", "alfa"]
    tokens = {
        "tbank": "T_BANK_TOKEN",
        "modulbank": "MODULBANK_TOKEN",
        "alfa": "ALFA_TOKEN",
    }

    for bank in banks:
        with patch.dict(
            os.environ,
            {"BANK_PROVIDER": bank, tokens[bank]: f"{bank}_token", "MODE": "prod"},
        ), patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"operations": []}
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value = mock_client_instance

            mock_ctx = AsyncMock()

            result = await get_bank_statement.fn(
                from_date="2025-01-01",
                to_date="2025-01-31",
                account_id="acc-1",
                ctx=mock_ctx,
            )

            assert result.structured_content["bank"] == bank


@pytest.mark.asyncio
async def test_get_bank_statement_provider_override_param():
    """Параметр bank_provider перекрывает env."""
    with patch.dict(
        os.environ, {"BANK_PROVIDER": "tbank", "MODULBANK_TOKEN": "token", "MODE": "test"}
    ), patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "1"}]
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        mock_ctx = AsyncMock()

        result = await get_bank_statement.fn(
            from_date="2025-01-01",
            to_date="2025-01-31",
            account_id="acc-1",
            bank_provider="modulbank",
            ctx=mock_ctx,
        )

        assert result.meta["bank"] == "modulbank"


@pytest.mark.asyncio
async def test_get_bank_statement_with_account_id_tbank():
    """Тест с указанием account_id (T-Bank)."""
    with patch.dict(
        os.environ, {"BANK_PROVIDER": "tbank", "T_BANK_TOKEN": "test_token", "MODE": "prod"}
    ), patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"operations": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        mock_ctx = AsyncMock()

        result = await get_bank_statement.fn(
            from_date="2025-01-01",
            to_date="2025-01-31",
            account_id="12345",
            ctx=mock_ctx,
        )

        # Проверка, что account_id был передан в запрос
        mock_client_instance.get.assert_called_once()
        call_args = mock_client_instance.get.call_args
        assert "accountId" in call_args.kwargs["params"]


@pytest.mark.asyncio
async def test_get_bank_statement_test_mode_uses_mocks():
    """Тест что в test режиме (не modulbank/tbank) возвращаются заглушки без HTTP вызова."""
    with patch.dict(
        os.environ, {"BANK_PROVIDER": "alfa", "ALFA_TOKEN": "test_token", "MODE": "test"}
    ), patch("httpx.AsyncClient") as mock_client:
        mock_ctx = AsyncMock()

        result = await get_bank_statement.fn(
            from_date="2025-01-01",
            to_date="2025-01-02",
            account_id="acc-1",
            ctx=mock_ctx,
        )

        assert result.meta["mode"] == "test"
        mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_get_bank_statement_modulbank_sandbox_calls_api():
    """Тест песочницы Модульбанка: делаем HTTP запрос с sandbox заголовком."""
    with patch.dict(
        os.environ,
        {
            "BANK_PROVIDER": "modulbank",
            "MODULBANK_TOKEN": "ignored_prod_token",
            "MODE": "test",
            "MODULBANK_SANDBOX_TOKEN": "sandboxtoken",
        },
    ), patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "1"}]
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance

        mock_ctx = AsyncMock()

        result = await get_bank_statement.fn(
            from_date="2025-01-01",
            to_date="2025-01-31",
            account_id="acc-1",
            ctx=mock_ctx,
        )

        mock_client_instance.post.assert_called_once()
        called_headers = mock_client_instance.post.call_args.kwargs["headers"]
        assert called_headers["Authorization"].endswith("sandboxtoken")
        assert called_headers["sandbox"] == "on"
        assert called_headers["clientId"] == "sandboxapp"
        assert called_headers["clientSecret"] == "sandboxappsecret"
        assert called_headers["token"] == "sandboxtoken"
        assert result.meta["mode"] == "sandbox"
        assert result.meta["total_operations"] == 1


@pytest.mark.asyncio
async def test_get_bank_statement_modulbank_requires_account_id():
    """Модульбанк требует account_id в песочнице и prod."""
    with patch.dict(
        os.environ,
        {"BANK_PROVIDER": "modulbank", "MODULBANK_TOKEN": "token", "MODE": "test"},
    ):
        mock_ctx = AsyncMock()

        with pytest.raises(McpError) as exc_info:
            await get_bank_statement.fn(
                from_date="2025-01-01",
                to_date="2025-01-31",
                ctx=mock_ctx,
            )

        assert exc_info.value.error.code == -32602


@pytest.mark.asyncio
async def test_get_bank_statement_tbank_sandbox_calls_api():
    """T-Bank в test режиме идёт в sandbox с Bearer TBankSandboxToken."""
    with patch.dict(
        os.environ,
        {
            "BANK_PROVIDER": "tbank",
            "T_BANK_TOKEN": "ignored_prod_token",
            "MODE": "test",
            "T_BANK_SANDBOX_TOKEN": "TBankSandboxToken",
        },
    ), patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"operations": [{"id": "1"}]}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        mock_ctx = AsyncMock()

        result = await get_bank_statement.fn(
            from_date="2025-01-01",
            to_date="2025-01-31",
            account_id="40702810110011000000",
            ctx=mock_ctx,
        )

        mock_client_instance.get.assert_called_once()
        called_headers = mock_client_instance.get.call_args.kwargs["headers"]
        called_params = mock_client_instance.get.call_args.kwargs["params"]
        assert called_headers["Authorization"] == "Bearer TBankSandboxToken"
        assert called_params["accountNumber"] == "40702810110011000000"
        assert called_params["from"].startswith("2025-01-01T")
        assert called_params["to"].startswith("2025-01-31T")
        assert result.meta["mode"] == "sandbox"
        assert result.meta["total_operations"] == 1

