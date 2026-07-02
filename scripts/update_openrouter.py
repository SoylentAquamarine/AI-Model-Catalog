#!/usr/bin/env python3
"""Update providers/openrouter.json from the public OpenRouter models API.

Source: https://openrouter.ai/api/v1/models — no API key required.
This is the richest public source: pricing, context limits, modalities,
and supported parameters per model.
"""

from __future__ import annotations

import catalog_lib as lib

MODELS_URL = "https://openrouter.ai/api/v1/models"
SOURCE = "openrouter_models_api"


def price_per_m_tokens(raw) -> float | None:
    """OpenRouter prices are USD per single token, as strings. Negative means dynamic/unpriced."""
    if raw in (None, ""):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value < 0:
        return None
    return round(value * 1_000_000, 6)


def build_model(entry: dict) -> dict:
    pricing = entry.get("pricing") or {}
    architecture = entry.get("architecture") or {}
    top = entry.get("top_provider") or {}
    supported = set(entry.get("supported_parameters") or [])
    input_modalities = set(architecture.get("input_modalities") or [])
    output_modalities = set(architecture.get("output_modalities") or [])

    input_per_m = price_per_m_tokens(pricing.get("prompt"))
    output_per_m = price_per_m_tokens(pricing.get("completion"))
    is_free = input_per_m == 0 and output_per_m == 0
    has_price = input_per_m is not None or output_per_m is not None

    def api_cap(value) -> dict:
        return lib.capability(value, SOURCE, "high")

    capabilities = {
        "chat": api_cap(True),
        "vision": api_cap("image" in input_modalities),
        "tools": api_cap("tools" in supported),
        "json": api_cap(bool({"response_format", "structured_outputs"} & supported)),
        "reasoning": api_cap(bool({"reasoning", "include_reasoning"} & supported)),
        "streaming": lib.capability(
            True,
            "provider_docs",
            "high",
            "OpenRouter documents streaming support for all models.",
        ),
    }
    if "audio" in input_modalities:
        capabilities["audio_input"] = api_cap(True)
    if "image" in output_modalities:
        capabilities["image_generation"] = api_cap(True)

    model = {
        "id": entry["id"],
        "providerModelId": entry["id"],
        "displayName": entry.get("name") or entry["id"],
        "costClass": "free" if is_free else ("paid" if has_price else "unknown"),
        "pricing": None,
        "limits": None,
        "capabilities": capabilities,
        "status": "available",
        "source": SOURCE,
        "lastChecked": lib.now_iso(),
    }

    if has_price:
        model["pricing"] = {
            "currency": "USD",
            "inputPerMTokens": input_per_m,
            "outputPerMTokens": output_per_m,
        }

    context = entry.get("context_length") or top.get("context_length")
    max_output = top.get("max_completion_tokens")
    if context or max_output:
        model["limits"] = {
            "contextTokens": context,
            "maxOutputTokens": max_output,
        }

    return model


def main() -> int:
    payload = lib.http_get_json(MODELS_URL)
    entries = payload.get("data") or []
    if not entries:
        raise SystemExit("openrouter: models API returned no data; aborting.")

    models = [build_model(entry) for entry in entries if entry.get("id")]
    lib.finish("openrouter", models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
