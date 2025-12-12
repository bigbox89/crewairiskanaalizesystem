import json, httpx, uuid
BASE = "https://ed00be74-9d99-44a9-9c57-7ffbd52fdb62-mcp-server.ai-agent.inference.cloud.ru"
SESSION = str(uuid.uuid4())
MCP = f"{BASE}/mcp"
HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
    "X-Session-Id": SESSION,
}
print("Using session", SESSION)

def mcp_call(method, params, id_=1):
    payload = {"jsonrpc": "2.0", "id": id_, "method": method, "params": params}
    resp = httpx.post(MCP, json=payload, headers=HEADERS, timeout=40)
    print(f"\n== {method} -> {resp.status_code} {resp.headers.get('content-type')}")
    if resp.status_code != 200:
        print(resp.text[:500])
        return None
    if "text/event-stream" in (resp.headers.get("content-type") or ""):
        for line in resp.text.splitlines():
            if line.startswith("data: "):
                payload = line[6:]
                try:
                    obj = json.loads(payload)
                    print(json.dumps(obj, ensure_ascii=False, indent=2))
                    return obj
                except Exception:
                    print("RAW:", payload[:500])
    else:
        print(resp.text[:500])
    return None

print("== tools/list")
mcp_call("tools/list", {"sessionId": SESSION}, 1)
