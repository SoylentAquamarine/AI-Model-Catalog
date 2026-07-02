#!/usr/bin/env python3
"""Update providers/mistral.json from the Mistral models API.

Source: https://api.mistral.ai/v1/models — requires MISTRAL_API_KEY_FREE.
Mistral's endpoint is unusually rich: it returns a per-model capabilities
object (chat, function calling, vision) and context length, all of which
ground catalog claims at high confidence. Mistral documents a rate-limited
free tier on La Plateforme.
"""

from __future__ import annotations

import catalog_lib as lib

MODELS_URL = "https://api.mistral.ai/v1/models"
SOURCE = "mistral_models_api"


def build_model(entry: dict) -> dict | None:
    model_id = entry.get("id")
    if not model_id:
        return None

    caps = entry.get("capabilities") or {}

    def api_cap(value) -> dict:
        return lib.capability(bool(value), SOURCE, "high")

    capabilities = {
        "chat": api_cap(caps.get("completion_chat")),
        "tools": api_cap(caps.get("function_calling")),
        "vision": api_cap(caps.get("vision")),
        "fine_tuning": api_cap(caps.get("fine_tuning")),
    }

    limits = None
    context = entry.get("max_context_length")
    if context:
        limits = {"contextTokens": context, "maxOutputTokens": None}

    return {
        "id": model_id,
        "providerModelId": model_id,
        "displayName": entry.get("name") or model_id,
        "costClass": "free",
        "pricing": None,
        "limits": limits,
        "capabilities": capabilities,
        "status": "available",
        "source": SOURCE,
        "lastChecked": lib.now_iso(),
    }


def main() -> int:
    key = lib.optional_key("MISTRAL_API_KEY_FREE", "mistral")
    if key is None:
        return 0

    payload = lib.http_get_json(MODELS_URL, headers={"Authorization": f"Bearer {key}"})
    entries = payload.get("data") or []
    if not entries:
        raise SystemExit("mistral: models API returned no data; aborting.")

    models = [m for m in (build_model(e) for e in entries) if m]
    lib.finish("mistral", models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
