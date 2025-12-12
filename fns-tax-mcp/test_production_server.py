"""Скрипт для проверки продакшн сервера."""
import asyncio
import json
import httpx
from typing import Dict, Any

BASE_URL = "https://b850adf3-acab-4d34-bd4f-9ed81f408203-mcp-server.ai-agent.inference.cloud.ru"

async def test_health(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Проверка health endpoint."""
    print("\n" + "="*60)
    print("1. Testing GET /health")
    print("="*60)
    try:
        response = await client.get(f"{BASE_URL}/health", timeout=10.0)
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
        response = await client.get(f"{BASE_URL}/", timeout=10.0)
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
    """Проверка tools/list через FastMCP Client."""
    print("\n" + "="*60)
    print("3. Testing POST /mcp (tools/list)")
    print("="*60)
    try:
        request_body = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        response = await client.post(
            f"{BASE_URL}/mcp",
            json=request_body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            timeout=30.0
        )
        response.raise_for_status()
        
        # FastMCP 2.0 использует SSE формат
        text = response.text
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response type: {response.headers.get('content-type', 'N/A')}")
        
        # Пытаемся найти JSON в SSE потоке
        if "data:" in text:
            lines = text.split("\n")
            for line in lines:
                if line.startswith("data: "):
                    json_str = line[6:]  # Убираем "data: "
                    try:
                        data = json.loads(json_str)
                        tools = data.get("result", {}).get("tools", [])
                        print(f"✅ Tools count: {len(tools)}")
                        if tools:
                            print(f"✅ First tool: {tools[0].get('name', 'N/A')}")
                        return {"status": "ok", "tools_count": len(tools), "response": data}
                    except json.JSONDecodeError:
                        pass
        
        print(f"⚠️  Response preview: {text[:200]}...")
        return {"status": "ok", "response_text": text[:500]}
    except Exception as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"❌ Response: {e.response.text[:200]}")
        return {"status": "error", "error": str(e)}

async def test_tool_call(client: httpx.AsyncClient, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Проверка вызова конкретного tool."""
    print(f"\n{'='*60}")
    print(f"4. Testing tool: {tool_name}")
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
        
        text = response.text
        print(f"✅ Status: {response.status_code}")
        
        # Пытаемся найти JSON в SSE потоке
        if "data:" in text:
            lines = text.split("\n")
            for line in lines:
                if line.startswith("data: "):
                    json_str = line[6:]
                    try:
                        data = json.loads(json_str)
                        if "error" in data:
                            print(f"⚠️  Tool error: {data.get('error', {}).get('message', 'Unknown')}")
                            return {"status": "tool_error", "tool": tool_name, "error": data.get("error")}
                        else:
                            result = data.get("result", {})
                            print(f"✅ Tool executed successfully")
                            return {"status": "ok", "tool": tool_name, "response": result}
                    except json.JSONDecodeError:
                        pass
        
        print(f"⚠️  Response preview: {text[:200]}...")
        return {"status": "ok", "tool": tool_name, "response_text": text[:500]}
    except Exception as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"❌ Response: {e.response.text[:200]}")
        return {"status": "error", "tool": tool_name, "error": str(e)}

async def main():
    """Основная функция для запуска всех тестов."""
    print("\n" + "="*60)
    print("🚀 ПРОВЕРКА ПРОДАКШН СЕРВЕРА")
    print("="*60)
    print(f"URL: {BASE_URL}")
    
    results = {
        "health": None,
        "root": None,
        "list_tools": None,
        "tool_call": None
    }
    
    async with httpx.AsyncClient(verify=True, timeout=60.0) as client:
        # 1. Health check
        results["health"] = await test_health(client)
        
        # 2. Root endpoint
        results["root"] = await test_root(client)
        
        # 3. List tools
        results["list_tools"] = await test_list_tools(client)
        
        # 4. Test one tool (generate_usn_declaration)
        results["tool_call"] = await test_tool_call(
            client,
            "generate_usn_declaration",
            {
                "inn": "7707083893",
                "period": "Q1",
                "year": 2025,
                "income": 1000000.0,
                "expenses": 0.0,
                "tax_rate": 6
            }
        )
    
    # Итоговая статистика
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*60)
    
    print(f"\nHealth check: {results['health'].get('status', 'unknown')}")
    print(f"Root endpoint: {results['root'].get('status', 'unknown')}")
    print(f"List tools: {results['list_tools'].get('status', 'unknown')}")
    print(f"Tool call: {results['tool_call'].get('status', 'unknown')}")
    
    # Сохранение результатов
    with open("production_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 Результаты сохранены в production_test_results.json")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())


