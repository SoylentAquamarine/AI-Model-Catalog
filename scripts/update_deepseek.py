#!/usr/bin/env python3
"""Update providers/deepseek.json from the DeepSeek models API.

Source: https://api.deepseek.com/v1/models — requires DEEPSEEK_API_KEY_FREE.
The DeepSeek API is pay-as-you-go (no documented free tier).
"""

from __future__ import annotations

import catalog_lib as lib


def main() -> int:
    return lib.update_openai_style(
        provider_id="deepseek",
        models_url="https://api.deepseek.com/v1/models",
        env_var="DEEPSEEK_API_KEY_FREE",
        cost_class="paid",
        source="deepseek_models_api",
    )


if __name__ == "__main__":
    raise SystemExit(main())
