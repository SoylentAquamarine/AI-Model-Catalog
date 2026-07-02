#!/usr/bin/env python3
"""Update providers/gemini.json from the Google Generative Language models API.

Source: https://generativelanguage.googleapis.com/v1beta/models — requires an
API key (GEMINI_API_KEY_FREE), passed as a query parameter. Returns token
limits and supported generation methods per model, which ground several
capability claims at high confidence.
"""

from __future__ import annotations

import urllib.parse

import catalog_lib as lib

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
SOURCE = "gemini_models_api"


def fetch_all(key: str) -> list[dict]:
    entries: list[dict] = []
    page_token = None
    while True:
        params = {"key": key, "pageSize": "1000"}
        if page_token:
            params["pageToken"] = page_token
        payload = lib.http_get_json(f"{BASE_URL}?{urllib.parse.urlencode(params)}")
        entries.extend(payload.get("models") or [])
        page_token = payload.get("nextPageToken")
        if not page_token:
            return entries


def build_model(entry: dict) -> dict | None:
    name = entry.get("name") or ""
    model_id = name.removeprefix("models/")
    if not model_id:
        return None

    methods = set(entry.get("supportedGenerationMethods") or [])

    def api_cap(value) -> dict:
        return lib.capability(value, SOURCE, "high")

    capabilities = {
        "chat": api_cap("generateContent" in methods),
        "streaming": api_cap("streamGenerateContent" in methods),
        "embeddings": api_cap(bool({"embedContent", "embedText"} & methods)),
    }

    limits = None
    context = entry.get("inputTokenLimit")
    max_output = entry.get("outputTokenLimit")
    if context or max_output:
        limits = {"contextTokens": context, "maxOutputTokens": max_output}

    # Google documents a rate-limited free tier for Gemini/Gemma API models;
    # other families (imagen, veo, ...) are not covered, so stay honest.
    is_free_family = model_id.startswith(("gemini", "gemma"))

    return {
        "id": model_id,
        "providerModelId": name,
        "displayName": entry.get("displayName") or model_id,
        "costClass": "free" if is_free_family else "unknown",
        "pricing": None,
        "limits": limits,
        "capabilities": capabilities,
        "status": "available",
        "source": SOURCE,
        "lastChecked": lib.now_iso(),
    }


def main() -> int:
    key = lib.optional_key("GEMINI_API_KEY_FREE", "gemini")
    if key is None:
        return 0

    entries = fetch_all(key)
    if not entries:
        raise SystemExit("gemini: models API returned no data; aborting.")

    models = [m for m in (build_model(e) for e in entries) if m]
    lib.finish("gemini", models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
