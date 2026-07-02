# Provider Sources

Provider source adapters should prefer official machine-readable APIs when available.

## Source Priority

```text
1. official provider API
2. official provider documentation
3. open-source dataset with compatible license
4. manual override
5. inference from base model
```

## Planned Providers

```text
openrouter
openai
gemini
groq
anthropic
ollama
```

## Source Metadata

Every imported or curated claim should track source metadata when possible.

```json
{
  "type": "provider_api",
  "name": "openrouter_models_api",
  "url": "https://openrouter.ai/api/v1/models",
  "lastChecked": "2026-07-02T00:00:00Z",
  "confidence": "high"
}
```

## Manual Overrides

Provider APIs often omit important facts.

Use the files in `overrides/` for manually curated pricing, capability, and deprecation corrections.

Manual overrides must include notes and source information.
