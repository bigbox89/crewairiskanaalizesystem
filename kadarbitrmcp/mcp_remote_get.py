import httpx, uuid, json
BASE = "https://ed00be74-9d99-44a9-9c57-7ffbd52fdb62-mcp-server.ai-agent.inference.cloud.ru"
MCP = f"{BASE}/mcp"
SESSION = str(uuid.uuid4())

# Try establish session with GET Accept: text/event-stream
resp = httpx.get(MCP, headers={"Accept":"text/event-stream","X-Session-Id":SESSION}, timeout=20)
print("GET /mcp", resp.status_code, resp.headers.get('content-type'))
print(resp.text[:200])
