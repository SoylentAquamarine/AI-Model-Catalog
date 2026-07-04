# Notices and Attribution

This catalog may incorporate, normalize, or reference data from provider APIs, provider documentation, and open-source datasets.

## Planned Sources

Initial planned sources include:

```text
OpenRouter public model API
OpenAI model API and documentation
Google Gemini model API and documentation
Groq model list and documentation
Anthropic model documentation
LiteLLM model pricing/context data where license-compatible
manual project-maintained overrides
```

## Source Tracking

Each catalog record should include source metadata when possible:

```json
{
  "source": {
    "type": "provider_api",
    "name": "openrouter_models_api",
    "url": "https://openrouter.ai/api/v1/models",
    "lastChecked": "2026-07-02T00:00:00Z",
    "confidence": "high"
  }
}
```

## License Compatibility

Do not bulk-copy data from a source unless its license and terms allow reuse.

When importing from open-source datasets, preserve required notices.

When importing from provider APIs, respect rate limits and provider terms.
