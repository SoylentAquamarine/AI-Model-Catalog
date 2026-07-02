#!/usr/bin/env python3
"""Validate catalog files against the published JSON Schemas.

With the `jsonschema` package installed (CI does this), files are validated
against schema/provider.schema.json and schema/catalog-index.schema.json.
Without it, a built-in structural check covers the required fields and enums
so the script still catches real problems when run locally with no deps.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_DIR = ROOT / "providers"
SCHEMA_DIR = ROOT / "schema"
INDEX_PATH = ROOT / "catalog-index.json"

API_TYPES = {"openai-compatible", "anthropic", "gemini", "ollama"}
AUTH_SCHEMES = {"bearer", "header", "query", "none"}
COST_CLASSES = {"free", "paid", "trial", "local", "unknown"}
CAP_VALUES = {True, False, "unknown", "likely", "partial"}
STATUSES = {"available", "preview", "deprecated", "unknown"}


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def structural_check_provider(data: dict, errors: list[str], where: str) -> None:
    for key in ("schemaVersion", "provider", "models"):
        if key not in data:
            errors.append(f"{where}: missing required key '{key}'")
            return

    provider = data["provider"]
    for key in ("id", "displayName", "apiBase", "apiType"):
        if not provider.get(key):
            errors.append(f"{where}: provider.{key} is missing or empty")
    if provider.get("apiType") not in API_TYPES:
        errors.append(f"{where}: provider.apiType {provider.get('apiType')!r} not in {sorted(API_TYPES)}")
    auth = provider.get("auth")
    if auth is not None and auth.get("scheme") not in AUTH_SCHEMES:
        errors.append(f"{where}: provider.auth.scheme {auth.get('scheme')!r} not in {sorted(AUTH_SCHEMES)}")

    for i, model in enumerate(data["models"]):
        label = f"{where}: models[{i}]"
        if not model.get("id"):
            errors.append(f"{label}: missing id")
        if model.get("costClass") not in COST_CLASSES:
            errors.append(f"{label}: costClass {model.get('costClass')!r} not in {sorted(COST_CLASSES)}")
        if model.get("status", "available") not in STATUSES:
            errors.append(f"{label}: status {model.get('status')!r} not in {sorted(STATUSES)}")
        for cap_name, cap in (model.get("capabilities") or {}).items():
            if not isinstance(cap, dict) or "value" not in cap:
                errors.append(f"{label}: capability '{cap_name}' must be an object with 'value'")
            elif cap["value"] not in CAP_VALUES:
                errors.append(f"{label}: capability '{cap_name}' value {cap['value']!r} invalid")


def structural_check_index(data: dict, errors: list[str]) -> None:
    for key in ("schemaVersion", "generatedAt", "providers"):
        if key not in data:
            errors.append(f"catalog-index.json: missing required key '{key}'")
            return
    for i, entry in enumerate(data["providers"]):
        for key in ("id", "file", "apiType"):
            if not entry.get(key):
                errors.append(f"catalog-index.json: providers[{i}].{key} missing or empty")
        file_path = ROOT / entry.get("file", "")
        if entry.get("file") and not file_path.exists():
            errors.append(f"catalog-index.json: providers[{i}].file {entry['file']!r} does not exist")


def main() -> int:
    errors: list[str] = []

    try:
        import jsonschema  # type: ignore
        have_jsonschema = True
    except ImportError:
        have_jsonschema = False
        print("note: jsonschema not installed; using built-in structural checks.")

    provider_schema = load_json(SCHEMA_DIR / "provider.schema.json")
    index_schema = load_json(SCHEMA_DIR / "catalog-index.schema.json")

    provider_paths = sorted(PROVIDERS_DIR.glob("*.json")) if PROVIDERS_DIR.exists() else []
    if not provider_paths:
        errors.append("no provider files found under providers/")

    for path in provider_paths:
        where = str(path.relative_to(ROOT))
        try:
            data = load_json(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{where}: invalid JSON: {exc}")
            continue
        if have_jsonschema:
            for err in jsonschema.Draft202012Validator(provider_schema).iter_errors(data):
                errors.append(f"{where}: {'/'.join(str(p) for p in err.path) or '(root)'}: {err.message}")
        else:
            structural_check_provider(data, errors, where)
        stem_id = data.get("provider", {}).get("id")
        if stem_id and stem_id != path.stem:
            errors.append(f"{where}: provider.id {stem_id!r} does not match filename")

    if INDEX_PATH.exists():
        try:
            index_data = load_json(INDEX_PATH)
            if have_jsonschema:
                for err in jsonschema.Draft202012Validator(index_schema).iter_errors(index_data):
                    errors.append(f"catalog-index.json: {'/'.join(str(p) for p in err.path) or '(root)'}: {err.message}")
            else:
                structural_check_index(index_data, errors)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"catalog-index.json: invalid JSON: {exc}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validation FAILED with {len(errors)} error(s).", file=sys.stderr)
        return 1

    checked = len(provider_paths) + (1 if INDEX_PATH.exists() else 0)
    mode = "jsonschema" if have_jsonschema else "structural"
    print(f"Validation passed: {checked} file(s), {mode} mode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
