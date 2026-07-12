#!/usr/bin/env python3
"""Capability test harness for the AI Model Catalog.

Runs tiny live probes (scripts/probes.py) against free models to VERIFY what
they can do, and records only tested results as `tested_by_catalog`. Designed to
run weekly without flooding token usage:

- Interleaves providers, honouring each provider's cooldown (scripts/test_config.py)
  between successive model rounds.
- Rotates least-recently-tested models first, so a global time budget
  (--max-minutes) never starves any model over successive weekly runs.
- chat/json/streaming are probed on every model; tools/vision only where a
  provider hint suggests support.

Results go to state/tested_capabilities.json (the source of truth, also read by
catalog_lib.finish() and build_catalog.py) and are written back into the
provider files' `capabilities`. Rotation timestamps live in
state/capability_test_state.json. Secrets are never printed.

Usage:
    python test_capabilities.py --dry-run
    python test_capabilities.py --provider pollinations --once
    python test_capabilities.py --max-minutes 60
"""

from __future__ import annotations

import argparse
import copy
import os
import time

import catalog_lib as lib
import probes
import test_config as cfg

ROTATION_PATH = lib.STATE_DIR / "capability_test_state.json"
DIAG_PATH = lib.STATE_DIR / "test_diagnostics.json"
TESTED_SOURCE = "tested_by_catalog"


def _load_json(path, default):
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            import json
            return json.load(f)
    return default


def _save_json(path, data):
    import json
    lib.STATE_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def _resolve_provider(provider: dict, conf: dict) -> dict | None:
    """Return a provider copy with apiBase placeholders substituted, or None if
    a required substitution variable is missing from the environment."""
    resolved = copy.deepcopy(provider)
    base = resolved["apiBase"]
    for placeholder, env_var in (conf.get("apiBaseVars") or {}).items():
        val = os.environ.get(env_var, "").strip()
        if not val:
            return None
        base = base.replace("{" + placeholder + "}", val)
    resolved["apiBase"] = base
    return resolved


def _hints_for(model: dict) -> dict:
    # After finish() runs, declared flags live in `hints`; before migration they
    # may still be under `capabilities`. Use whichever is present for gating.
    return model.get("hints") or model.get("capabilities") or {}


def _cap_entry(value: bool) -> dict:
    return {
        "value": value,
        "source": TESTED_SOURCE,
        "confidence": "high",
        "lastChecked": lib.now_iso(),
    }


def gather(only_provider: str | None, limit: int | None):
    """Build per-provider work lists. Returns (work, skipped).

    work: {provider_id: {"provider": resolved, "key": key, "cooldown": s,
                         "models": [(model, [caps])...] ordered oldest-tested first}}
    """
    rotation = _load_json(ROTATION_PATH, {})
    work: dict[str, dict] = {}
    skipped: list[str] = []

    for path in sorted(lib.PROVIDERS_DIR.glob("*.json")):
        pid = path.stem
        if only_provider and pid != only_provider:
            continue
        data = lib.load_provider(pid)
        conf = cfg.provider_config(pid)

        key = None
        if conf.get("keyEnv"):
            key = os.environ.get(conf["keyEnv"], "").strip() or None
            if key is None:
                skipped.append(f"{pid} (no {conf['keyEnv']})")
                continue

        resolved = _resolve_provider(data["provider"], conf)
        if resolved is None:
            skipped.append(f"{pid} (unresolved apiBase vars)")
            continue

        prov_rotation = rotation.get(pid, {})
        models = data.get("models", [])
        # Oldest-tested first; never-tested ("") sorts before any timestamp.
        models = sorted(models, key=lambda m: prov_rotation.get(m["id"], ""))
        if limit:
            models = models[:limit]

        entries = [(m, cfg.capabilities_for(_hints_for(m))) for m in models]
        work[pid] = {
            "provider": resolved,
            "key": key,
            "cooldown": conf.get("cooldownSeconds", cfg.DEFAULT_COOLDOWN_SECONDS),
            "interProbeDelay": cfg.inter_probe_delay(pid),
            "models": entries,
        }
    return work, skipped, rotation


def test_one(provider: dict, model: dict, key: str | None, caps: list[str], delay: float):
    """Run a model's probe burst.

    Returns (verified, probe_log):
      verified:  {cap: cap_entry} for pass/fail only (publish-eligible).
      probe_log: {cap: {outcome, detail, at}} for EVERY probe, errors included,
                 so nothing is ever guessed -- the raw last result is on record.
    """
    verified: dict[str, dict] = {}
    probe_log: dict[str, dict] = {}
    for i, cap in enumerate(caps):
        if i:
            time.sleep(delay)
        outcome, detail = probes.run_probe(provider, model, cap, key)
        probe_log[cap] = {"outcome": outcome, "detail": detail, "at": lib.now_iso()}
        if outcome == probes.PASS:
            verified[cap] = _cap_entry(True)
        elif outcome == probes.FAIL:
            verified[cap] = _cap_entry(False)
        # ERROR -> not verified; the probe_log still records why.
    return verified, probe_log


def _new_diag() -> dict:
    return {
        "modelsTested": 0,
        "probes": 0,
        "outcomes": {probes.PASS: 0, probes.FAIL: 0, probes.ERROR: 0},
        "byDetail": {},
        "byCapability": {},
    }


def _record_diag(diag: dict, cap: str, outcome: str, detail: str) -> None:
    diag["probes"] += 1
    diag["outcomes"][outcome] = diag["outcomes"].get(outcome, 0) + 1
    diag["byDetail"][detail] = diag["byDetail"].get(detail, 0) + 1
    per_cap = diag["byCapability"].setdefault(cap, {probes.PASS: 0, probes.FAIL: 0, probes.ERROR: 0})
    per_cap[outcome] = per_cap.get(outcome, 0) + 1


def run(work: dict, rotation: dict, max_minutes: float, once: bool):
    store = lib.load_tested_store()
    diagnostics: dict[str, dict] = {}
    deadline = time.monotonic() + max_minutes * 60
    next_ready = {pid: 0.0 for pid in work}
    cursor = {pid: 0 for pid in work}
    touched: set[str] = set()
    models_done = 0
    probes_done = 0

    def remaining(pid):
        return len(work[pid]["models"]) - cursor[pid]

    while True:
        now = time.monotonic()
        if now >= deadline:
            print("Time budget reached; stopping.")
            break
        active = [pid for pid in work if remaining(pid) > 0]
        if not active:
            break
        ready = [pid for pid in active if next_ready[pid] <= now]
        if not ready:
            wake = min(next_ready[pid] for pid in active)
            time.sleep(min(max(wake - now, 0.1), 5.0, max(deadline - now, 0.1)))
            continue

        for pid in ready:
            if time.monotonic() >= deadline:
                break
            w = work[pid]
            model, caps = w["models"][cursor[pid]]
            cursor[pid] += 1
            verified, probe_log = test_one(w["provider"], model, w["key"], caps, w["interProbeDelay"])
            probes_done += len(caps)
            models_done += 1

            entry = store.setdefault(pid, {}).setdefault(model["id"], {})
            entry.setdefault("capabilities", {}).update(verified)
            entry["probes"] = probe_log  # raw last result of every probe, errors included
            entry["lastTested"] = lib.now_iso()
            rotation.setdefault(pid, {})[model["id"]] = lib.now_iso()
            # Adaptive backoff: if this burst got rate-limited, rest longer.
            rate_limited = any(r["detail"] == "http_429" for r in probe_log.values())
            penalty = cfg.RATE_LIMIT_PENALTY_SECONDS if rate_limited else 0
            next_ready[pid] = time.monotonic() + w["cooldown"] + penalty
            touched.add(pid)

            diag = diagnostics.setdefault(pid, _new_diag())
            diag["modelsTested"] += 1
            for cap, r in probe_log.items():
                _record_diag(diag, cap, r["outcome"], r["detail"])

            summary = " ".join(f"{c}={r['outcome']}({r['detail']})" for c, r in probe_log.items())
            print(f"  {pid}: {model['id']}  {summary}")

        if once:
            break

    lib.save_tested_store(store)
    _save_json(ROTATION_PATH, rotation)
    _save_json(DIAG_PATH, {"generatedAt": lib.now_iso(), "providers": diagnostics})
    _write_back(store, touched)
    _print_diag_summary(diagnostics)
    return models_done, probes_done


def _print_diag_summary(diagnostics: dict) -> None:
    print("\nComms diagnostics (this run):")
    print(f"  {'provider':12} {'models':>6} {'pass':>5} {'fail':>5} {'error':>5}  top error details")
    for pid in sorted(diagnostics):
        d = diagnostics[pid]
        o = d["outcomes"]
        err_details = {k: v for k, v in d["byDetail"].items()
                       if k not in ("ok", "empty", "unsupported_param", "bad_json", "no_tool_call", "no_stream")}
        top = ", ".join(f"{k}:{v}" for k, v in sorted(err_details.items(), key=lambda x: -x[1])[:4])
        print(f"  {pid:12} {d['modelsTested']:6} {o.get('pass',0):5} {o.get('fail',0):5} {o.get('error',0):5}  {top}")


def _write_back(store: dict, touched: set[str]) -> None:
    """Reflect tested capabilities from the store into the provider files."""
    for pid in sorted(touched):
        data = lib.load_provider(pid)
        prov = store.get(pid, {})
        for m in data.get("models", []):
            tested = prov.get(m["id"], {}).get("capabilities")
            if tested:
                m["capabilities"] = tested
        lib.save_provider(pid, data)
        print(f"  wrote tested capabilities into providers/{pid}.json")


def dry_run(work: dict, skipped: list[str]) -> None:
    total_models = total_probes = 0
    print("DRY RUN -- no API calls will be made.\n")
    for pid in sorted(work):
        w = work[pid]
        n = len(w["models"])
        p = sum(len(caps) for _, caps in w["models"])
        total_models += n
        total_probes += p
        print(f"  {pid:12} {n:4} models, ~{p:4} probes, cooldown {w['cooldown']}s")
    print(f"\n  TOTAL: {total_models} models, ~{total_probes} probe calls")
    if skipped:
        print("\n  skipped: " + ", ".join(skipped))


def main() -> int:
    ap = argparse.ArgumentParser(description="AI Model Catalog capability test harness")
    ap.add_argument("--dry-run", action="store_true", help="list planned probes, make no calls")
    ap.add_argument("--provider", help="restrict to a single provider id")
    ap.add_argument("--limit", type=int, help="max models per provider this run")
    ap.add_argument("--once", action="store_true", help="one round per ready provider, then stop")
    ap.add_argument("--max-minutes", type=float, default=cfg.DEFAULT_MAX_MINUTES,
                    help="global wall-clock budget (default from test_config)")
    args = ap.parse_args()

    work, skipped, rotation = gather(args.provider, args.limit)
    if not work:
        print("No providers to test." + (f" skipped: {', '.join(skipped)}" if skipped else ""))
        return 0

    if args.dry_run:
        dry_run(work, skipped)
        return 0

    if skipped:
        print("Skipping (no key / unresolved): " + ", ".join(skipped))
    print(f"Testing {sum(len(w['models']) for w in work.values())} models "
          f"across {len(work)} provider(s); budget {args.max_minutes} min.")
    models_done, probes_done = run(work, rotation, args.max_minutes, args.once)
    print(f"Done: {models_done} models tested, {probes_done} probe calls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
