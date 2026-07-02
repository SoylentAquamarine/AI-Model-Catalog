#!/usr/bin/env python3
"""Update providers/together.json from the Together AI models API.

Source: https://api.together.xyz/v1/models — requires TOGETHER_API_KEY_FREE.
The endpoint returns a JSON array with per-model pricing (USD per million
tokens), context length, and a type field (chat, embedding, image, rerank,
...), so cost class comes from real pricing data.
"""

from __future__ import annotations

import catalog_lib as lib

MODELS_URL = "https://api.together.xyz/v1/models"
SOURCE = "together_models_api"

TYPE_CAPABILITY = {
    "chat": "chat",
    "language": "completion",
    "embedding": "embeddings",
    "image": "image_generation",
    "rerank": "rerank",
    "audio": "text_to_speech",
    "transcribe": "speech_to_text",
    "moderation": None,
}


def build_model(entry: dict) -> dict | None:
    model_id = entry.get("id")
    if not model_id:
        return None

    pricing_raw = entry.get("pricing") or {}
    input_per_m = pricing_raw.get("input")
    output_per_m = pricing_raw.get("output")
    has_price = isinstance(input_per_m, (int, float)) or isinstance(output_per_m, (int, float))
    is_free = has_price and not input_per_m and not output_per_m

    pricing = None
    if has_price:
        pricing = {
            "currency": "USD",
            "inputPerMTokens": input_per_m,
            "outputPerMTokens": output_per_m,
        }

    capabilities = {}
    cap_name = TYPE_CAPABILITY.get(entry.get("type") or "")
    if cap_name:
        capabilities[cap_name] = lib.capability(True, SOURCE, "high")

    limits = None
    context = entry.get("context_length")
    if context:
        limits = {"contextTokens": context, "maxOutputTokens": None}

    return {
        "id": model_id,
        "providerModelId": model_id,
        "displayName": entry.get("display_name") or model_id,
        "costClass": "free" if is_free else ("paid" if has_price else "unknown"),
        "pricing": pricing,
        "limits": limits,
        "capabilities": capabilities,
        "status": "available",
        "source": SOURCE,
        "lastChecked": lib.now_iso(),
    }


def main() -> int:
    key = lib.optional_key("TOGETHER_API_KEY_FREE", "together")
    if key is None:
        return 0

    payload = lib.http_get_json(MODELS_URL, headers={"Authorization": f"Bearer {key}"})
    entries = payload if isinstance(payload, list) else (payload.get("data") or [])
    if not entries:
        raise SystemExit("together: models API returned no data; aborting.")

    models = [m for m in (build_model(e) for e in entries) if m]
    lib.finish("together", models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
