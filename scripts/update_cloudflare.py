#!/usr/bin/env python3
"""Update providers/cloudflare.json from the Workers AI model search API.

Source: GET /client/v4/accounts/{account_id}/ai/models/search — requires
BOTH CLOUDFLARE_API_KEY_FREE and CLOUDFLARE_ACCOUNT_ID (the API is
account-scoped). Skips gracefully if either is missing. Workers AI
documents a daily free allocation, so models are classed as free.
"""

from __future__ import annotations

import os
import urllib.parse

import catalog_lib as lib

SOURCE = "cloudflare_models_search_api"

TASK_CAPABILITY = {
    "Text Generation": "chat",
    "Text Embeddings": "embeddings",
    "Text-to-Image": "image_generation",
    "Automatic Speech Recognition": "speech_to_text",
    "Text-to-Speech": "text_to_speech",
    "Translation": None,
    "Summarization": None,
    "Image Classification": None,
    "Object Detection": None,
    "Image-to-Text": "vision",
}


def fetch_all(account_id: str, key: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {key}"}
    base = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/models/search"
    entries: list[dict] = []
    page = 1
    while True:
        params = urllib.parse.urlencode({"per_page": "50", "page": str(page)})
        payload = lib.http_get_json(f"{base}?{params}", headers=headers)
        batch = payload.get("result") or []
        if not batch:
            return entries
        entries.extend(batch)
        page += 1


def build_model(entry: dict) -> dict | None:
    model_id = entry.get("name")
    if not model_id:
        return None

    task = (entry.get("task") or {}).get("name") or ""
    capabilities = {}
    cap_name = TASK_CAPABILITY.get(task)
    if cap_name:
        capabilities[cap_name] = lib.capability(True, SOURCE, "high")

    return {
        "id": model_id,
        "providerModelId": model_id,
        "displayName": model_id,
        "costClass": "free",
        "pricing": None,
        "limits": None,
        "capabilities": capabilities,
        "status": "available",
        "source": SOURCE,
        "lastChecked": lib.now_iso(),
        "notes": f"Workers AI task: {task}" if task else None,
    }


def main() -> int:
    key = lib.optional_key("CLOUDFLARE_API_KEY_FREE", "cloudflare")
    if key is None:
        return 0
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    if not account_id:
        print(
            "cloudflare: CLOUDFLARE_ACCOUNT_ID not configured; "
            "skipping remote update, existing file kept."
        )
        return 0

    entries = fetch_all(account_id, key)
    if not entries:
        raise SystemExit("cloudflare: models search API returned no data; aborting.")

    models = [m for m in (build_model(e) for e in entries) if m]
    lib.finish("cloudflare", models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
