#!/usr/bin/env python3
"""Update providers/cerebras.json from the Cerebras models API.

Source: https://api.cerebras.ai/v1/models — requires CEREBRAS_API_KEY_FREE.
Cerebras documents a rate-limited free tier covering its API models.
"""

from __future__ import annotations

import catalog_lib as lib


def main() -> int:
    return lib.update_openai_style(
        provider_id="cerebras",
        models_url="https://api.cerebras.ai/v1/models",
        env_var="CEREBRAS_API_KEY_FREE",
        cost_class="free",
        source="cerebras_models_api",
    )


if __name__ == "__main__":
    raise SystemExit(main())
