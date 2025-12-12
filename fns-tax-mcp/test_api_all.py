"""Скрипт для проверки всех API endpoints MCP сервера."""
# CHANGE: Создание скрипта для проверки всех API endpoints
# WHY: Автоматическая проверка работоспособности всех endpoints
# REF: Требование пользователя проверить все запросы по API

import json
import asyncio
import httpx
from typing import Dict, Any, List

BASE_URL = "http://localhost:8080"

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
        "inn": "7707083893"
    },
    "multinfo_companies": {
        "inns": "7707083893,7736050003"
    },
    "multcheck_companies": {
        "inns": "7707083893,7736050003"
    },
    "check_counterparty": {
        "inn": "7707083893"
    },
    "check_account_blocks": {
        "inn": "7707083893"
    },
    "check_account_blocks_file": {
        "inn": "7707083893"
    },
    "track_changes": {
        "inn": "7707083893",
        "date": "2024-01-01"
    },
    "monitor_companies": {
        "command": "list"
    },
    "get_extract": {
        "inn": "7707083893",
        "ogrn": None
    },
    "get_msp_extract": {
        "inn": "7707083893"
    },
    "get_accounting_report": {
        "inn": "7707083893",
        "year": 2023
    },
    "get_accounting_report_file": {
        "inn": "7707083893",
        "year": 2023
    },
    "get_inn_by_passport": {
        "surname": "Иванов",
        "name": "Иван",
        "patronymic": "Иванович",
        "birthdate": "1990-01-01",
        "passport_series": "1234",
        "passport_number": "567890"
    },
    "check_passport": {
        "passport_series": "1234",
        "passport_number": "567890"
    },
    "check_passport_info": {
        "passport_series": "1234",
        "passport_number": "567890"
    },
    "check_person_status": {
        "inn": "123456789012"
    },
    "get_fsrar_licenses": {
        "inn": "7707083893"
    },
    "get_api_statistics": {}
}

async def test_health(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Проверка health endpoint."""
    print("\n" + "="*60)
    print("1. Testing GET /health")
    print("="*60)
    try:
        response = await client.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return {"status": "ok", "response": data}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}

async def test_root(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Проверка root endpoint."""
    print("\n" + "="*60)
    print("2. Testing GET /")
    print("="*60)
    try:
        response = await client.get(f"{BASE_URL}/")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Service: {data.get('service')}")
        print(f"✅ Tools count: {len(data.get('tools', []))}")
        print(f"✅ Tools: {', '.join(data.get('tools', [])[:5])}...")
        return {"status": "ok", "response": data}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}

async def test_list_tools(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Проверка tools/list."""
    print("\n" + "="*60)
    print("3b. Testing POST /mcp (tools/list)")
    print("="*60)
    try:
        request_body = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        # CHANGE: Убрана работа с session ID - FastMCP 2.0 обрабатывает это автоматически
        # WHY: FastMCP 2.0 с streamable-http транспортом автоматически управляет сессиями
        response = await client.post(
            f"{BASE_URL}/mcp",
            json=request_body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        )
        response.raise_for_status()
        data = response.json()
        tools = data.get("result", {}).get("tools", [])
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Tools count: {len(tools)}")
        print(f"✅ First tool: {tools[0].get('name') if tools else 'N/A'}")
        return {"status": "ok", "tools_count": len(tools), "response": data}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}

async def test_tool_call(client: httpx.AsyncClient, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Проверка вызова конкретного tool."""
    print(f"\n{'='*60}")
    print(f"Testing tool: {tool_name}")
    print(f"{'='*60}")
    try:
        request_body = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 2,
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        # CHANGE: Убрана работа с session ID - FastMCP 2.0 обрабатывает это автоматически
        response = await client.post(
            f"{BASE_URL}/mcp",
            json=request_body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            print(f"⚠️  Status: {response.status_code}")
            print(f"⚠️  Error: {data.get('error', {}).get('message', 'Unknown error')}")
            return {"status": "error", "tool": tool_name, "error": data.get("error")}
        else:
            result = data.get("result", {})
            content = result.get("content", [])
            is_error = result.get("isError", False)
            
            if is_error:
                print(f"⚠️  Status: {response.status_code} (tool returned error)")
                print(f"⚠️  Content: {content[0].get('text', '')[:200] if content else 'N/A'}...")
            else:
                print(f"✅ Status: {response.status_code}")
                text_preview = content[0].get("text", "")[:200] if content else "N/A"
                print(f"✅ Content preview: {text_preview}...")
            
            return {
                "status": "ok" if not is_error else "tool_error",
                "tool": tool_name,
                "is_error": is_error,
                "response": data
            }
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"❌ Response: {e.response.text[:200]}")
        return {"status": "http_error", "tool": tool_name, "error": str(e)}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "tool": tool_name, "error": str(e)}

async def main():
    """Основная функция для запуска всех тестов."""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК ПРОВЕРКИ ВСЕХ API ENDPOINTS")
    print("="*60)
    
    results = {
        "health": None,
        "root": None,
        "list_tools": None,
        "tools": {}
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Health check
        results["health"] = await test_health(client)
        
        # 2. Root endpoint
        results["root"] = await test_root(client)
        
        # 3. List tools (FastMCP 2.0 автоматически обрабатывает сессии)
        results["list_tools"] = await test_list_tools(client)
        
        # 4. Test each tool
        print("\n" + "="*60)
        print("4. Testing all tools")
        print("="*60)
        
        for tool_name, arguments in TEST_DATA.items():
            results["tools"][tool_name] = await test_tool_call(client, tool_name, arguments)
            await asyncio.sleep(0.5)  # Небольшая задержка между запросами
    
    # Итоговая статистика
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*60)
    
    print(f"\nHealth check: {results['health'].get('status', 'unknown')}")
    print(f"Root endpoint: {results['root'].get('status', 'unknown')}")
    print(f"List tools: {results['list_tools'].get('status', 'unknown')}")
    
    tools_ok = sum(1 for r in results["tools"].values() if r.get("status") == "ok")
    tools_error = sum(1 for r in results["tools"].values() if r.get("status") == "error")
    tools_tool_error = sum(1 for r in results["tools"].values() if r.get("status") == "tool_error")
    tools_http_error = sum(1 for r in results["tools"].values() if r.get("status") == "http_error")
    
    print(f"\nTools tested: {len(results['tools'])}")
    print(f"✅ OK: {tools_ok}")
    print(f"⚠️  Tool error: {tools_tool_error}")
    print(f"❌ HTTP error: {tools_http_error}")
    print(f"❌ Error: {tools_error}")
    
    # Сохранение результатов
    with open("api_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 Результаты сохранены в api_test_results.json")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())

