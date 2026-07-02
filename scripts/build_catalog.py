#!/usr/bin/env python3
"""Build catalog-index.json from the provider files and print a summary.

The index is the consumer entry point: fetch it first, compare generatedAt
to your last sync, then fetch the provider files it lists.
"""

from __future__ import annotations

import json
from pathlib import Path

import catalog_lib as lib

INDEX_SCHEMA_VERSION = "1.1.0"
INDEX_PATH = lib.ROOT / "catalog-index.json"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    providers = []
    model_count = 0
    free_count = 0

    for path in sorted(lib.PROVIDERS_DIR.glob("*.json")):
        data = read_json(path)
        provider = data.get("provider", {})
        models = data.get("models", [])
        free_models = sum(1 for m in models if m.get("costClass") == "free")
        model_count += len(models)
        free_count += free_models
        providers.append(
            {
                "id": provider.get("id", path.stem),
                "file": f"providers/{path.name}",
                "apiType": provider.get("apiType"),
                "modelCount": len(models),
                "freeModelCount": free_models,
                "lastChecked": provider.get("lastChecked"),
            }
        )
        print(f"{provider.get('id', path.stem)}: {len(models)} models ({free_models} free)")

    index = {
        "schemaVersion": INDEX_SCHEMA_VERSION,
        "generatedAt": lib.now_iso(),
        "totalModels": model_count,
        "totalFreeModels": free_count,
        "providers": sorted(providers, key=lambda p: p["id"]),
    }

    with INDEX_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Provider summary: {len(providers)} providers, {model_count} models.")
    print(f"Wrote {INDEX_PATH.relative_to(lib.ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
