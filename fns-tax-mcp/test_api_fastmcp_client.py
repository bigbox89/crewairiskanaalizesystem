"""Скрипт для проверки всех API endpoints через FastMCP Client."""
# CHANGE: Создание скрипта с использованием FastMCP Client
# WHY: FastMCP Client автоматически обрабатывает сессии и SSE формат
# REF: Документация FastMCP 2.0 - использование Client для работы с MCP серверами

import asyncio
import json
from typing import Dict, Any

try:
    from fastmcp import Client
except ImportError:
    print("❌ FastMCP Client не установлен. Установите: pip install fastmcp>=2.0.0")
    exit(1)

BASE_URL = "http://localhost:8080/mcp"

# Тестовые данные для каждого tool
TEST_DATA = {
    "generate_usn_declaration": {
        "inn": "7707083893",
        "period": "Q1",
        "year": 2025,
        "income": 1000000.0,
        "expenses": 0.0,
        "tax_rate": 6
    },
    "generate_osno_declaration": {
        "inn": "7707083893",
        "period": "Q1",
        "year": 2025,
        "income": 2000000.0,
        "expenses": 500000.0,
        "profit": 1500000.0,
        "loss": 0.0,
        "nds": 200000.0
    },
    "generate_nds_declaration": {
        "inn": "7707083893",
        "period": "Q1",
        "year": 2025,
        "turnover": 2000000.0,
        "nds_to_pay": 200000.0,
        "nds_to_refund": 0.0
    },
    "generate_6ndfl_declaration": {
        "inn": "7707083893",
        "period": "Q1",
        "year": 2025,
        "total_income": 5000000.0,
        "total_ndfl": 650000.0,
        "withheld_ndfl": 650000.0
    },
    "search_companies": {
        "q": "Яндекс"
    },
    "autocomplete": {
        "q": "Яндекс"
    },
    "get_company_data": {
        "req": "7707083893"
    },
    "multinfo_companies": {
        "req": "7707083893,7736050003"
    },
    "multcheck_companies": {
        "req": "7707083893,7736050003"
    },
    "check_counterparty": {
        "req": "7707083893"
    },
    "check_account_blocks": {
        "inn": "7707083893"
    },
    "check_account_blocks_file": {
        "inn": "7707083893"
    },
    "track_changes": {
        "req": "7707083893",
        "dat": "2024-01-01"
    },
    "monitor_companies": {
        "cmd": "list"
    },
    "get_extract": {
        "req": "7707083893"
    },
    "get_msp_extract": {
        "req": "7707083893"
    },
    "get_accounting_report": {
        "req": "7707083893"
    },
    "get_accounting_report_file": {
        "req": "7707083893",
        "year": 2023
    },
    "get_inn_by_passport": {
        "fam": "Иванов",
        "nam": "Иван",
        "otch": "Иванович",
        "bdate": "01.01.1990",
        "docno": "1234 567890"
    },
    "check_passport": {
        "docno": "1234 567890"
    },
    "check_passport_info": {
        "docno": "1234 567890"
    },
    "check_person_status": {
        "inn": "123456789012"
    },
    "get_fsrar_licenses": {
        "inn": "7707083893"
    },
    "get_api_statistics": {}
}

async def test_list_tools(client: Client) -> Dict[str, Any]:
    """Проверка tools/list через FastMCP Client."""
    print("\n" + "="*60)
    print("3. Testing tools/list via FastMCP Client")
    print("="*60)
    try:
        tools = await client.list_tools()
        print(f"✅ Tools count: {len(tools)}")
        if tools:
            print(f"✅ First tool: {tools[0].name}")
        return {"status": "ok", "tools_count": len(tools)}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}

async def test_tool_call(client: Client, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Проверка вызова конкретного tool через FastMCP Client."""
    print(f"\n{'='*60}")
    print(f"Testing tool: {tool_name}")
    print(f"{'='*60}")
    try:
        result = await client.call_tool(name=tool_name, arguments=arguments)
        
        # Проверяем результат
        if hasattr(result, 'content') and result.content:
            text_preview = str(result.content[0])[:200] if result.content else "N/A"
            print(f"✅ Status: OK")
            print(f"✅ Content preview: {text_preview}...")
        else:
            print(f"✅ Status: OK (no content)")
        
        return {
            "status": "ok",
            "tool": tool_name,
            "result": str(result)[:200] if result else "N/A"
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "tool": tool_name, "error": str(e)}

async def main():
    """Основная функция для запуска всех тестов."""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК ПРОВЕРКИ ВСЕХ API ENDPOINTS (FastMCP Client)")
    print("="*60)
    
    results = {
        "list_tools": None,
        "tools": {}
    }
    
    # CHANGE: Использование FastMCP Client для автоматической обработки сессий
    # WHY: FastMCP Client автоматически обрабатывает SSE формат и session ID
    client = Client(BASE_URL)
    
    try:
        async with client:
            # 3. List tools
            results["list_tools"] = await test_list_tools(client)
            
            # 4. Test each tool
            print("\n" + "="*60)
            print("4. Testing all tools")
            print("="*60)
            
            for tool_name, arguments in TEST_DATA.items():
                results["tools"][tool_name] = await test_tool_call(client, tool_name, arguments)
                await asyncio.sleep(0.3)  # Небольшая задержка между запросами
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return
    
    # Итоговая статистика
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*60)
    
    print(f"\nList tools: {results['list_tools'].get('status', 'unknown')}")
    
    tools_ok = sum(1 for r in results["tools"].values() if r.get("status") == "ok")
    tools_error = sum(1 for r in results["tools"].values() if r.get("status") == "error")
    
    print(f"\nTools tested: {len(results['tools'])}")
    print(f"✅ OK: {tools_ok}")
    print(f"❌ Error: {tools_error}")
    
    # Сохранение результатов
    with open("api_test_results_client.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 Результаты сохранены в api_test_results_client.json")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())

