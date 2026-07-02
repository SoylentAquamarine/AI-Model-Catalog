#!/usr/bin/env python3
"""Update providers/pollinations.json from the public Pollinations model list.

Source: https://text.pollinations.ai/models — no API key required.
Pollinations is a free, keyless service; entries expose vision/reasoning/
audio flags that ground capability claims.
"""

from __future__ import annotations

import catalog_lib as lib

MODELS_URL = "https://text.pollinations.ai/models"
SOURCE = "pollinations_models_api"


def build_model(entry: dict) -> dict | None:
    model_id = entry.get("name")
    if not model_id:
        return None

    def api_cap(value) -> dict:
        return lib.capability(bool(value), SOURCE, "high")

    capabilities = {
        "chat": api_cap(True),
        "vision": api_cap(entry.get("vision")),
        "reasoning": api_cap(entry.get("reasoning")),
    }
    if entry.get("audio"):
        capabilities["audio_output"] = api_cap(True)

    return {
        "id": model_id,
        "providerModelId": model_id,
        "displayName": entry.get("description") or model_id,
        "costClass": "free",
        "pricing": None,
        "limits": None,
        "capabilities": capabilities,
        "status": "available",
        "source": SOURCE,
        "lastChecked": lib.now_iso(),
    }


def main() -> int:
    payload = lib.http_get_json(MODELS_URL)
    entries = payload if isinstance(payload, list) else []
    if not entries:
        raise SystemExit("pollinations: models API returned no data; aborting.")

    models = [m for m in (build_model(e) for e in entries) if m]
    lib.finish("pollinations", models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
