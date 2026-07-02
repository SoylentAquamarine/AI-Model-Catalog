#!/usr/bin/env python3
"""Update providers/sambanova.json from the SambaNova Cloud models API.

Source: https://api.sambanova.ai/v1/models — requires SAMBANOVA_API_KEY_FREE.
SambaNova documents a rate-limited free tier on SambaNova Cloud.
"""

from __future__ import annotations

import catalog_lib as lib


def main() -> int:
    return lib.update_openai_style(
        provider_id="sambanova",
        models_url="https://api.sambanova.ai/v1/models",
        env_var="SAMBANOVA_API_KEY_FREE",
        cost_class="free",
        source="sambanova_models_api",
    )


if __name__ == "__main__":
    raise SystemExit(main())
