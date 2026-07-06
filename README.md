# AI Model Catalog

**Free AI, standardized.** A public, always-updated catalog of the free AI providers — which models are free, what they can do, and exactly how to connect — normalized into simple JSON config files carrying pricing, free/paid status, capabilities, limits, and source confidence. Download the config, skip writing that plumbing yourself.

**This project pays for nothing.** Every provider is checked with a free-tier or keyless account only — never a paid plan — so the catalog is a live map of what you can genuinely reach and run for free. Paid models that surface are still listed and clearly flagged, so you see the whole picture, but the mission is the free tier.

## Consuming the Catalog

Two files kinds, plain HTTPS, no account needed:

```bash
# which providers exist, when the catalog was built
curl -s https://raw.githubusercontent.com/SoylentAquamarine/AI-Model-Catalog/main/catalog-index.json

# a provider's models, capabilities, and how to talk to its API
curl -s https://raw.githubusercontent.com/SoylentAquamarine/AI-Model-Catalog/main/providers/openrouter.json

# how many free models are verified for each capability (chat, json, tools, vision, streaming)
curl -s https://raw.githubusercontent.com/SoylentAquamarine/AI-Model-Catalog/main/capabilities.json
```

Capabilities are **verified, not declared**: each is confirmed by a tiny live test the catalog runs weekly (`source: tested_by_catalog`) and only proven capabilities are published — so counts start low and grow as testing rotates through the models.

Start with `docs/CONSUMING.md`. The contract: files validate against `schema/`, versioned by semver (`docs/VERSIONING.md`), consumers ignore unknown fields. Everything else in this repo is maintenance machinery.

## Goal

The free AI landscape is scattered and inconsistent. Every provider exposes model information differently — some publish model lists, some publish pricing, some publish capabilities, some expose almost nothing machine-readable — and it's rarely obvious which providers even have a usable free tier.

This project standardizes that: it normalizes the free providers into simple, consistent JSON config files that any tool or project can consume, and keeps them current automatically. The point is to cut out the tedious, repeated setup work of discovering and wiring up free AI, so developers can build on the free tier without a budget.

## How It Updates

```text
providers/
  openrouter.json    public models API - richest data, no key needed (free models only)
  pollinations.json  public models API - free keyless service, no key needed
  gemini.json        models API (key) - token limits, generation methods
  groq.json          models API (key) - context windows, free tier
  mistral.json       models API (key) - per-model capabilities, free tier
  together.json      models API (key) - free models only, per-model types
  cohere.json        models API (key) - endpoint lists (chat/embed/rerank)
  cerebras.json      models API (key) - model presence, free tier
  sambanova.json     models API (key) - model presence, free tier
  huggingface.json   router models API (key) - free inference allowance
  cloudflare.json    Workers AI search API (key + account id)
```

Only models with a standing free tier are published. Providers that are paid, or only free via an expiring trial credit (OpenAI, Anthropic, DeepSeek, Fireworks, and others), are intentionally excluded. Providers whose model API returns paid/trial models (OpenRouter, Together) are filtered to their free models only.

One updater script per provider (`scripts/update_<provider>.py`). They run weekly via GitHub Actions, on demand from the Actions tab, and on provider announcement emails via `repository_dispatch` — see `docs/EMAIL-TRIGGERS.md`. Key-based updaters skip gracefully when their key is not configured.

Each provider file records:

```text
how to talk to the provider: apiType, apiBase, auth shape (never a key)
model id and display name
free/paid/trial/local/unknown
pricing when known (USD per million tokens)
context limits when known
capabilities with evidence: value, source, confidence, lastChecked
```

## Core Idea

Separate the base model from the provider offering as the catalog matures.

```text
Base model:
  what the model probably is and can generally do

Provider offering:
  how a specific provider exposes that model, including pricing,
  limits, API features, free tier status, and availability
```

For the MVP, provider files can carry the important fields directly.

## Important Rule

Never present guessed data as confirmed data.

Capabilities should include evidence and confidence.

```json
{
  "value": "likely",
  "source": "inferred_from_base_model",
  "confidence": "medium"
}
```

## Intended Consumers

This catalog should be useful for:

```text
MCP tools
AI routers
local AI consoles
small apps that need a model selector
developer dashboards
free-model discovery tools
pricing comparison tools
capability-aware model routing
```

## VTX MCP-AI Integration

VTX MCP-AI will be one consumer of this catalog, but the schema should remain generic and useful outside the VTX ecosystem.

Local tools should merge this public catalog with local user-specific state, such as:

```text
usableWithCurrentKey
cooldownUntil
rateLimited
disabledByUser
preferred profiles
```

The public catalog should not contain private user-specific access information.

## License

Code and scripts are licensed under Apache-2.0.

Catalog data is licensed under CC BY 4.0 unless otherwise noted.

See `LICENSE.md`, `LICENSE-CODE`, `LICENSE-DATA`, and `NOTICE.md`.
