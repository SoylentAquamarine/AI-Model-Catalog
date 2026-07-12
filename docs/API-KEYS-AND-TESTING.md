# API Keys and Testing

This project can use GitHub Actions secrets for provider metadata checks and optional free-tier capability testing.

Do not commit API keys, tokens, raw provider responses containing secrets, or account-specific data.

## Configured Secret Names

The repository may use these GitHub Actions secrets:

```text
CEREBRAS_API_KEY_FREE
CLOUDFLARE_API_KEY_FREE
COHERE_API_KEY_FREE
GEMINI_API_KEY_FREE
GROQ_API_KEY_FREE
HUGGINGFACE_API_KEY_FREE
MISTRAL_API_KEY_FREE
OPENROUTER_API_KEY_FREE
POLLINATIONS_API_KEY_FREE
SAMBANOVA_API_KEY_FREE
TOGETHER_API_KEY_FREE
```

This is a free-only catalog: it uses `*_API_KEY_FREE` (free-tier or keyless) secrets exclusively. There are no paid testing keys — the project never spends money on a provider.

## Capability Test Harness

`scripts/test_capabilities.py` verifies model capabilities with tiny live calls and publishes only
proven results (`source: tested_by_catalog`). See `docs/CAPABILITY-FLAGS.md` for the data model.

```text
Probes (core 5):  chat, json, streaming (every model);  tools, vision (only where a hint suggests support)
Adapters:         one per apiType -- openai-compatible and gemini (scripts/probes.py)
Cadence:          weekly (.github/workflows/test-capabilities.yml, Wed 06:00 UTC) + workflow_dispatch
Cooldown:         per provider (scripts/test_config.py); low-RPM providers up to 300s between model rounds
Budget:           --max-minutes wall-clock guard; least-recently-tested models run first (rotation)
State:            state/tested_capabilities.json (results + raw per-probe log),
                  state/capability_test_state.json (rotation),
                  state/test_diagnostics.json (per-provider comms health each run)
```

Every probe records an outcome (`pass`/`fail`/`error`) AND a detail code, so nothing is guessed:
`ok`, `empty`, `unsupported_param`, `bad_json`, `no_tool_call`, `no_stream`, `http_404`, `http_429`,
`http_500`, `timeout`, `conn_error`, `exception:<Type>`. The run log prints one line per model
(`provider: model  chat=pass(ok) json=error(http_429) ...`) and a per-provider summary table, so a
provider that is genuinely failing (auth/rate-limit/outage) is immediately distinguishable from one
merely serving non-chat models (which cleanly fail a chat-style probe).

Tune per-provider cooldowns and the probe policy in `scripts/test_config.py`. Handy invocations:

```text
python scripts/test_capabilities.py --dry-run                 # list planned probes, no calls
python scripts/test_capabilities.py --provider pollinations --once
python scripts/test_capabilities.py --max-minutes 60
```

## Testing Tiers

### Public metadata update

Runs without secrets where possible.

```text
fetch public model lists
normalize provider JSON
build catalog indexes
validate JSON
```

### Free-key test

Uses `*_API_KEY_FREE` secrets.

```text
check whether a free key exists
make tiny free-tier calls only when implemented
update tested capability metadata
avoid paid models
```

## Safety Rules

```text
Never print secret values.
Never write secret values to JSON output.
Only free-tier keys are used; never add a paid billing key.
Prefer workflow_dispatch for token-burning tests.
```

## What GitHub Actions Can Test

Realistic tests:

```text
model list fetch
basic key presence
basic access check
chat response
strict JSON response
tool/function-call support
vision with tiny image
embeddings with tiny text
text-to-speech with tiny phrase
speech-to-text with tiny audio fixture
rate limit/cooldown handling
```

Do not test everything every day.

Recommended split:

```text
Daily or weekly:
  public metadata refresh

Weekly free-key test:
  selected free models only

Manual deep test:
  broader capability testing when needed
```
