#!/usr/bin/env python3
"""Update providers/openai.json from the OpenAI models API.

Source: https://api.openai.com/v1/models — requires an API key
(OPENAI_API_KEY_FREE). The endpoint returns model ids only; pricing and
capabilities are not machine-readable there, so this updater records model
presence honestly and leaves capabilities empty rather than guessing.
"""

from __future__ import annotations

import catalog_lib as lib

MODELS_URL = "https://api.openai.com/v1/models"
SOURCE = "openai_models_api"


def main() -> int:
    key = lib.optional_key("OPENAI_API_KEY_FREE", "openai")
    if key is None:
        return 0

    payload = lib.http_get_json(MODELS_URL, headers={"Authorization": f"Bearer {key}"})
    entries = payload.get("data") or []
    if not entries:
        raise SystemExit("openai: models API returned no data; aborting.")

    models = []
    for entry in entries:
        model_id = entry.get("id")
        if not model_id:
            continue
        models.append(
            {
                "id": model_id,
                "providerModelId": model_id,
                "displayName": model_id,
                # No reliable free access on signup: starter credits are not
                # guaranteed, and OpenAI's data-sharing free tier (free daily
                # tokens) requires reaching Usage Tier 1 (~$5 prior spend).
                # Classed as paid; the conditional free option is noted on the
                # provider record. Verified 2026-07.
                "costClass": "paid",
                "pricing": None,
                "limits": None,
                "capabilities": {},
                "status": "available",
                "source": SOURCE,
                "lastChecked": lib.now_iso(),
            }
        )

    lib.finish("openai", models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
