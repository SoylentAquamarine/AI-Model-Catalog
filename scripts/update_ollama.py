#!/usr/bin/env python3
"""Ollama catalog note.

Ollama is a local runtime: which models exist depends entirely on what each
user has pulled onto their own machine, so a public catalog cannot list them.
providers/ollama.json intentionally publishes only the connection contract
(apiType, apiBase, auth: none). Consumers should enumerate models at runtime
from the local instance (GET /api/tags).

This script exists so "one updater per provider" stays uniform; it verifies
the file loads and changes nothing.
"""

from __future__ import annotations

import catalog_lib as lib


def main() -> int:
    data = lib.load_provider("ollama")
    provider_id = data.get("provider", {}).get("id")
    if provider_id != "ollama":
        raise SystemExit("ollama: providers/ollama.json has unexpected content.")
    print("ollama: local runtime, no public model list; connection contract kept as-is.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
