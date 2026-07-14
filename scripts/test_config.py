#!/usr/bin/env python3
"""Configuration for the capability test harness (scripts/test_capabilities.py).

Everything a maintainer is likely to tune lives here: which capabilities are
probed, and how hard each provider may be hit.

Cooldown model: `cooldownSeconds` is the minimum gap between successive MODEL
rounds against the same provider. A model's probe burst (its few capability
calls) runs together, then the provider rests for its cooldown before the next
model. The scheduler interleaves providers, so while one rests others run.

Some providers genuinely need a long cooldown (low free-tier RPM); those get up
to 300s here. High-volume providers get a few seconds so their large model lists
still finish within a weekly run. Adjust freely as real limits become clear.
"""

from __future__ import annotations

# ---- Capability probe policy -------------------------------------------------
CORE_CAPABILITIES = ("chat", "json", "streaming", "tools", "vision")

# Probed on every model (all share the /chat/completions endpoint, cheap):
ALWAYS_PROBE = ("chat", "json", "streaming")

# Probed only where a provider hint suggests support (they need special request
# shapes and are otherwise likely to just fail — saves tokens):
HINT_GATED = ("tools", "vision")

# Values in a hint that count as "worth probing":
POSITIVE_HINTS = {True, "likely", "partial"}

# ---- Timing defaults ---------------------------------------------------------
DEFAULT_COOLDOWN_SECONDS = 30
INTER_PROBE_DELAY_SECONDS = 1.5   # default gap between probes within one model's burst
DEFAULT_MAX_MINUTES = 300         # global wall-clock budget guard for a run
# When a provider returns http_429 (rate limit) during a model's burst, its next
# model round is pushed out by this penalty on top of its normal cooldown.
RATE_LIMIT_PENALTY_SECONDS = 90

# ---- Per-provider config -----------------------------------------------------
# keyEnv: environment variable holding that provider's free key (None = keyless).
# apiBaseVars: {placeholder: ENV_VAR} substituted into apiBase before calling.
# interProbeDelaySeconds: override the burst spacing for rate-sensitive providers.
PROVIDERS: dict[str, dict] = {
    "cerebras":     {"keyEnv": "CEREBRAS_API_KEY_FREE",    "cooldownSeconds": 300},
    "cloudflare":   {"keyEnv": "CLOUDFLARE_API_KEY_FREE",  "cooldownSeconds": 10,
                     "apiBaseVars": {"account_id": "CLOUDFLARE_ACCOUNT_ID"}},
    "cohere":       {"keyEnv": "COHERE_API_KEY_FREE",      "cooldownSeconds": 60},
    # Gemini's free tier is strict on RPM; space the burst out and rest longer.
    "gemini":       {"keyEnv": "GEMINI_API_KEY_FREE",      "cooldownSeconds": 90,
                     "interProbeDelaySeconds": 8},
    "groq":         {"keyEnv": "GROQ_API_KEY_FREE",        "cooldownSeconds": 15},
    "huggingface":  {"keyEnv": "HUGGINGFACE_API_KEY_FREE", "cooldownSeconds": 5},
    "mistral":      {"keyEnv": "MISTRAL_API_KEY_FREE",     "cooldownSeconds": 15},
    "openrouter":   {"keyEnv": "OPENROUTER_API_KEY_FREE",  "cooldownSeconds": 15},
    "pollinations": {"keyEnv": None,                       "cooldownSeconds": 15},
    "sambanova":    {"keyEnv": "SAMBANOVA_API_KEY_FREE",   "cooldownSeconds": 300},
}


def provider_config(provider_id: str) -> dict:
    return PROVIDERS.get(provider_id, {"keyEnv": None, "cooldownSeconds": DEFAULT_COOLDOWN_SECONDS})


def inter_probe_delay(provider_id: str) -> float:
    return provider_config(provider_id).get("interProbeDelaySeconds", INTER_PROBE_DELAY_SECONDS)


def capabilities_for(hints: dict | None) -> list[str]:
    """Which capabilities to probe for a model, given its provider-declared hints."""
    hints = hints or {}
    caps = list(ALWAYS_PROBE)
    for cap in HINT_GATED:
        entry = hints.get(cap)
        value = entry.get("value") if isinstance(entry, dict) else entry
        if value in POSITIVE_HINTS:
            caps.append(cap)
    return caps
