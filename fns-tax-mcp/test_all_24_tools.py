"""Тестирование всех 24 tools в режиме заглушек."""

import asyncio
import os
import sys

# Устанавливаем test режим
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

# Mock Context
class MockContext:
    async def info(self, msg): 
        print(f"  INFO: {msg}")
    async def error(self, msg): 
        print(f"  ERROR: {msg}")
    async def report_progress(self, progress, total): 
        pass

ctx = MockContext()

async def test_all_24_tools():
    """Тестирование всех 24 tools в режиме заглушек."""
    print("=" * 80)
    print("🧪 ТЕСТИРОВАНИЕ ВСЕХ 24 TOOLS В РЕЖИМЕ ЗАГЛУШЕК (TEST)")
    print("=" * 80)
    print(f"FNS_MODE: {os.getenv('FNS_MODE')}")
    print()
    
    tests = [
        # Декларации
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
        # API-ФНС методы
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
            print(f"\n{'='*80}")
            print(f"🔍 Тест {passed + failed + 1}/24: {name}")
            args["ctx"] = ctx
            
            if hasattr(tool_func, 'fn'):
                result = await tool_func.fn(**args)
            else:
                result = await tool_func(**args)
            
            if result and result.content:
                text_preview = result.content[0].text[:150] if result.content[0].text else ""
                print(f"✅ {name}: PASSED")
                print(f"   Результат: {text_preview}...")
                
                # Проверяем, что это заглушка (для API методов) или локальная генерация (для деклараций)
                if "тестовый режим" in text_preview.lower() or "заглушка" in text_preview.lower() or "тестов" in text_preview.lower() or "сгенерирована" in text_preview.lower():
                    print(f"   ✓ Успешно выполнено")
                else:
                    print(f"   ⚠️  Возможно не заглушка!")
                
                passed += 1
            else:
                print(f"❌ {name}: FAILED - Нет результата")
                failed += 1
                
        except Exception as e:
            print(f"❌ {name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print(f"   ✅ Успешно: {passed}")
    print(f"   ❌ Провалено: {failed}")
    print(f"   📈 Всего протестировано: {passed + failed}/24")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(test_all_24_tools())
    sys.exit(0 if success else 1)

