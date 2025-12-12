"""Тестовый скрипт для проверки всех tools."""
import asyncio
import os
import sys

if "FNS_MODE" not in os.environ:
    os.environ["FNS_MODE"] = "test"

# Импортируем все tools
from tools import (
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

# Mock Context
class MockContext:
    async def info(self, msg): 
        print(f"INFO: {msg}")
    async def error(self, msg): 
        print(f"ERROR: {msg}")
    async def report_progress(self, progress, total): 
        pass

ctx = MockContext()

async def test_all_tools():
    """Тестирование всех tools."""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ ВСЕХ TOOLS")
    print("=" * 60)
    
    # CHANGE: Прямой вызов функций вместо использования mcp.tools
    # WHY: FastMCP может не иметь атрибута tools, но функции доступны напрямую
    # REF: Упрощение тестирования
    
    tests = [
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
    ]
    
    passed = 0
    failed = 0
    
    for name, tool_func, args in tests:
        try:
            print(f"\n🔍 Тестирование: {name}")
            args["ctx"] = ctx
            # CHANGE: Использование .fn для доступа к исходной функции
            # WHY: @mcp.tool() оборачивает функцию в FunctionTool, исходная функция в атрибуте .fn
            # REF: FastMCP FunctionTool имеет атрибут fn
            if hasattr(tool_func, 'fn'):
                result = await tool_func.fn(**args)
            else:
                result = await tool_func(**args)
            print(f"✅ {name}: OK")
            if result.content:
                text_preview = result.content[0].text[:100] if result.content[0].text else ""
                print(f"   Результат: {text_preview}...")
            passed += 1
        except Exception as e:
            print(f"❌ {name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed} прошло, {failed} провалено")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(test_all_tools())
    sys.exit(0 if success else 1)

