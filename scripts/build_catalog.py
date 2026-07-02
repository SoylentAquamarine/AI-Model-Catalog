#!/usr/bin/env python3
"""Print a simple provider/model summary.

MVP note: provider files under /providers are the public catalog.
This script intentionally does not generate extra /data files yet.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = ROOT / "providers"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    provider_count = 0
    model_count = 0

    for path in sorted(PROVIDERS.glob("*.json")):
        provider_count += 1
        provider_file = read_json(path)
        models = provider_file.get("models", [])
        model_count += len(models)
        provider_id = provider_file.get("provider", {}).get("id", path.stem)
        print(f"{provider_id}: {len(models)} models")

    print(f"Provider summary: {provider_count} providers, {model_count} models.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
