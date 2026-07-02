#!/usr/bin/env python3
"""Update providers/cohere.json from the Cohere models API.

Source: https://api.cohere.com/v1/models — requires COHERE_API_KEY_FREE.
Each model lists its supported endpoints (chat, embed, rerank), which
ground capability claims at high confidence. Cohere trial keys are free
with rate limits, so models are classed as trial.
"""

from __future__ import annotations

import urllib.parse

import catalog_lib as lib

MODELS_URL = "https://api.cohere.com/v1/models"
SOURCE = "cohere_models_api"


def fetch_all(key: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {key}"}
    entries: list[dict] = []
    page_token = None
    while True:
        params = {"page_size": "100"}
        if page_token:
            params["page_token"] = page_token
        payload = lib.http_get_json(
            f"{MODELS_URL}?{urllib.parse.urlencode(params)}", headers=headers
        )
        entries.extend(payload.get("models") or [])
        page_token = payload.get("next_page_token")
        if not page_token:
            return entries


def build_model(entry: dict) -> dict | None:
    model_id = entry.get("name")
    if not model_id:
        return None

    endpoints = set(entry.get("endpoints") or [])

    def api_cap(value) -> dict:
        return lib.capability(value, SOURCE, "high")

    capabilities = {
        "chat": api_cap("chat" in endpoints),
        "embeddings": api_cap("embed" in endpoints),
        "rerank": api_cap("rerank" in endpoints),
    }

    limits = None
    context = entry.get("context_length")
    if context:
        limits = {"contextTokens": int(context), "maxOutputTokens": None}

    return {
        "id": model_id,
        "providerModelId": model_id,
        "displayName": model_id,
        "costClass": "trial",
        "pricing": None,
        "limits": limits,
        "capabilities": capabilities,
        "status": "available",
        "source": SOURCE,
        "lastChecked": lib.now_iso(),
    }


def main() -> int:
    key = lib.optional_key("COHERE_API_KEY_FREE", "cohere")
    if key is None:
        return 0

    entries = fetch_all(key)
    if not entries:
        raise SystemExit("cohere: models API returned no data; aborting.")

    models = [m for m in (build_model(e) for e in entries) if m]
    lib.finish("cohere", models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
