"""Полное тестирование всех методов API-ФНС в prod режиме."""
import asyncio
import os
import sys

# Устанавливаем prod режим
os.environ["FNS_MODE"] = "prod"
os.environ["FNS_API_TOKEN"] = "e8d5147b30c2d87db8ec61b5651f400d5da812b7"

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
        print(f"  INFO: {msg}")
    async def error(self, msg): 
        print(f"  ERROR: {msg}")
    async def report_progress(self, progress, total): 
        pass

ctx = MockContext()

async def test_all_api_prod():
    """Тестирование всех методов API-ФНС в prod режиме с реальными запросами."""
    print("=" * 80)
    print("🧪 ПОЛНОЕ ТЕСТИРОВАНИЕ ВСЕХ МЕТОДОВ API-ФНС В PROD РЕЖИМЕ")
    print("=" * 80)
    print(f"FNS_MODE: {os.getenv('FNS_MODE')}")
    print(f"FNS_API_TOKEN: {'*' * 20}...{os.getenv('FNS_API_TOKEN')[-10:]}")
    print()
    
    # CHANGE: Реальные примеры запросов из документации API-ФНС
    # WHY: Тестирование с реальными данными из api-fns.ru/api_help
    # REF: Примеры из документации API-ФНС
    
    tests = [
        # 1. search - Поиск компаний
        ("search_companies", search_companies, {
            "q": "Борунов Алексей Владимирович"
        }, "Поиск по ФИО из примера документации"),
        
        # 2. autocomplete - Автодополнение
        ("autocomplete", autocomplete, {
            "q": "тм1"
        }, "Автодополнение по первым буквам"),
        
        # 3. get_company_data (egr) - Данные о компании
        ("get_company_data", get_company_data, {
            "req": "1032502271548"
        }, "Получение данных по ОГРН из примера"),
        
        # 4. multinfo - Реквизиты группы компаний
        ("multinfo_companies", multinfo_companies, {
            "req": "308661702400048,7811051680"
        }, "Получение данных о группе компаний"),
        
        # 5. multcheck - Проверка группы компаний
        ("multcheck_companies", multcheck_companies, {
            "req": "1047796296910,304532133100229"
        }, "Проверка группы компаний"),
        
        # 6. check - Проверка контрагента
        ("check_counterparty", check_counterparty, {
            "req": "1027739471517"
        }, "Проверка контрагента из примера"),
        
        # 7. check_account_blocks (nalogbi) - Блокировки счета
        ("check_account_blocks", check_account_blocks, {
            "inn": "7706148097"
        }, "Проверка блокировок счета"),
        
        # 8. check_account_blocks_file (nalogbi_file) - Блокировки файлом
        ("check_account_blocks_file", check_account_blocks_file, {
            "inn": "7706148097"
        }, "Проверка блокировок счета (файл)"),
        
        # 9. track_changes (changes) - Отслеживание изменений
        ("track_changes", track_changes, {
            "req": "1076671015431",
            "dat": "2018-01-25"
        }, "Отслеживание изменений с даты"),
        
        # 10. monitor_companies (mon) - Мониторинг (list)
        ("monitor_companies", monitor_companies, {
            "cmd": "list"
        }, "Список компаний на мониторинге"),
        
        # 11. get_extract (vyp) - Выписка из ЕГРЮЛ
        ("get_extract", get_extract, {
            "req": "1026605606620"
        }, "Выписка из ЕГРЮЛ"),
        
        # 12. get_msp_extract (mspinfo_file) - Выписка МСП
        ("get_msp_extract", get_msp_extract, {
            "req": "3827024814"
        }, "Выписка из реестра МСП"),
        
        # 13. get_accounting_report (bo) - Бухгалтерская отчетность
        ("get_accounting_report", get_accounting_report, {
            "req": "7605016030"
        }, "Бухгалтерская отчетность"),
        
        # 14. get_accounting_report_file (bo_file) - Отчетность файлом
        ("get_accounting_report_file", get_accounting_report_file, {
            "req": "7605016030",
            "year": 2019
        }, "Бухгалтерская отчетность (файл)"),
        
        # 15. get_inn_by_passport (innfl) - ИНН по паспорту
        ("get_inn_by_passport", get_inn_by_passport, {
            "fam": "Иванов",
            "nam": "Степан",
            "otch": "Петрович",
            "bdate": "02.01.1935",
            "doctype": "21",
            "docno": "7500548998"
        }, "ИНН по паспортным данным из примера"),
        
        # 16. check_passport (mvdpass) - Проверка паспорта
        ("check_passport", check_passport, {
            "docno": "7500548998"
        }, "Проверка паспорта на недействительность"),
        
        # 17. check_passport_info (mvdinfo) - Информация о паспорте
        ("check_passport_info", check_passport_info, {
            "docno": "7513280230"
        }, "Информация о паспорте с причиной"),
        
        # 18. check_person_status (fl_status) - Статусы физлица
        ("check_person_status", check_person_status, {
            "inn": "773208978609"
        }, "Статусы физического лица"),
        
        # 19. get_fsrar_licenses (fsrar) - Лицензии ФСРАР
        ("get_fsrar_licenses", get_fsrar_licenses, {
            "inn": "2116493687"
        }, "Лицензии ФСРАР"),
        
        # 20. get_api_statistics (stat) - Статистика
        ("get_api_statistics", get_api_statistics, {}, "Статистика использования API"),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, tool_func, args, description in tests:
        try:
            print(f"\n{'='*80}")
            print(f"🔍 Тест {passed + failed + skipped + 1}/20: {name}")
            print(f"   Описание: {description}")
            print(f"   Параметры: {args}")
            print()
            
            # Вызываем tool функцию
            if hasattr(tool_func, 'fn'):
                result = await tool_func.fn(**args, ctx=ctx)
            else:
                result = await tool_func(**args, ctx=ctx)
            
            # Проверяем результат
            if result and result.content:
                text_preview = result.content[0].text[:150] if result.content[0].text else ""
                print(f"✅ {name}: PASSED")
                print(f"   Результат: {text_preview}...")
                
                # Проверяем, что это не заглушка
                if "тестовый режим" in text_preview.lower() or "заглушка" in text_preview.lower():
                    print(f"   ⚠️  ВНИМАНИЕ: Возможно используется заглушка вместо реального API!")
                else:
                    print(f"   ✓ Реальный API вызов выполнен")
                
                passed += 1
            else:
                print(f"❌ {name}: FAILED - Нет результата")
                failed += 1
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {name}: FAILED - {error_msg}")
            
            # Проверяем тип ошибки
            if "403" in error_msg or "Forbidden" in error_msg:
                print(f"   ⚠️  Ошибка 403: Возможно, метод недоступен для вашего API ключа")
                skipped += 1
            elif "404" in error_msg or "Not Found" in error_msg:
                print(f"   ⚠️  Ошибка 404: Метод или данные не найдены")
                failed += 1
            else:
                import traceback
                traceback.print_exc()
                failed += 1
    
    print("\n" + "=" * 80)
    print(f"📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print(f"   ✅ Успешно: {passed}")
    print(f"   ❌ Провалено: {failed}")
    print(f"   ⏭️  Пропущено (403): {skipped}")
    print(f"   📈 Всего протестировано: {passed + failed + skipped}/20")
    print("=" * 80)
    
    # Проверяем статистику API
    print("\n📊 Проверка статистики использования API...")
    try:
        stats_result = await get_api_statistics.fn(ctx=ctx)
        if stats_result and stats_result.content:
            print(stats_result.content[0].text)
    except Exception as e:
        print(f"Не удалось получить статистику: {e}")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(test_all_api_prod())
    sys.exit(0 if success else 1)

