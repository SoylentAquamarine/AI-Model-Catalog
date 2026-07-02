# API Keys and Testing

This project can use GitHub Actions secrets for provider metadata checks and optional free-tier capability testing.

Do not commit API keys, tokens, raw provider responses containing secrets, or account-specific data.

## Configured Secret Names

The repository may use these GitHub Actions secrets:

```text
CEREBRAS_API_KEY_FREE
CLOUDFLARE_API_KEY_FREE
COHERE_API_KEY_FREE
DEEPSEEK_API_KEY_FREE
FIREWORKS_API_KEY_FREE
GEMINI_API_KEY_FREE
GROQ_API_KEY_FREE
HUGGINGFACE_API_KEY_FREE
MISTRAL_API_KEY_FREE
OPENAI_API_KEY_FREE
OPENROUTER_API_KEY_FREE
POLLINATIONS_API_KEY_FREE
SAMBANOVA_API_KEY_FREE
TOGETHER_API_KEY_FREE
```

Paid testing keys should use the same pattern later:

```text
OPENROUTER_API_KEY_PAID
OPENAI_API_KEY_PAID
GEMINI_API_KEY_PAID
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

### Paid-light test

Future optional workflow.

```text
runs weekly or manually only
uses *_API_KEY_PAID secrets
sets a hard cost budget
uses tiny prompts/files
uploads debug artifacts instead of committing raw outputs
```

## Safety Rules

```text
Never print secret values.
Never write secret values to JSON output.
Never run paid tests on pull_request from forks.
Prefer workflow_dispatch for token-burning tests.
Keep scheduled paid tests small and budgeted.
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
