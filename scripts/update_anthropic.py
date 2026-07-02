#!/usr/bin/env python3
"""Update providers/anthropic.json from the Anthropic models API.

Source: https://api.anthropic.com/v1/models — requires an API key
(ANTHROPIC_API_KEY_FREE) sent as the x-api-key header plus an
anthropic-version header. Returns model ids and display names; pricing and
capabilities are not machine-readable there, so they stay honest (empty).
"""

from __future__ import annotations

import urllib.parse

import catalog_lib as lib

MODELS_URL = "https://api.anthropic.com/v1/models"
SOURCE = "anthropic_models_api"
API_VERSION = "2023-06-01"


def fetch_all(key: str) -> list[dict]:
    headers = {"x-api-key": key, "anthropic-version": API_VERSION}
    entries: list[dict] = []
    after_id = None
    while True:
        params = {"limit": "100"}
        if after_id:
            params["after_id"] = after_id
        payload = lib.http_get_json(
            f"{MODELS_URL}?{urllib.parse.urlencode(params)}", headers=headers
        )
        page = payload.get("data") or []
        entries.extend(page)
        if not payload.get("has_more") or not page:
            return entries
        after_id = page[-1].get("id")


def main() -> int:
    key = lib.optional_key("ANTHROPIC_API_KEY_FREE", "anthropic")
    if key is None:
        return 0

    entries = fetch_all(key)
    if not entries:
        raise SystemExit("anthropic: models API returned no data; aborting.")

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
                # The Anthropic API has no free tier (provider_docs).
                "costClass": "paid",
                "pricing": None,
                "limits": None,
                "capabilities": {},
                "status": "available",
                "source": SOURCE,
                "lastChecked": lib.now_iso(),
            }
        )

    lib.finish("anthropic", models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
