#!/usr/bin/env python3
"""Live capability probes for the AI Model Catalog test harness.

Each probe makes ONE tiny API call and returns (outcome, detail):

    outcome: "pass"  -> capability confirmed supported   (value: true)
             "fail"  -> capability confirmed unsupported  (value: false)
             "error" -> transient/unknown -> skip, retry next rotation, nothing
                        recorded as a capability
    detail:  a short reason code so nothing is guessed -- e.g. "ok", "empty",
             "unsupported_param", "bad_json", "no_tool_call", "no_stream",
             "http_404", "http_429", "http_500", "timeout", "conn_error",
             "exception:KeyError".

Only two adapters are needed because every free provider uses apiType
"openai-compatible" or "gemini". Probes never print or return secrets.

Capabilities probed (the core 5): chat, json, streaming, tools, vision.
"""

from __future__ import annotations

import json
import socket
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

# Sentinel HTTP statuses from _post for transport failures:
_TIMEOUT = -1
_CONN = 0


# --------------------------------------------------------------------------- #
# Low-level HTTP
# --------------------------------------------------------------------------- #
def _post(url: str, headers: dict, body: dict, stream: bool = False):
    """POST JSON. Returns (status, text).

    status > 0  -> real HTTP status code
    status == 0 -> connection error (DNS, reset, refused)
    status ==-1 -> timeout
    """
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
    except (TimeoutError, socket.timeout):
        return _TIMEOUT, ""
    except urllib.error.URLError as exc:
        if isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout)):
            return _TIMEOUT, ""
        return _CONN, ""
    except Exception:  # noqa: BLE001
        return _CONN, ""


def _status_detail(status: int) -> str:
    if status == _TIMEOUT:
        return "timeout"
    if status == _CONN:
        return "conn_error"
    return f"http_{status}"


def _feature_result(status: int, text: str, evaluate) -> tuple[str, str]:
    """Shared classification for the feature probes (json/streaming/tools/vision).

    A clean 200 is judged by `evaluate(text) -> (ok: bool, reason: str)`.
    400/422 means the provider rejected the feature -> confirmed FAIL.
    Anything else non-2xx is a transient ERROR carrying its status detail.
    """
    if 200 <= status < 300:
        ok, reason = evaluate(text)
        return (PASS, "ok") if ok else (FAIL, reason)
    if status in (400, 422):
        return FAIL, "unsupported_param"
    return ERROR, _status_detail(status)


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
def _openai(provider: dict, model: dict, capability: str, key: str | None) -> tuple[str, str]:
    base = provider["apiBase"].rstrip("/")
    url = base + "/chat/completions"
    headers: dict = {}
    url = _apply_auth(provider, key, url, headers)
    send_id = _model_send_id(model)

    if capability == "chat":
        body = {"model": send_id, "messages": [{"role": "user", "content": CHAT_PROMPT}], "max_tokens": MAX_TOKENS}
        status, text = _post(url, headers, body)
        if 200 <= status < 300:
            return (PASS, "ok") if _openai_text(text) else (FAIL, "empty")
        return ERROR, _status_detail(status)  # chat itself failing -> can't judge; skip

    if capability == "json":
        body = {
            "model": send_id,
            "messages": [{"role": "user", "content": JSON_PROMPT}],
            "max_tokens": 48,
            "response_format": {"type": "json_object"},
        }
        status, text = _post(url, headers, body)
        return _feature_result(status, text, _eval_json_openai)

    if capability == "streaming":
        body = {
            "model": send_id,
            "messages": [{"role": "user", "content": CHAT_PROMPT}],
            "max_tokens": MAX_TOKENS,
            "stream": True,
        }
        status, text = _post(url, headers, body, stream=True)
        return _feature_result(status, text, lambda t: (("data:" in t or '"delta"' in t), "no_stream"))

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
        return _feature_result(status, text, lambda t: (_openai_has_tool_call(t), "no_tool_call"))

    if capability == "vision":
        content = [
            {"type": "text", "text": VISION_PROMPT},
            {"type": "image_url", "image_url": {"url": PNG_1PX_DATA_URI}},
        ]
        body = {"model": send_id, "messages": [{"role": "user", "content": content}], "max_tokens": MAX_TOKENS}
        status, text = _post(url, headers, body)
        return _feature_result(status, text, lambda t: (bool(_openai_text(t)), "empty"))

    raise ValueError(f"unknown capability {capability!r}")


def _eval_json_openai(text: str) -> tuple[bool, str]:
    content = _openai_text(text)
    if not content:
        return False, "empty"
    try:
        json.loads(content)
        return True, "ok"
    except (ValueError, TypeError):
        return False, "bad_json"


def _coerce_text(content) -> str:
    """Normalise an OpenAI message `content` to text.

    Providers return content either as a plain string or as a list of content
    parts (e.g. [{"type": "text", "text": "..."}]). Handle both.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        out = []
        for part in content:
            if isinstance(part, dict):
                out.append(part.get("text") or part.get("content") or "")
            elif isinstance(part, str):
                out.append(part)
        return "".join(out).strip()
    return str(content).strip()


def _openai_text(text: str) -> str:
    try:
        data = json.loads(text)
        content = data["choices"][0]["message"].get("content")
    except (ValueError, KeyError, IndexError, TypeError):
        return ""
    return _coerce_text(content)


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
def _gemini(provider: dict, model: dict, capability: str, key: str | None) -> tuple[str, str]:
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

    if capability == "chat":
        if 200 <= status < 300:
            return (PASS, "ok") if _gemini_text(text) else (FAIL, "empty")
        return ERROR, _status_detail(status)
    if capability == "streaming":
        return _feature_result(status, text, lambda t: (('"text"' in t or '"candidates"' in t), "no_stream"))
    if capability == "tools":
        return _feature_result(status, text, lambda t: (('"functionCall"' in t), "no_tool_call"))
    if capability == "json":
        return _feature_result(status, text, _eval_json_gemini)
    if capability == "vision":
        return _feature_result(status, text, lambda t: (bool(_gemini_text(t)), "empty"))

    raise ValueError(f"unknown capability {capability!r}")


def _eval_json_gemini(text: str) -> tuple[bool, str]:
    content = _gemini_text(text)
    if not content:
        return False, "empty"
    try:
        json.loads(content)
        return True, "ok"
    except (ValueError, TypeError):
        return False, "bad_json"


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
def run_probe(provider: dict, model: dict, capability: str, key: str | None) -> tuple[str, str]:
    """Run one capability probe. Returns (outcome, detail).

    A probe must never crash the weekly run: any unexpected error becomes
    ERROR with an exception detail and is retried on the next rotation.
    """
    try:
        api_type = provider.get("apiType")
        if api_type == "gemini":
            return _gemini(provider, model, capability, key)
        if api_type == "openai-compatible":
            return _openai(provider, model, capability, key)
        return ERROR, "unknown_driver"
    except Exception as exc:  # noqa: BLE001  -- resilience: skip, do not abort the run
        return ERROR, f"exception:{type(exc).__name__}"
