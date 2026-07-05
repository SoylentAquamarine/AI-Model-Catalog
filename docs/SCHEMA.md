# Schema

The machine-readable truth lives in `schema/`:

```text
schema/provider.schema.json        validates providers/<id>.json
schema/catalog-index.schema.json   validates catalog-index.json
```

CI validates every file against these before anything publishes. This document is the human-readable companion.

## Main Concepts

```text
provider
  the company or service offering model access, plus HOW to talk to it
  (apiType, apiBase, auth)

model (offering)
  a provider-specific model entry: cost class, pricing, limits, capabilities

capability
  a task or interface the model supports, always with evidence

evidence
  how the catalog knows a claim is true, false, likely, or unknown
```

## Provider File Shape

```json
{
  "schemaVersion": "1.0.0",
  "provider": {
    "id": "gemini",
    "displayName": "Google Gemini",
    "homepage": "https://ai.google.dev",
    "apiBase": "https://generativelanguage.googleapis.com/v1beta",
    "apiType": "gemini",
    "auth": {
      "scheme": "query",
      "name": "key",
      "extraHeaders": null
    },
    "notes": "Google documents a rate-limited free tier for Gemini and Gemma API models.",
    "lastChecked": "2026-07-05T08:52:19Z"
  },
  "models": [ ... ]
}
```

### apiType

Which client driver a consumer should use:

```text
openai-compatible   /chat/completions style (Groq, OpenRouter, Cohere, many others)
gemini              Google Generative Language API
anthropic           Anthropic Messages API (driver defined; no free provider uses it)
ollama              local Ollama runtime (for models you host yourself)
```

New values are additive (minor version bump). A consumer that implements these drivers can talk to any provider in the catalog without provider-specific code.

### auth

How to present a credential — never the credential itself:

```text
bearer   Authorization: Bearer <key>
header   <auth.name>: <key>, plus auth.extraHeaders sent verbatim
query    ?<auth.name>=<key>
none     no credential required
```

## Model Entry Shape

```json
{
  "id": "example/model-id",
  "providerModelId": "example/model-id",
  "displayName": "Example Model",
  "costClass": "free",
  "pricing": { "currency": "USD", "inputPerMTokens": 0.0, "outputPerMTokens": 0.0 },
  "limits": { "contextTokens": 32768, "maxOutputTokens": 8192 },
  "capabilities": { "chat": { "value": true, "source": "openrouter_models_api", "confidence": "high", "lastChecked": "..." } },
  "status": "available",
  "source": "openrouter_models_api",
  "lastChecked": "2026-07-02T17:53:48Z"
}
```

```text
costClass    free | paid | trial | local | unknown   (docs/FREE-PAID-CLASSIFICATION.md)
pricing      USD per million tokens, when known; null when not
limits       token limits, when known; null when not
status       available | preview | deprecated | unknown
capabilities keys from docs/CAPABILITY-FLAGS.md; absent key = no claim made
```

## Capability Values

Capabilities are never plain booleans:

```text
true      confirmed supported
false     confirmed not supported
unknown   no good information yet
likely    inferred but not confirmed
partial   supported with limits or caveats
```

Every capability carries evidence:

```json
{
  "value": "likely",
  "source": "inferred_from_base_model",
  "confidence": "medium",
  "lastChecked": null,
  "notes": "Provider endpoint has not confirmed this feature."
}
```

See `docs/CONFIDENCE-LEVELS.md`. The integrity rule: a guessed value with high confidence is worse than an honest unknown.

## Forward Compatibility

Consumers must ignore fields they do not recognize. Schemas set `additionalProperties: true` on purpose — new fields arrive as minor versions. See `docs/VERSIONING.md`.
