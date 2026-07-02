#!/usr/bin/env python3
"""Basic JSON validation for provider catalog files."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECK_DIRS = [ROOT / "providers"]


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    errors: list[str] = []

    for base in CHECK_DIRS:
        if not base.exists():
            errors.append(f"Missing directory: {base}")
            continue
        for path in sorted(base.rglob("*.json")):
            try:
                load_json(path)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Invalid JSON: {path.relative_to(ROOT)}: {exc}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Provider JSON validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
