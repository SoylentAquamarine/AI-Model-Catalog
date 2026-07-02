# AI Model Catalog

A public, normalized JSON catalog of AI providers, models, pricing, free/paid status, capabilities, limits, and source confidence.

## Goal

AI providers expose model information in different ways. Some publish model lists. Some publish pricing. Some publish capabilities. Some expose almost nothing in a clean machine-readable format.

This project normalizes that information into simple provider JSON files that can be consumed by many tools and projects.

## MVP Direction

Keep the first version simple.

```text
providers/
  openrouter.json
  openai.json
  gemini.json
  groq.json
  anthropic.json
  ollama.json
```

Each provider file tracks that provider's model offerings.

The first useful target is:

```text
model id
display name
free/paid/trial/local/unknown
pricing when known
context limits when known
basic capabilities, especially for free models
source
confidence
last checked
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
