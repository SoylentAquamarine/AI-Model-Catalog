#!/usr/bin/env python3
"""Build catalog-index.json and capabilities.json from the provider files.

The index is the consumer entry point: fetch it first, compare generatedAt
to your last sync, then fetch the provider files it lists. capabilities.json
summarises, per capability, how many models have that capability *verified by a
live test* (source tested_by_catalog, value true) and lists their ids.
"""

from __future__ import annotations

import json
from pathlib import Path

import catalog_lib as lib

INDEX_SCHEMA_VERSION = "1.4.0"
INDEX_PATH = lib.ROOT / "catalog-index.json"
CAPABILITIES_PATH = lib.ROOT / "capabilities.json"
TESTED_SOURCE = "tested_by_catalog"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _verified(cap: dict) -> bool:
    """True only for a live-tested, confirmed-supported capability."""
    return (
        isinstance(cap, dict)
        and cap.get("value") is True
        and cap.get("source") == TESTED_SOURCE
    )


def main() -> int:
    providers = []
    model_count = 0
    # capability -> list of "<provider>:<modelId>" with verified support
    cap_models: dict[str, list[str]] = {}

    for path in sorted(lib.PROVIDERS_DIR.glob("*.json")):
        data = read_json(path)
        provider = data.get("provider", {})
        pid = provider.get("id", path.stem)
        models = data.get("models", [])
        # Free-only catalog: every published model is costClass=free, so
        # freeModelCount always equals modelCount. Kept for consumer clarity.
        free_models = sum(1 for m in models if m.get("costClass") == "free")
        model_count += len(models)

        for m in models:
            for cap_name, cap in (m.get("capabilities") or {}).items():
                if _verified(cap):
                    cap_models.setdefault(cap_name, []).append(f"{pid}:{m['id']}")

        providers.append(
            {
                "id": pid,
                "file": f"providers/{path.name}",
                "apiType": provider.get("apiType"),
                "modelCount": len(models),
                "freeModelCount": free_models,
                "lastChecked": provider.get("lastChecked"),
            }
        )
        print(f"{pid}: {len(models)} free models")

    capability_summary = {c: len(ids) for c, ids in sorted(cap_models.items())}

    index = {
        "schemaVersion": INDEX_SCHEMA_VERSION,
        "generatedAt": lib.now_iso(),
        "totalModels": model_count,
        "totalFreeModels": model_count,
        "capabilitySummary": capability_summary,
        "providers": sorted(providers, key=lambda p: p["id"]),
    }
    with INDEX_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")

    capabilities = {
        "generatedAt": index["generatedAt"],
        "note": "Counts reflect capabilities verified by live test (source tested_by_catalog).",
        "capabilities": {
            c: {"count": len(ids), "models": sorted(ids)}
            for c, ids in sorted(cap_models.items())
        },
    }
    with CAPABILITIES_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(capabilities, f, indent=2, ensure_ascii=False)
        f.write("\n")

    verified_total = sum(capability_summary.values())
    print(f"Provider summary: {len(providers)} providers, {model_count} models.")
    print(f"Verified capability entries: {verified_total} across {len(capability_summary)} capabilities.")
    print(f"Wrote {INDEX_PATH.relative_to(lib.ROOT)} and {CAPABILITIES_PATH.relative_to(lib.ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
