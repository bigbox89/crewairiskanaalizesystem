"""
Универсальный инструмент получения банковской выписки из 3 банков.
Поддерживает T‑Bank (бывш. Тинькофф Бизнес), Модульбанк, Альфа-Банк.
"""
import os
from typing import Dict, List, Optional

import httpx
from fastmcp import Context
from mcp.shared.exceptions import ErrorData, McpError
from mcp.types import TextContent
from opentelemetry import trace
from pydantic import Field

from mcp_instance import mcp
from . import mocks
from .utils import ToolResult, format_error, require_env_vars

tracer = trace.get_tracer(__name__)


class _NoopContext:
    """Контекст-заглушка для случаев, когда ctx не передан."""

    async def info(self, message: str) -> None:
        return None

    async def error(self, message: str) -> None:
        return None

    async def report_progress(self, progress: int, total: int) -> None:
        return None


@mcp.tool(
    name="get_bank_statement",
    description="""Получить выписку операций по расчётному счёту за период.
Поддерживает T‑Bank, Модульбанк, Альфа-Банк.
Пользователь заполняет BANK_PROVIDER и соответствующий *_TOKEN в настройках MCP.""",
)
async def get_bank_statement(
    from_date: str = Field(..., description="Дата начала в формате YYYY-MM-DD"),
    to_date: str = Field(..., description="Дата конца в формате YYYY-MM-DD"),
    account_id: Optional[str] = Field(None, description="ID счёта (опционально, если несколько)"),
    bank_provider: Optional[str] = Field(
        default=None,
        description="Банк для запроса: tbank | modulbank | alfa. Если не указано — используется BANK_PROVIDER из окружения.",
    ),
    ctx: Optional[Context] = None,
) -> ToolResult:
    """
    Возвращает выписку из банка в structured_content.

    Args:
        from_date: Дата начала периода в формате YYYY-MM-DD
        to_date: Дата конца периода в формате YYYY-MM-DD
        account_id: Опциональный ID счёта
        ctx: Context для логирования и прогресса

    Returns:
        ToolResult с content, structured_content и meta

    Raises:
        McpError: При ошибках валидации (-32602) или API (-32603)
    """
    explicit_provider = bank_provider if isinstance(bank_provider, str) else None
    provider_source = explicit_provider or os.getenv("BANK_PROVIDER", "")
    provider = provider_source.lower() if isinstance(provider_source, str) else ""
    if provider not in ["tbank", "modulbank", "alfa"]:
        raise format_error("Укажите BANK_PROVIDER: tbank|modulbank|alfa", code=-32602)

    mode = os.getenv("MODE", "test").lower()
    token_var = "T_BANK_TOKEN" if provider == "tbank" else f"{provider.upper()}_TOKEN"
    if provider == "modulbank" and mode == "test":
        # CHANGE: Для песочницы используем дефолтный sandbox токен без обязательного env
        # WHY: Документация запрещает реальные токены, нужно sandboxtoken
        # QUOTE(TЗ): "Вместо реальных идентификаторов ... sandboxtoken"
        # REF: modulbankv1.json
        token = os.getenv("MODULBANK_SANDBOX_TOKEN", "sandboxtoken")
    else:
        tokens = require_env_vars([token_var])
        token = tokens[token_var]

    safe_ctx = ctx or _NoopContext()

    normalized_account_id = account_id if isinstance(account_id, str) and account_id.strip() else None

    if provider == "modulbank" and not normalized_account_id:
        # CHANGE: Ранний валидатор account_id для Модульбанка
        # WHY: Путь /operation-history/{accountId} без идентификатора возвращает 400, нужно ловить раньше
        # QUOTE(TЗ): "для запроса просмотра истории операций ... accountId обязателен"
        # REF: modulbankv1.json
        raise format_error("Для Модульбанка нужно указать account_id", code=-32602)

    with tracer.start_as_current_span("get_bank_statement") as span:
        span.set_attribute("bank", provider)
        span.set_attribute("from_date", from_date)
        span.set_attribute("to_date", to_date)
        if normalized_account_id:
            span.set_attribute("account_id", normalized_account_id)

        await safe_ctx.info(f"🔍 Запрос выписки из {provider.upper()} за {from_date} — {to_date}")
        await safe_ctx.report_progress(progress=0, total=100)

        if mode == "test" and provider == "tbank":
            operations = await _fetch_tbank_sandbox(
                account_number=normalized_account_id,
                from_date=from_date,
                to_date=to_date,
                ctx=safe_ctx,
            )
            await safe_ctx.report_progress(progress=100, total=100)
            await safe_ctx.info(f"✅ (sandbox TBank) Получено {len(operations)} операций")
            
            # CHANGE: Форматируем реальные операции из sandbox в читаемый вид
            # WHY: Пользователь должен видеть реальные данные из sandbox, а не просто количество
            # QUOTE(TЗ): "а заглушку" - пользователь видит заглушку вместо реальных данных
            # REF: user-message
            human_text = _format_tbank_statement(operations, from_date, to_date, normalized_account_id)
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text)],
                structured_content={
                    "bank": provider,
                    "period": {"from": from_date, "to": to_date},
                    "operations": operations,
                },
                meta={"mode": "sandbox", "total_operations": len(operations), "bank": provider},
            )

        if mode == "test" and provider not in ["modulbank", "tbank"]:
            mock_payload = mocks.get_bank_statement_mock(
                provider=provider,
                from_date=from_date,
                to_date=to_date,
                account_id=normalized_account_id,
            )
            operations = mock_payload.get("operations", [])
            await safe_ctx.report_progress(progress=100, total=100)
            await safe_ctx.info(f"✅ (test) Получено {len(operations)} операций")
            human_text = (
                f"[TEST] Выписка из {provider.upper()} за {from_date}–{to_date}\n"
                f"Операций: {len(operations)}"
            )
            return ToolResult(
                content=[TextContent(type="text", text=human_text)],
                structured_content=mock_payload,
                meta={"mode": "test", "total_operations": len(operations), "bank": provider},
            )

        headers = (
            {"X-API-Key": token} if provider == "alfa" else {"Authorization": f"Bearer {token}"}
        )

        url_map: Dict[str, str] = {
            "tbank": "https://business-api.tinkoff.ru/api/v1/statement",
            "modulbank": "https://api.modulbank.ru/v1",
            "alfa": "https://api.alfabank.ru/statement/v2",
        }

        await safe_ctx.report_progress(progress=50, total=100)
        await safe_ctx.info("📡 Отправка запроса в банк")

        try:
            if provider == "modulbank":
                # CHANGE: В тестовом режиме ходим в sandbox Модульбанка вместо локальных моков
                # WHY: Нужно получать реальные ответы песочницы для проверки совместимости
                # QUOTE(TЗ): "если запрос идет к модульбанку и в режиме тест то нужно отдавать запрос к модульбанку в режиме песочницы"
                # REF: user-message
                operations = await _fetch_modulbank_history(
                    base_url=url_map["modulbank"],
                    token=token,
                    account_id=normalized_account_id,
                    from_date=from_date,
                    to_date=to_date,
                    sandbox=(mode == "test"),
                    ctx=safe_ctx,
                )
            else:
                params: Dict[str, str] = {"from": from_date, "to": to_date}
                if normalized_account_id:
                    params["accountId"] = normalized_account_id

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url_map[provider], headers=headers, params=params)
                    response.raise_for_status()
                    data = response.json()

                operations = (
                    data.get("operations")
                    or data.get("transactions")
                    or data.get("items")
                    or data.get("operations", [])
                )

            await safe_ctx.report_progress(progress=100, total=100)
            await safe_ctx.info(f"✅ Получено {len(operations)} операций")

            human_text = (
                f"Выписка из {provider.upper()} за {from_date}–{to_date}\n"
                f"Операций: {len(operations)}"
            )

            return ToolResult(
                content=[TextContent(type="text", text=human_text)],
                structured_content={
                    "bank": provider,
                    "period": {"from": from_date, "to": to_date},
                    "operations": operations,
                },
                meta={
                    "mode": "sandbox" if mode == "test" and provider == "modulbank" else mode,
                    "total_operations": len(operations),
                    "bank": provider,
                },
            )

        except McpError:
            raise
        except httpx.HTTPStatusError as http_error:
            status_code = http_error.response.status_code if http_error.response else 0
            error_msg = f"Банк вернул ошибку {status_code}"
            await safe_ctx.error(f"❌ {error_msg}")
            raise McpError(ErrorData(code=-32603, message=error_msg)) from http_error
        except Exception as unexpected:
            await safe_ctx.error(f"❌ Неизвестная ошибка: {unexpected}")
            raise McpError(ErrorData(code=-32603, message="Не удалось получить выписку")) from unexpected


async def _fetch_modulbank_history(
    *,
    base_url: str,
    token: str,
    account_id: Optional[str],
    from_date: str,
    to_date: str,
    sandbox: bool,
    ctx: _NoopContext,
) -> List[Dict[str, object]]:
    """
    Выполняет запрос к operation-history Модульбанка с поддержкой песочницы.
    """
    # CHANGE: Жёстко требуем account_id для соответствия спецификации
    # WHY: Endpoint /operation-history/{accountId} требует идентификатор счёта
    # QUOTE(TЗ): "если запрос идет к модульбанку и в режиме тест то нужно отдавать запрос к модульбанку в режиме песочницы"
    # REF: user-message
    if not account_id:
        raise format_error("Для Модульбанка нужно указать account_id", code=-32602)

    sandbox_token = os.getenv("MODULBANK_SANDBOX_TOKEN", "sandboxtoken")
    auth_token = sandbox_token if sandbox else token
    headers: Dict[str, str] = {"Authorization": f"Bearer {auth_token}"}
    if sandbox:
        headers["sandbox"] = "on"
        headers["clientId"] = os.getenv("MODULBANK_SANDBOX_CLIENT_ID", "sandboxapp")
        headers["clientSecret"] = os.getenv("MODULBANK_SANDBOX_CLIENT_SECRET", "sandboxappsecret")
        headers["token"] = auth_token

    payload: Dict[str, object] = {"records": 50, "skip": 0} if sandbox else {
        "from": f"{from_date}T00:00:00",
        "till": f"{to_date}T23:59:59",
    }

    endpoint = f"{base_url}/operation-history/{account_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    if isinstance(data, list):
        operations: List[Dict[str, object]] = data
    else:
        operations = data.get("operations") or data.get("transactions") or []

    await ctx.info("🧪 Модульбанк sandbox ответ получен")
    return operations


def _format_tbank_statement(
    operations: List[Dict[str, object]], from_date: str, to_date: str, account_id: Optional[str]
) -> str:
    """
    Форматирует операции T-Bank в читаемый вид для human_text.
    """
    # CHANGE: Форматирование реальных операций из sandbox
    # WHY: Пользователь должен видеть детали операций, а не просто количество
    # QUOTE(TЗ): "а заглушку" - нужно показывать реальные данные
    # REF: user-message
    from datetime import datetime
    
    lines = [f"Выписка Т‑Банк"]
    lines.append(f"Период: {from_date} – {to_date}")
    if account_id:
        lines.append(f"Счёт: {account_id}")
    lines.append("")
    
    if not operations:
        lines.append("Операций не найдено")
        return "\n".join(lines)
    
    lines.append("Дата\tОписание\tСумма\tОстаток")
    
    total_debit = 0.0
    total_credit = 0.0
    
    for op in operations:
        op_date_str = op.get("operationDate", "")
        if op_date_str:
            try:
                dt = datetime.fromisoformat(op_date_str.replace("Z", "+00:00"))
                date_str = dt.strftime("%d.%m.%Y %H:%M")
            except Exception:
                date_str = op_date_str[:10] if len(op_date_str) >= 10 else op_date_str
        else:
            date_str = "—"
        
        description = op.get("description") or op.get("payPurpose") or "Операция"
        amount = float(op.get("operationAmount", 0))
        op_type = op.get("typeOfOperation", "")
        
        if op_type == "Credit":
            amount_str = f"+{amount:,.2f} ₽"
            total_credit += amount
        else:
            amount_str = f"-{amount:,.2f} ₽"
            total_debit += amount
        
        lines.append(f"{date_str}\t{description}\t{amount_str}\t—")
    
    lines.append("")
    if total_credit > 0:
        lines.append(f"Итого оборот: +{total_credit:,.2f} ₽")
    if total_debit > 0:
        lines.append(f"Итого оборот: -{total_debit:,.2f} ₽")
    
    return "\n".join(lines)


async def _fetch_tbank_sandbox(
    *,
    account_number: Optional[str],
    from_date: str,
    to_date: str,
    ctx: _NoopContext,
) -> List[Dict[str, object]]:
    """
    Запрашивает выписку в песочнице T-Bank.

    Требуется:
    - account_number (используем account_id поля вызова)
    - токен T_BANK_SANDBOX_TOKEN (default TBankSandboxToken)
    """
    if not account_number:
        raise format_error("Для T-Bank sandbox нужно указать account_id (accountNumber)", code=-32602)

    sandbox_token = os.getenv("T_BANK_SANDBOX_TOKEN", "TBankSandboxToken")
    headers = {"Authorization": f"Bearer {sandbox_token}"}
    params = {
        "accountNumber": account_number,
        "from": f"{from_date}T00:00:00.000Z",
        "to": f"{to_date}T23:59:59.999Z",
    }

    url = "https://business.tbank.ru/openapi/sandbox/api/v1/statement"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    operations = data.get("operations") or []
    await ctx.info("🧪 T-Bank sandbox ответ получен")
    return operations

