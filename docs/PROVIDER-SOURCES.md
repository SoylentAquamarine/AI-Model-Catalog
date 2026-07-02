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

## Current Providers

```text
openrouter    pollinations    openai      anthropic
gemini        groq            mistral     together
cohere        cerebras        deepseek    fireworks
sambanova     huggingface     cloudflare  ollama
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
update_openrouter.py    public models API, no key needed
update_pollinations.py  public models API, no key needed
update_openai.py        needs OPENAI_API_KEY_FREE
update_anthropic.py     needs ANTHROPIC_API_KEY_FREE
update_gemini.py        needs GEMINI_API_KEY_FREE
update_groq.py          needs GROQ_API_KEY_FREE
update_mistral.py       needs MISTRAL_API_KEY_FREE
update_together.py      needs TOGETHER_API_KEY_FREE
update_cohere.py        needs COHERE_API_KEY_FREE
update_cerebras.py      needs CEREBRAS_API_KEY_FREE
update_deepseek.py      needs DEEPSEEK_API_KEY_FREE
update_fireworks.py     needs FIREWORKS_API_KEY_FREE
update_sambanova.py     needs SAMBANOVA_API_KEY_FREE
update_huggingface.py   needs HUGGINGFACE_API_KEY_FREE
update_cloudflare.py    needs CLOUDFLARE_API_KEY_FREE + CLOUDFLARE_ACCOUNT_ID
update_ollama.py        no fetch; local runtime, connection contract only
```

Key-based updaters skip gracefully when their key is missing, keeping the existing file. An updater that fetches zero models aborts rather than wiping a good file. In the update workflow each provider runs as its own tolerant step, so one provider's outage never blocks the rest.

## Manual Curation (planned)

Provider APIs often omit important facts — pricing pages especially. A curated-overrides lane (merged at build time, with notes and source information required) is planned; it was removed from the MVP and will return once the fetched lane is stable.
