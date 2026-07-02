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

## Current Updaters

One script per provider under `scripts/`:

```text
update_openrouter.py   public models API, no key needed
update_openai.py       needs OPENAI_API_KEY_FREE
update_groq.py         needs GROQ_API_KEY_FREE
update_gemini.py       needs GEMINI_API_KEY_FREE
update_anthropic.py    needs ANTHROPIC_API_KEY_FREE
update_ollama.py       no fetch; local runtime, connection contract only
```

Key-based updaters skip gracefully when their key is missing, keeping the existing file. An updater that fetches zero models aborts rather than wiping a good file.

## Manual Curation (planned)

Provider APIs often omit important facts — pricing pages especially. A curated-overrides lane (merged at build time, with notes and source information required) is planned; it was removed from the MVP and will return once the fetched lane is stable.
