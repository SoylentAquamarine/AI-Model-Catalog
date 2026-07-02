#!/usr/bin/env python3
"""Update providers/groq.json from the Groq models API.

Source: https://api.groq.com/openai/v1/models — requires an API key
(GROQ_API_KEY_FREE). OpenAI-compatible shape; some entries include context
window and max completion tokens.
"""

from __future__ import annotations

import catalog_lib as lib

MODELS_URL = "https://api.groq.com/openai/v1/models"
SOURCE = "groq_models_api"


def main() -> int:
    key = lib.optional_key("GROQ_API_KEY_FREE", "groq")
    if key is None:
        return 0

    payload = lib.http_get_json(MODELS_URL, headers={"Authorization": f"Bearer {key}"})
    entries = payload.get("data") or []
    if not entries:
        raise SystemExit("groq: models API returned no data; aborting.")

    models = []
    for entry in entries:
        model_id = entry.get("id")
        if not model_id:
            continue

        limits = None
        context = entry.get("context_window")
        max_output = entry.get("max_completion_tokens")
        if context or max_output:
            limits = {"contextTokens": context, "maxOutputTokens": max_output}

        status = "available" if entry.get("active", True) else "deprecated"

        models.append(
            {
                "id": model_id,
                "providerModelId": model_id,
                "displayName": model_id,
                # Groq documents a rate-limited free tier covering its API models.
                "costClass": "free",
                "pricing": None,
                "limits": limits,
                "capabilities": {},
                "status": status,
                "source": SOURCE,
                "lastChecked": lib.now_iso(),
            }
        )

    lib.finish("groq", models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
