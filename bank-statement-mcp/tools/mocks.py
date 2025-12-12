"""Заглушки для test режима bank-statement-mcp."""
# CHANGE: Заглушки операций для трёх банков
# WHY: Тестовый режим должен возвращать реалистичные данные без реальных API
# QUOTE(TЗ): "test: возвращаем заглушки (реалистичные примеры из публичных доков)"
# REF: План, раздел Технические детали
from typing import Dict, List, Optional
from datetime import datetime, timezone


def _operation(
    *,
    op_id: str,
    amount: float,
    currency: str,
    description: str,
    dt: str,
    account_id: str,
    balance_after: Optional[float] = None,
) -> Dict[str, object]:
    """Формирует типовую операцию."""
    return {
        "id": op_id,
        "date": dt,
        "amount": amount,
        "currency": currency,
        "description": description,
        "accountId": account_id,
        "balanceAfter": balance_after,
    }


def get_bank_statement_mock(
    provider: str, from_date: str, to_date: str, account_id: Optional[str]
) -> Dict[str, object]:
    """Возвращает набор операций для тестового режима."""
    # CHANGE: Разные примеры под каждый банк
    # WHY: Приблизиться к реальным полям публичных API
    account = account_id or "test-account-001"
    date_range = f"{from_date}..{to_date}"
    if provider == "tbank":
        operations: List[Dict[str, Any]] = [
            _operation(
                op_id="tb-1",
                amount=15000.0,
                currency="RUB",
                description="Поступление от ООО Альфа",
                dt=f"{from_date}T10:00:00Z",
                account_id=account,
                balance_after=115000.0,
            ),
            _operation(
                op_id="tb-2",
                amount=-3200.5,
                currency="RUB",
                description="Оплата поставщику",
                dt=f"{to_date}T15:30:00Z",
                account_id=account,
                balance_after=111799.5,
            ),
        ]
    elif provider == "modulbank":
        operations = [
            _operation(
                op_id="mb-1",
                amount=50250.75,
                currency="RUB",
                description="Зачисление по счету",
                dt=f"{from_date}T09:15:00Z",
                account_id=account,
            ),
            _operation(
                op_id="mb-2",
                amount=-12500.0,
                currency="RUB",
                description="Выплата контрагенту",
                dt=f"{to_date}T18:45:00Z",
                account_id=account,
            ),
        ]
    else:
        operations = [
            _operation(
                op_id="alfa-1",
                amount=8800.0,
                currency="RUB",
                description="Зачисление клиент",
                dt=f"{from_date}T12:00:00Z",
                account_id=account,
            ),
            _operation(
                op_id="alfa-2",
                amount=-2100.0,
                currency="RUB",
                description="Комиссия банка",
                dt=f"{to_date}T16:10:00Z",
                account_id=account,
            ),
        ]

    return {
        "bank": provider,
        "period": {"from": from_date, "to": to_date},
        "accountId": account,
        "operations": operations,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "test",
        "dateRange": date_range,
    }

