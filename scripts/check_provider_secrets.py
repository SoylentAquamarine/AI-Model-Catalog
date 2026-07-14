#!/usr/bin/env python3
"""Check which provider API-key secrets are available to a workflow.

This script never prints secret values. It only reports configured/missing status.
"""

from __future__ import annotations

import os

SECRET_NAMES = [
    "CEREBRAS_API_KEY_FREE",
    "CLOUDFLARE_API_KEY_FREE",
    "CLOUDFLARE_ACCOUNT_ID",
    "COHERE_API_KEY_FREE",
    "GEMINI_API_KEY_FREE",
    "GROQ_API_KEY_FREE",
    "HUGGINGFACE_API_KEY_FREE",
    "MISTRAL_API_KEY_FREE",
    "OPENROUTER_API_KEY_FREE",
    "POLLINATIONS_API_KEY_FREE",
    "SAMBANOVA_API_KEY_FREE",
]


def main() -> int:
    configured = []
    missing = []

    for name in SECRET_NAMES:
        if os.environ.get(name):
            configured.append(name)
        else:
            missing.append(name)

    print("Provider free-key secret status:")
    for name in configured:
        print(f"  configured: {name}")
    for name in missing:
        print(f"  missing:    {name}")

    print(f"Configured {len(configured)} of {len(SECRET_NAMES)} free-key secrets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
