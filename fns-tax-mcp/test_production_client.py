"""Проверка продакшн сервера через FastMCP Client."""
import asyncio
import json
from typing import Dict, Any

try:
    from fastmcp import Client
except ImportError:
    print("❌ FastMCP Client не установлен. Установите: pip install fastmcp>=2.0.0")
    exit(1)

BASE_URL = "https://b850adf3-acab-4d34-bd4f-9ed81f408203-mcp-server.ai-agent.inference.cloud.ru/mcp"

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
            print(f"✅ Sample tools: {', '.join([t.name for t in tools[:5]])}")
        return {"status": "ok", "tools_count": len(tools)}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}

async def test_tool_call(client: Client, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Проверка вызова конкретного tool через FastMCP Client."""
    print(f"\n{'='*60}")
    print(f"4. Testing tool: {tool_name}")
    print(f"{'='*60}")
    try:
        result = await client.call_tool(name=tool_name, arguments=arguments)
        
        if hasattr(result, 'content') and result.content:
            text_preview = str(result.content[0])[:300] if result.content else "N/A"
            print(f"✅ Status: OK")
            print(f"✅ Content preview: {text_preview}...")
        else:
            print(f"✅ Status: OK (no content)")
        
        return {
            "status": "ok",
            "tool": tool_name,
            "result": str(result)[:300] if result else "N/A"
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "tool": tool_name, "error": str(e)}

async def main():
    """Основная функция для запуска всех тестов."""
    print("\n" + "="*60)
    print("🚀 ПРОВЕРКА ПРОДАКШН СЕРВЕРА (FastMCP Client)")
    print("="*60)
    print(f"URL: {BASE_URL}")
    
    results = {
        "list_tools": None,
        "tool_call": None
    }
    
    # CHANGE: Использование FastMCP Client для автоматической обработки сессий
    client = Client(BASE_URL)
    
    try:
        async with client:
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
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Итоговая статистика
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*60)
    
    print(f"\nList tools: {results['list_tools'].get('status', 'unknown')}")
    print(f"Tool call: {results['tool_call'].get('status', 'unknown')}")
    
    # Сохранение результатов
    with open("production_test_results_client.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 Результаты сохранены в production_test_results_client.json")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())


