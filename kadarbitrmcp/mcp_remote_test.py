import json, httpx, uuid
BASE = "https://ed00be74-9d99-44a9-9c57-7ffbd52fdb62-mcp-server.ai-agent.inference.cloud.ru"
SESSION = str(uuid.uuid4())
MCP = f"{BASE}/mcp?sessionId={SESSION}"
HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
    "X-Session-Id": SESSION,
}
print("Using session", SESSION)

def mcp_call(method, params, id_=1):
    resp = httpx.post(
        MCP,
        json={"jsonrpc": "2.0", "id": id_, "method": method, "params": params},
        headers=HEADERS,
        timeout=40,
    )
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
list_resp = mcp_call("tools/list", {}, 1)

print("== arbitr_search_cases")
search = mcp_call(
    "tools/call",
    {
        "name": "arbitr_search_cases",
        "arguments": {
            "Inn": "ROSNEFT",
            "DateFrom": "2020-10-16",
            "DateTo": "2020-11-16",
        },
    },
    2,
)
case_id = "b82051d4-9713-4dcd-8de5-ef6d18d8ac66"
if search:
    sc = search.get("result", {}).get("result", {}).get("structured_content", {})
    cases = sc.get("Cases", [])
    if cases:
        case_id = cases[0].get("CaseId", case_id)

print("== arbitr_details_by_number")
mcp_call(
    "tools/call",
    {"name": "arbitr_details_by_number", "arguments": {"CaseNumber": "A71-1202/2015"}},
    3,
)

print("== arbitr_details_by_id")
mcp_call(
    "tools/call",
    {"name": "arbitr_details_by_id", "arguments": {"CaseId": case_id}},
    4,
)

print("== arbitr_download_pdf")
mcp_call(
    "tools/call",
    {
        "name": "arbitr_download_pdf",
        "arguments": {
            "url": "https://kad.arbitr.ru/PdfDocument/63778dcd-c696-4863-b781-73a839cbf8a8/A71-1202-2015_20150507_Reshenija%20i%20postanovlenija.pdf"
        },
    },
    5,
)
