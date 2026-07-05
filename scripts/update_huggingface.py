#!/usr/bin/env python3
"""Update providers/huggingface.json from the HF Inference Providers router.

Source: https://router.huggingface.co/v1/models — requires
HUGGINGFACE_API_KEY_FREE. Hugging Face accounts include a recurring monthly
free inference allowance (a standing free tier that resets, not a one-time
trial), so models are classed as free. Verified against HF docs, 2026-07.
"""

from __future__ import annotations

import catalog_lib as lib


def main() -> int:
    return lib.update_openai_style(
        provider_id="huggingface",
        models_url="https://router.huggingface.co/v1/models",
        env_var="HUGGINGFACE_API_KEY_FREE",
        cost_class="free",
        source="huggingface_router_models_api",
    )


if __name__ == "__main__":
    raise SystemExit(main())
