# Capability Flags

Capability flags describe what a model or provider offering can do.

## Verified-only publishing

The catalog publishes a model's `capabilities` **only after a live test proves them**
(`source: tested_by_catalog`). Nothing inferred or provider-declared is published as a capability.

- The weekly harness (`scripts/test_capabilities.py`) runs a tiny probe per capability and records
  `value: true` (probe passed) or `value: false` (probe cleanly failed), both at `confidence: high`.
  Transient errors (rate limit, outage) record nothing and are retried next rotation.
- Provider-declared flags from a model-list API are kept on each model under **`hints`** — never
  under `capabilities`. Hints are used only to decide *what* to probe (e.g. only test `vision`
  where a hint suggests it). Consumers must not treat `hints` as confirmed.
- The tested set (the "core 5"): `chat`, `json`, `streaming`, `tools`, `vision`.
- Verified results are the source of truth in `state/tested_capabilities.json` and are rolled up
  into `catalog-index.json.capabilitySummary` and `capabilities.json`.

## Initial Capability Names

```text
chat
completion
json
tools
vision
audio_input
audio_output
speech_to_text
text_to_speech
embeddings
rerank
image_generation
code
reasoning
streaming
batch
fine_tuning
```

## Values

Use these values:

```text
true      confirmed supported
false     confirmed not supported
unknown   no good information yet
likely    inferred but not confirmed
partial   supported with limits or caveats
```

## Sources

Common source values:

```text
provider_api
provider_docs
provider_pricing_page
manual_override
inferred_from_base_model
tested_by_catalog
not_confirmed
```

## Confidence

```text
high
medium
low
unknown
```

## Rule

Do not turn `likely` into `true` unless there is provider documentation, provider API metadata, or a catalog test proving it.

For this catalog specifically, only a catalog test (`tested_by_catalog`) promotes a capability into the published `capabilities`; everything else stays in `hints`.
