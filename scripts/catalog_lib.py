#!/usr/bin/env python3
"""Shared helpers for AI Model Catalog updater and build scripts.

Updater contract (every update_<provider>.py follows it):
- Missing API key      -> print a skip note, exit 0, existing file untouched.
- Remote fetch failure -> exit nonzero so the workflow fails loudly.
- Empty model list     -> exit nonzero rather than wiping a good file.
- Success              -> rewrite providers/<id>.json with sorted models and
                          a fresh provider.lastChecked.

Secrets are never printed, logged, or written into catalog files.
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_DIR = ROOT / "providers"
SCHEMA_VERSION = "1.0.0"
USER_AGENT = (
    "AI-Model-Catalog-updater "
    "(+https://github.com/SoylentAquamarine/AI-Model-Catalog)"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_provider(provider_id: str) -> dict:
    path = PROVIDERS_DIR / f"{provider_id}.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_provider(provider_id: str, data: dict) -> None:
    path = PROVIDERS_DIR / f"{provider_id}.json"
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def http_get_json(url: str, headers: dict | None = None, timeout: int = 60) -> object:
    merged = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    merged.update(headers or {})
    request = urllib.request.Request(url, headers=merged)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def optional_key(env_var: str, provider_id: str) -> str | None:
    """Return the API key from env_var, or None (with a skip note) if unset."""
    key = os.environ.get(env_var, "").strip()
    if not key:
        print(
            f"{provider_id}: {env_var} not configured; "
            "skipping remote update, existing file kept."
        )
        return None
    return key


def capability(value, source: str, confidence: str, notes: str | None = None) -> dict:
    cap = {
        "value": value,
        "source": source,
        "confidence": confidence,
        "lastChecked": now_iso(),
    }
    if notes:
        cap["notes"] = notes
    return cap


def update_openai_style(
    provider_id: str,
    models_url: str,
    env_var: str,
    cost_class: str,
    source: str,
) -> int:
    """Shared flow for providers whose models endpoint is plain OpenAI-shaped:
    GET {models_url} with a bearer key -> {"data": [{"id": ...}, ...]}.
    Records model presence honestly; leaves capabilities empty rather than
    guessing what the endpoint does not state."""
    key = optional_key(env_var, provider_id)
    if key is None:
        return 0

    payload = http_get_json(models_url, headers={"Authorization": f"Bearer {key}"})
    entries = payload.get("data") if isinstance(payload, dict) else payload
    if not entries:
        raise SystemExit(f"{provider_id}: models API returned no data; aborting.")

    models = []
    for entry in entries:
        model_id = entry.get("id")
        if not model_id:
            continue
        models.append(
            {
                "id": model_id,
                "providerModelId": model_id,
                "displayName": entry.get("display_name") or model_id,
                "costClass": cost_class,
                "pricing": None,
                "limits": None,
                "capabilities": {},
                "status": "available",
                "source": source,
                "lastChecked": now_iso(),
            }
        )

    finish(provider_id, models)
    return 0


def finish(provider_id: str, models: list[dict]) -> None:
    """Write the provider file with refreshed models, keeping the provider block."""
    if not models:
        raise SystemExit(
            f"{provider_id}: updater produced zero models; "
            "refusing to overwrite the existing file."
        )
    data = load_provider(provider_id)
    data["schemaVersion"] = SCHEMA_VERSION
    data["provider"]["lastChecked"] = now_iso()
    data["models"] = sorted(models, key=lambda m: m["id"])
    save_provider(provider_id, data)
    print(f"{provider_id}: wrote {len(models)} models.")
