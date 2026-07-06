#!/usr/bin/env python3
"""Live capability probes for the AI Model Catalog test harness.

Each probe makes ONE tiny API call and returns a ProbeResult:
    "pass"  -> the capability is confirmed supported  (value: true)
    "fail"  -> the capability is confirmed unsupported (value: false)
    "error" -> transient/unknown (429, 5xx, timeout, model unusable) -> skip,
               retried on the next rotation; nothing is recorded.

Only two adapters are needed because every free provider in the catalog uses
apiType "openai-compatible" or "gemini". Probes never print secrets.

Capabilities probed (the core 5): chat, json, streaming, tools, vision.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 30
MAX_TOKENS = 16
USER_AGENT = "AI-Model-Catalog-capability-tester (+https://github.com/SoylentAquamarine/AI-Model-Catalog)"

CHAT_PROMPT = "Reply with the single word: ok"
JSON_PROMPT = 'Return a JSON object exactly like {"ok": true} and nothing else.'
TOOLS_PROMPT = "Call the ping function now."
VISION_PROMPT = "What color is this image? Answer in one word."

# A 1x1 transparent PNG, used for the vision probe (smallest possible image).
PNG_1PX_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
PNG_1PX_DATA_URI = "data:image/png;base64," + PNG_1PX_B64

CAPABILITIES = ("chat", "json", "streaming", "tools", "vision")

PASS, FAIL, ERROR = "pass", "fail", "error"


# --------------------------------------------------------------------------- #
# Low-level HTTP
# --------------------------------------------------------------------------- #
def _post(url: str, headers: dict, body: dict, stream: bool = False):
    """POST JSON. Returns (status, text). status 0 means a transport error."""
    data = json.dumps(body).encode("utf-8")
    merged = {"User-Agent": USER_AGENT, "Content-Type": "application/json", "Accept": "application/json"}
    merged.update(headers)
    req = urllib.request.Request(url, data=data, headers=merged, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if stream:
                # Read just enough to confirm at least one streamed chunk arrives.
                chunk = resp.read(4096)
                return resp.status, chunk.decode("utf-8", "replace")
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        try:
            text = exc.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            text = ""
        return exc.code, text
    except Exception:  # noqa: BLE001  (timeout, connection reset, etc.)
        return 0, ""


def _classify_http(status: int) -> str | None:
    """Map an HTTP status to ERROR (transient) or None (usable response).

    400/422 are treated by callers as a clean 'unsupported feature' (FAIL) for
    feature probes; everything else non-2xx is ERROR so we never record a false
    negative from a rate limit or outage.
    """
    if 200 <= status < 300:
        return None
    if status in (400, 422):
        return "unsupported"
    return ERROR


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
def _apply_auth(provider: dict, key: str | None, url: str, headers: dict) -> str:
    """Attach the provider's credential to headers/url; return the (maybe) new url."""
    auth = provider.get("auth") or {}
    scheme = auth.get("scheme")
    if scheme == "bearer" and key:
        headers["Authorization"] = f"Bearer {key}"
    elif scheme == "header" and key:
        headers[auth.get("name") or "Authorization"] = key
    elif scheme == "query" and key:
        sep = "&" if "?" in url else "?"
        url = url + sep + urllib.parse.urlencode({auth.get("name") or "key": key})
    for hk, hv in (auth.get("extraHeaders") or {}).items():
        headers[hk] = hv
    return url


def _model_send_id(model: dict) -> str:
    return model.get("providerModelId") or model["id"]


# --------------------------------------------------------------------------- #
# openai-compatible adapter
# --------------------------------------------------------------------------- #
def _openai(provider: dict, model: dict, capability: str, key: str | None) -> str:
    base = provider["apiBase"].rstrip("/")
    url = base + "/chat/completions"
    headers: dict = {}
    url = _apply_auth(provider, key, url, headers)
    send_id = _model_send_id(model)

    if capability == "chat":
        body = {"model": send_id, "messages": [{"role": "user", "content": CHAT_PROMPT}], "max_tokens": MAX_TOKENS}
        status, text = _post(url, headers, body)
        cls = _classify_http(status)
        if cls in (ERROR, "unsupported"):
            return ERROR  # a non-2xx on plain chat means the model isn't usable for chat here; skip
        return PASS if _openai_text(text) else FAIL

    if capability == "json":
        body = {
            "model": send_id,
            "messages": [{"role": "user", "content": JSON_PROMPT}],
            "max_tokens": 48,
            "response_format": {"type": "json_object"},
        }
        status, text = _post(url, headers, body)
        cls = _classify_http(status)
        if cls == ERROR:
            return ERROR
        if cls == "unsupported":
            return FAIL  # provider rejected response_format -> structured JSON not supported
        content = _openai_text(text)
        if not content:
            return FAIL
        try:
            json.loads(content)
            return PASS
        except (ValueError, TypeError):
            return FAIL

    if capability == "streaming":
        body = {
            "model": send_id,
            "messages": [{"role": "user", "content": CHAT_PROMPT}],
            "max_tokens": MAX_TOKENS,
            "stream": True,
        }
        status, text = _post(url, headers, body, stream=True)
        cls = _classify_http(status)
        if cls == ERROR:
            return ERROR
        if cls == "unsupported":
            return FAIL
        return PASS if ("data:" in text or '"delta"' in text) else FAIL

    if capability == "tools":
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "ping",
                    "description": "Respond to a ping.",
                    "parameters": {"type": "object", "properties": {"ok": {"type": "boolean"}}},
                },
            }
        ]
        body = {
            "model": send_id,
            "messages": [{"role": "user", "content": TOOLS_PROMPT}],
            "tools": tools,
            "tool_choice": "auto",
            "max_tokens": 48,
        }
        status, text = _post(url, headers, body)
        cls = _classify_http(status)
        if cls == ERROR:
            return ERROR
        if cls == "unsupported":
            return FAIL
        return PASS if _openai_has_tool_call(text) else FAIL

    if capability == "vision":
        content = [
            {"type": "text", "text": VISION_PROMPT},
            {"type": "image_url", "image_url": {"url": PNG_1PX_DATA_URI}},
        ]
        body = {"model": send_id, "messages": [{"role": "user", "content": content}], "max_tokens": MAX_TOKENS}
        status, text = _post(url, headers, body)
        cls = _classify_http(status)
        if cls == ERROR:
            return ERROR
        if cls == "unsupported":
            return FAIL
        return PASS if _openai_text(text) else FAIL

    raise ValueError(f"unknown capability {capability!r}")


def _openai_text(text: str) -> str:
    try:
        data = json.loads(text)
        return (data["choices"][0]["message"].get("content") or "").strip()
    except (ValueError, KeyError, IndexError, TypeError):
        return ""


def _openai_has_tool_call(text: str) -> bool:
    try:
        data = json.loads(text)
        msg = data["choices"][0]["message"]
        return bool(msg.get("tool_calls"))
    except (ValueError, KeyError, IndexError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# gemini adapter
# --------------------------------------------------------------------------- #
def _gemini(provider: dict, model: dict, capability: str, key: str | None) -> str:
    base = provider["apiBase"].rstrip("/")
    send_id = _model_send_id(model)  # already like "models/gemini-2.0-flash"
    verb = "streamGenerateContent" if capability == "streaming" else "generateContent"
    url = f"{base}/{send_id}:{verb}"
    headers: dict = {}
    url = _apply_auth(provider, key, url, headers)

    gen_config = {"maxOutputTokens": MAX_TOKENS}
    parts = [{"text": CHAT_PROMPT}]

    if capability == "json":
        gen_config["responseMimeType"] = "application/json"
        parts = [{"text": JSON_PROMPT}]
    elif capability == "vision":
        parts = [
            {"text": VISION_PROMPT},
            {"inlineData": {"mimeType": "image/png", "data": PNG_1PX_B64}},
        ]

    body: dict = {"contents": [{"parts": parts}], "generationConfig": gen_config}

    if capability == "tools":
        body["tools"] = [
            {"functionDeclarations": [{"name": "ping", "description": "Respond to a ping.",
                                       "parameters": {"type": "object", "properties": {}}}]}
        ]
        body["contents"] = [{"parts": [{"text": TOOLS_PROMPT}]}]

    status, text = _post(url, headers, body, stream=(capability == "streaming"))
    cls = _classify_http(status)
    if cls == ERROR:
        return ERROR
    if cls == "unsupported":
        return ERROR if capability == "chat" else FAIL

    if capability == "streaming":
        return PASS if ('"text"' in text or '"candidates"' in text) else FAIL
    if capability == "tools":
        return PASS if '"functionCall"' in text else FAIL
    if capability == "json":
        content = _gemini_text(text)
        if not content:
            return FAIL
        try:
            json.loads(content)
            return PASS
        except (ValueError, TypeError):
            return FAIL
    # chat / vision
    if capability == "chat" and not _gemini_text(text):
        return ERROR
    return PASS if _gemini_text(text) else FAIL


def _gemini_text(text: str) -> str:
    try:
        data = json.loads(text)
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()
    except (ValueError, KeyError, IndexError, TypeError):
        return ""


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def run_probe(provider: dict, model: dict, capability: str, key: str | None) -> str:
    """Run one capability probe. Returns PASS / FAIL / ERROR."""
    api_type = provider.get("apiType")
    if api_type == "gemini":
        return _gemini(provider, model, capability, key)
    if api_type == "openai-compatible":
        return _openai(provider, model, capability, key)
    return ERROR  # unknown driver: never fabricate a result
