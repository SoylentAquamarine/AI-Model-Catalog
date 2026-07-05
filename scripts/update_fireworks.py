#!/usr/bin/env python3
"""Update providers/fireworks.json from the Fireworks AI models API.

Source: https://api.fireworks.ai/inference/v1/models — requires
FIREWORKS_API_KEY_FREE. New accounts get ~$1 in free starter credits (usable
without a card, capped at 10 RPM), then pay-as-you-go — a trial, not a
standing free tier. Verified 2026-07.
"""

from __future__ import annotations

import catalog_lib as lib


def main() -> int:
    return lib.update_openai_style(
        provider_id="fireworks",
        models_url="https://api.fireworks.ai/inference/v1/models",
        env_var="FIREWORKS_API_KEY_FREE",
        cost_class="trial",
        source="fireworks_models_api",
    )


if __name__ == "__main__":
    raise SystemExit(main())
