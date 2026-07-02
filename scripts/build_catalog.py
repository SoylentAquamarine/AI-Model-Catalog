#!/usr/bin/env python3
"""Build merged catalog and simple indexes from provider files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROVIDERS = DATA / "providers"
INDEXES = DATA / "indexes"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def cap_value(model: dict, capability: str):
    cap = model.get("capabilities", {}).get(capability)
    if isinstance(cap, dict):
        return cap.get("value")
    return None


def matches_cap(model: dict, capability: str) -> bool:
    return cap_value(model, capability) in (True, "likely", "partial")


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    providers: list[str] = []
    models: list[dict] = []

    for path in sorted(PROVIDERS.glob("*.json")):
        provider_file = read_json(path)
        provider_id = provider_file.get("provider", {}).get("id", path.stem)
        providers.append(provider_id)
        for model in provider_file.get("models", []):
            model.setdefault("providerId", provider_id)
            models.append(model)

    write_json(DATA / "catalog.json", {
        "schemaVersion": "0.1.0",
        "generatedAt": now,
        "providers": providers,
        "models": models,
    })

    free_models = [m for m in models if m.get("cost", {}).get("class") == "free"]
    write_json(DATA / "free.json", {
        "schemaVersion": "0.1.0",
        "generatedAt": now,
        "models": free_models,
    })

    indexes = {
        "free-chat.json": [m for m in free_models if matches_cap(m, "chat")],
        "free-json.json": [m for m in free_models if matches_cap(m, "json")],
        "free-code.json": [m for m in free_models if matches_cap(m, "code")],
        "vision.json": [m for m in models if matches_cap(m, "vision")],
        "embeddings.json": [m for m in models if matches_cap(m, "embeddings")],
    }

    for filename, index_models in indexes.items():
        write_json(INDEXES / filename, {
            "schemaVersion": "0.1.0",
            "generatedAt": now,
            "models": index_models,
        })

    print(f"Built catalog with {len(models)} models from {len(providers)} providers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
