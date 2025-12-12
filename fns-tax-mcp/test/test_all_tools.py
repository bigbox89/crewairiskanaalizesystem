"""API тесты для всех 24 tools в режиме test."""

import os
import pytest
from fastmcp import Context

# Устанавливаем test режим перед импортом tools
os.environ["FNS_MODE"] = "test"

# Импортируем все tools
from tools import (
    generate_usn_declaration,
    generate_osno_declaration,
    generate_nds_declaration,
    generate_6ndfl_declaration,
    search_companies,
    autocomplete,
    get_company_data,
    multinfo_companies,
    multcheck_companies,
    check_counterparty,
    check_account_blocks,
    check_account_blocks_file,
    track_changes,
    monitor_companies,
    get_extract,
    get_msp_extract,
    get_accounting_report,
    get_accounting_report_file,
    get_inn_by_passport,
    check_passport,
    check_passport_info,
    check_person_status,
    get_fsrar_licenses,
    get_api_statistics,
)


class MockContext:
    """Mock контекст для тестирования tools."""
    async def info(self, msg):
        pass
    
    async def error(self, msg):
        pass
    
    async def report_progress(self, progress, total):
        pass


@pytest.fixture
def ctx():
    """Фикстура для MockContext."""
    return MockContext()


# Тесты для генерации деклараций
@pytest.mark.asyncio
async def test_generate_usn_declaration(ctx):
    """Тест генерации декларации УСН."""
    result = await generate_usn_declaration.fn(
        inn="7707083893",
        period="Q1",
        year=2025,
        income=1000000.0,
        expenses=0.0,
        tax_rate=6,
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None
    assert len(result.content) > 0
    assert "УСН" in result.content[0].text
    assert "7707083893" in result.content[0].text
    assert result.structured_content["status"] == "generated"
    assert "declaration_xml" in result.structured_content


@pytest.mark.asyncio
async def test_generate_osno_declaration(ctx):
    """Тест генерации декларации ОСНО."""
    result = await generate_osno_declaration.fn(
        inn="7707083893",
        period="Q1",
        year=2025,
        income=1000000.0,
        expenses=500000.0,
        profit=500000.0,
        loss=0.0,
        nds=100000.0,
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None
    assert len(result.content) > 0
    assert "ОСНО" in result.content[0].text
    assert result.structured_content["status"] == "generated"
    assert "declaration_xml" in result.structured_content


@pytest.mark.asyncio
async def test_generate_nds_declaration(ctx):
    """Тест генерации декларации НДС."""
    result = await generate_nds_declaration.fn(
        inn="7707083893",
        period="Q1",
        year=2025,
        nds_to_pay=200000.0,
        nds_to_refund=0.0,
        turnover=2000000.0,
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None
    assert len(result.content) > 0
    assert "НДС" in result.content[0].text
    assert result.structured_content["status"] == "generated"
    assert "declaration_xml" in result.structured_content


@pytest.mark.asyncio
async def test_generate_6ndfl_declaration(ctx):
    """Тест генерации формы 6-НДФЛ."""
    result = await generate_6ndfl_declaration.fn(
        inn="7707083893",
        period="Q1",
        year=2025,
        total_income=5000000.0,
        total_ndfl=650000.0,
        withheld_ndfl=650000.0,
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None
    assert len(result.content) > 0
    assert "6-НДФЛ" in result.content[0].text
    assert result.structured_content["status"] == "generated"
    assert "declaration_xml" in result.structured_content


# Тесты для API-ФНС методов
@pytest.mark.asyncio
async def test_search_companies(ctx):
    """Тест поиска компаний."""
    result = await search_companies.fn(
        q="Борунов Алексей Владимирович",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_autocomplete(ctx):
    """Тест автодополнения."""
    result = await autocomplete.fn(
        q="тм1",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_get_company_data(ctx):
    """Тест получения данных о компании."""
    result = await get_company_data.fn(
        req="1032502271548",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_multinfo_companies(ctx):
    """Тест получения данных о нескольких компаниях."""
    result = await multinfo_companies.fn(
        req="308661702400048,7811051680",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_multcheck_companies(ctx):
    """Тест проверки нескольких компаний."""
    result = await multcheck_companies.fn(
        req="1047796296910,304532133100229",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_check_counterparty(ctx):
    """Тест проверки контрагента."""
    result = await check_counterparty.fn(
        req="1027739471517",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_check_account_blocks(ctx):
    """Тест проверки блокировок счета."""
    result = await check_account_blocks.fn(
        inn="7706148097",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_check_account_blocks_file(ctx):
    """Тест проверки блокировок счета в виде файла."""
    result = await check_account_blocks_file.fn(
        inn="7706148097",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_track_changes(ctx):
    """Тест отслеживания изменений."""
    result = await track_changes.fn(
        req="1076671015431",
        dat="2018-01-25",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_monitor_companies(ctx):
    """Тест мониторинга компаний."""
    result = await monitor_companies.fn(
        cmd="list",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_get_extract(ctx):
    """Тест получения выписки."""
    result = await get_extract.fn(
        req="1026605606620",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_get_msp_extract(ctx):
    """Тест получения выписки МСП."""
    result = await get_msp_extract.fn(
        req="3827024814",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_get_accounting_report(ctx):
    """Тест получения бухгалтерской отчетности."""
    result = await get_accounting_report.fn(
        req="7605016030",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_get_accounting_report_file(ctx):
    """Тест получения бухгалтерской отчетности в виде файла."""
    result = await get_accounting_report_file.fn(
        req="7605016030",
        year=2019,
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_get_inn_by_passport(ctx):
    """Тест получения ИНН по паспорту."""
    result = await get_inn_by_passport.fn(
        fam="Иванов",
        nam="Степан",
        otch="Петрович",
        bdate="02.01.1935",
        doctype="21",
        docno="7500548998",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_check_passport(ctx):
    """Тест проверки паспорта."""
    result = await check_passport.fn(
        docno="7500548998",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_check_passport_info(ctx):
    """Тест получения информации о паспорте."""
    result = await check_passport_info.fn(
        docno="7513280230",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_check_person_status(ctx):
    """Тест проверки статуса физического лица."""
    result = await check_person_status.fn(
        inn="773208978609",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_get_fsrar_licenses(ctx):
    """Тест получения лицензий ФСРАР."""
    result = await get_fsrar_licenses.fn(
        inn="2116493687",
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_get_api_statistics(ctx):
    """Тест получения статистики API."""
    result = await get_api_statistics.fn(
        ctx=ctx
    )
    assert result is not None
    assert result.content is not None


# Параметризованный тест для проверки всех tools
@pytest.mark.parametrize("tool_name,tool_func,args", [
    ("generate_usn_declaration", generate_usn_declaration, {
        "inn": "7707083893",
        "period": "Q1",
        "year": 2025,
        "income": 1000000.0,
        "expenses": 0.0,
        "tax_rate": 6
    }),
    ("generate_osno_declaration", generate_osno_declaration, {
        "inn": "7707083893",
        "period": "Q1",
        "year": 2025,
        "income": 1000000.0,
        "expenses": 500000.0,
        "profit": 500000.0,
        "loss": 0.0,
        "nds": 100000.0
    }),
    ("generate_nds_declaration", generate_nds_declaration, {
        "inn": "7707083893",
        "period": "Q1",
        "year": 2025,
        "turnover": 2000000.0,
        "nds_to_pay": 200000.0,
        "nds_to_refund": 0.0
    }),
    ("generate_6ndfl_declaration", generate_6ndfl_declaration, {
        "inn": "7707083893",
        "period": "Q1",
        "year": 2025,
        "total_income": 5000000.0,
        "total_ndfl": 650000.0,
        "withheld_ndfl": 650000.0
    }),
    ("search_companies", search_companies, {"q": "Борунов Алексей Владимирович"}),
    ("autocomplete", autocomplete, {"q": "тм1"}),
    ("get_company_data", get_company_data, {"req": "1032502271548"}),
    ("multinfo_companies", multinfo_companies, {"req": "308661702400048,7811051680"}),
    ("multcheck_companies", multcheck_companies, {"req": "1047796296910,304532133100229"}),
    ("check_counterparty", check_counterparty, {"req": "1027739471517"}),
    ("check_account_blocks", check_account_blocks, {"inn": "7706148097"}),
    ("check_account_blocks_file", check_account_blocks_file, {"inn": "7706148097"}),
    ("track_changes", track_changes, {"req": "1076671015431", "dat": "2018-01-25"}),
    ("monitor_companies", monitor_companies, {"cmd": "list"}),
    ("get_extract", get_extract, {"req": "1026605606620"}),
    ("get_msp_extract", get_msp_extract, {"req": "3827024814"}),
    ("get_accounting_report", get_accounting_report, {"req": "7605016030"}),
    ("get_accounting_report_file", get_accounting_report_file, {"req": "7605016030", "year": 2019}),
    ("get_inn_by_passport", get_inn_by_passport, {
        "fam": "Иванов", "nam": "Степан", "otch": "Петрович",
        "bdate": "02.01.1935", "doctype": "21", "docno": "7500548998"
    }),
    ("check_passport", check_passport, {"docno": "7500548998"}),
    ("check_passport_info", check_passport_info, {"docno": "7513280230"}),
    ("check_person_status", check_person_status, {"inn": "773208978609"}),
    ("get_fsrar_licenses", get_fsrar_licenses, {"inn": "2116493687"}),
    ("get_api_statistics", get_api_statistics, {}),
])
@pytest.mark.asyncio
async def test_all_tools_integration(tool_name, tool_func, args, ctx):
    """Интеграционный тест для всех tools."""
    
    args["ctx"] = ctx
    
    # Вызываем tool
    if hasattr(tool_func, 'fn'):
        result = await tool_func.fn(**args)
    else:
        result = await tool_func(**args)
    
    # Проверяем результат
    assert result is not None, f"{tool_name}: результат не должен быть None"
    assert result.content is not None, f"{tool_name}: content не должен быть None"
    assert len(result.content) > 0, f"{tool_name}: content не должен быть пустым"
    assert result.structured_content is not None, f"{tool_name}: structured_content не должен быть None"
    assert result.meta is not None, f"{tool_name}: meta не должен быть None"

