"""
FastAPI-based chat UI to talk to the agent via A2A URL.
Env:
  PUBLIC_URL – agent URL (with https://...)
  AGENT_TOKEN – bearer token
Run:
  uvicorn ui_app:app --port 8010 --reload
"""

import os
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from a2a.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest, AgentCard


load_dotenv()

DEFAULT_AGENT_URL = os.getenv(
    "PUBLIC_URL",
    "https://7f69ee58-fda6-4701-88c8-ec3ea67e4be1-agent-system.ai-agent.inference.cloud.ru",
)
DEFAULT_TOKEN = os.getenv(
    "AGENT_TOKEN",
    "NzM2MDBkMDAtMTY3Mi00YjZhLWE1MjEtMmRjOTdhMzNhNTUz.1764f1d2e2b9faf97b4e6f03f4c6d263",
)

app = FastAPI(title="Agent UI", version="0.1.0")

# Allow CORS for local dev (UI on 8080 or 3000) and same-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:8010",
    ],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SendPayload(BaseModel):
    message: str
    base_url: Optional[str] = None
    token: Optional[str] = None


async def _send_to_agent(base_url: str, token: str, message: str) -> Dict[str, Any]:
    """Send a single message to the agent using the a2a client stack."""
    if not base_url.endswith("/"):
        base_url = base_url + "/"
    timeout_config = httpx.Timeout(5 * 60.0, connect=30.0)
    headers: Dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=timeout_config, headers=headers) as httpx_client:
        agent_card = await _resolve_agent_card(httpx_client, base_url)

        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        send_message_payload: Dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
                "messageId": uuid4().hex,
            },
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))
        response = await client.send_message(request)
        return response.model_dump(mode="json", exclude_none=True)


async def _resolve_agent_card(httpx_client: httpx.AsyncClient, base_url: str) -> AgentCard:
    """Fetch agent card using the new recommended endpoint, with fallback."""
    paths = ["/.well-known/agent-card.json", "/.well-known/agent.json"]
    last_error: Optional[str] = None
    for path in paths:
        url = base_url.rstrip("/") + path
        try:
            resp = await httpx_client.get(url)
            if resp.status_code == 200:
                return AgentCard.model_validate(resp.json())
            last_error = f"HTTP {resp.status_code} at {url}"
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            continue
    raise RuntimeError(f"Failed to load agent card. Last error: {last_error}")


def _extract_text_from_a2a_response(response: Dict[str, Any]) -> str:
    """Best-effort extraction of textual answer from a2a JSON."""

    def walk_texts(obj, depth=0):
        texts = []
        if depth > 6:
            return texts
        if isinstance(obj, dict):
            if obj.get("kind") == "text" and isinstance(obj.get("text"), str):
                texts.append(obj["text"])
            for v in obj.values():
                texts.extend(walk_texts(v, depth + 1))
        elif isinstance(obj, list):
            for item in obj:
                texts.extend(walk_texts(item, depth + 1))
        return texts

    artifacts = response.get("result", {}).get("artifacts", [])
    texts = walk_texts(artifacts)
    if texts:
        return "\n\n".join(t for t in texts if isinstance(t, str) and t.strip()).strip()

    history = response.get("result", {}).get("history", [])
    texts = walk_texts(history)
    if texts:
        return "\n\n".join(t for t in texts if isinstance(t, str) and t.strip()).strip()

    txt = response.get("result", {}).get("text")
    if isinstance(txt, str) and txt.strip():
        return txt.strip()

    result = response.get("result", {})
    for v in result.values():
        if isinstance(v, str) and v.strip():
            return v.strip()

    return ""


def _format_human_readable(response: Dict[str, Any]) -> str:
    """Build a concise human-readable summary from agent response."""
    result = response.get("result", {}) if isinstance(response, dict) else {}
    status = result.get("status", {}) if isinstance(result, dict) else {}
    state = status.get("state", "unknown")
    ts = status.get("timestamp", "")

    artifacts = result.get("artifacts", []) if isinstance(result, dict) else []
    artifact_texts = []
    if isinstance(artifacts, list):
        for art in artifacts:
            parts = art.get("parts") if isinstance(art, dict) else None
            if isinstance(parts, list):
                for p in parts:
                    if isinstance(p, dict) and p.get("kind") == "text":
                        txt = p.get("text", "")
                        if txt:
                            artifact_texts.append(txt)

    history_lines = []
    history = result.get("history", []) if isinstance(result, dict) else []
    if isinstance(history, list):
        for entry in history:
            if not isinstance(entry, dict):
                continue
            role = entry.get("role", "")
            parts = entry.get("parts", [])
            texts = []
            if isinstance(parts, list):
                for p in parts:
                    if isinstance(p, dict) and p.get("kind") == "text":
                        t = p.get("text", "")
                        if t:
                            texts.append(t)
            if texts:
                history_lines.append(f"{role or 'message'}: " + " / ".join(texts))

    lines = []
    lines.append(f"Статус: {state}" + (f" @ {ts}" if ts else ""))
    if artifact_texts:
        lines.append("\nОтвет:")
        lines.append("\n\n".join(artifact_texts))
    if history_lines:
        lines.append("\nИстория:")
        lines.append("\n".join(f"• {h}" for h in history_lines))

    return "\n".join(lines).strip()


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/send")
async def send_message(body: SendPayload) -> Dict[str, Any]:
    try:
        base_url = (body.base_url or DEFAULT_AGENT_URL).strip()
        token = (body.token or DEFAULT_TOKEN or "").strip()
        if not base_url:
            raise ValueError("Agent URL is not configured. Set PUBLIC_URL in .env.")
        base_url = str(httpx.URL(base_url))
        data = await _send_to_agent(base_url, token, body.message)
        extracted = _extract_text_from_a2a_response(data)
        formatted = _format_human_readable(data)
        return {"ok": True, "text": extracted, "formatted": formatted, "data": data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.options("/api/send")
async def options_send() -> Dict[str, Any]:
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve a simple ChatGPT-like UI (env-based URL/token)."""
    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>A2A Agent UI</title>
      <style>
        :root {{ color-scheme: light dark; }}
        body {{
          margin: 0;
          font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
          background: #0b1221;
          color: #e8f0ff;
          display: flex;
          flex-direction: column;
          min-height: 100vh;
        }}
        .topbar {{
          padding: 14px 18px;
          border-bottom: 1px solid #1c2740;
          background: #0f1628;
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          align-items: center;
        }}
        .status-pill {{
          padding: 6px 10px;
          border-radius: 999px;
          background: #14203a;
          border: 1px solid #1f2f50;
          font-size: 13px;
          color: #9ab4ff;
        }}
        .container {{
          flex: 1;
          display: flex;
          flex-direction: column;
          max-width: 1200px;
          width: 100%;
          margin: 0 auto;
          padding: 16px;
          gap: 12px;
        }}
        .chat-box {{
          flex: 1;
          background: #0f1628;
          border: 1px solid #1e2d4a;
          border-radius: 16px;
          padding: 18px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 12px;
          box-shadow: 0 10px 32px rgba(0,0,0,0.35);
        }}
        .msg {{
          max-width: 80%;
          padding: 12px 14px;
          border-radius: 14px;
          line-height: 1.5;
          white-space: pre-wrap;
          word-break: break-word;
          border: 1px solid #203153;
        }}
        .msg.user {{
          margin-left: auto;
          background: linear-gradient(135deg, #4b8bff, #1fd1f9);
          color: #0b1221;
          border: none;
        }}
        .msg.bot {{
          margin-right: auto;
          background: #111a2e;
          color: #e8f0ff;
        }}
        .input-bar {{
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 10px;
          padding: 12px;
          background: #0f1628;
          border: 1px solid #1e2d4a;
          border-radius: 16px;
          box-shadow: 0 10px 32px rgba(0,0,0,0.35);
        }}
        textarea {{
          width: 100%;
          background: #0b1221;
          color: #e8f0ff;
          border: 1px solid #1f2f50;
          border-radius: 12px;
          padding: 12px;
          min-height: 60px;
          resize: vertical;
        }}
        button {{
          padding: 12px 18px;
          border: none;
          border-radius: 12px;
          background: linear-gradient(135deg, #4b8bff, #1fd1f9);
          color: #0b1221;
          font-weight: 700;
          cursor: pointer;
          min-width: 120px;
        }}
        button:disabled {{
          opacity: 0.6;
          cursor: not-allowed;
        }}
        .subtext {{
          font-size: 13px;
          color: #9ab4ff;
        }}
      </style>
    </head>
    <body>
      <div class="topbar">
        <span class="status-pill">Health: <span id="health">–</span></span>
        <span class="status-pill" id="status">Idle</span>
        <span class="subtext">Используются значения из .env (PUBLIC_URL / AGENT_TOKEN)</span>
      </div>

      <div class="container">
        <div class="chat-box" id="chatBox">
          <div class="msg bot">Привет! Используются PUBLIC_URL / AGENT_TOKEN из .env. Просто введите сообщение ниже.</div>
        </div>

        <div class="input-bar">
          <textarea id="message" placeholder="Напишите запрос..." rows="3"></textarea>
          <div style="display:flex; flex-direction:column; gap:8px;">
            <button id="sendBtn">Send</button>
            <button id="clearBtn" style="background:#1c2740; color:#e8f0ff;">Clear</button>
          </div>
        </div>
        <div class="subtext">Отправка идёт через /api/send с a2a клиентом. URL и токен берутся из .env (или дефолтов в коде).</div>
      </div>

      <script>
        const chatBox = document.getElementById("chatBox");
        const statusEl = document.getElementById("status");
        const healthEl = document.getElementById("health");
        const msgInput = document.getElementById("message");
        const sendBtn = document.getElementById("sendBtn");
        const clearBtn = document.getElementById("clearBtn");

        function appendMessage(text, role) {{
          const div = document.createElement("div");
          div.className = `msg ${{role}}`;
          div.textContent = text;
          chatBox.appendChild(div);
          chatBox.scrollTop = chatBox.scrollHeight;
        }}

        async function checkHealth() {{
          try {{
            const res = await fetch("/health");
            const data = await res.json();
            healthEl.textContent = data.status === "ok" ? "ok" : "error";
          }} catch {{
            healthEl.textContent = "error";
          }}
        }}
        checkHealth();

        async function sendMessage() {{
          const message = msgInput.value.trim();
          if (!message) {{
            statusEl.textContent = "Введите сообщение";
            return;
          }}
          appendMessage(message, "user");
          statusEl.textContent = "Отправляем...";
          sendBtn.disabled = true;
          try {{
            const res = await fetch("/api/send", {{
              method: "POST",
              headers: {{ "Content-Type": "application/json" }},
              body: JSON.stringify({{ message }}),
            }});
            const data = await res.json();
            if (data.ok) {{
              const shown =
                (data.formatted && data.formatted.trim())
                  ? data.formatted
                  : (data.text && data.text.trim())
                    ? data.text
                    : JSON.stringify(data.data, null, 2);
              appendMessage(shown, "bot");
              statusEl.textContent = "Готово";
            }} else {{
              appendMessage("Ошибка: " + (data.detail || data.error || "unknown"), "bot");
              statusEl.textContent = "Ошибка";
            }}
          }} catch (err) {{
            appendMessage("Ошибка запроса: " + err, "bot");
            statusEl.textContent = "Ошибка";
          }} finally {{
            sendBtn.disabled = false;
            msgInput.value = "";
            msgInput.focus();
          }}
        }}

        sendBtn.addEventListener("click", sendMessage);
        msgInput.addEventListener("keydown", (e) => {{
          if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {{
            sendMessage();
          }}
        }});
        clearBtn.addEventListener("click", () => {{
          chatBox.innerHTML = "";
        }});
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


