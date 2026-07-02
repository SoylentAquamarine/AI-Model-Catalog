# Repository Index

Quick map of the AI Model Catalog repository. Keep this updated when files or folders are added, removed, or renamed.

```text
AI-Model-Catalog/
  README.md
  INDEX.md
  LICENSE.md
  LICENSE-CODE
  LICENSE-DATA
  NOTICE.md
  CONTRIBUTING.md
  index.html
  catalog-index.json        # generated - consumer entry point

  providers/                # the published data, one file per provider
    openrouter.json
    pollinations.json
    openai.json
    anthropic.json
    gemini.json
    groq.json
    mistral.json
    together.json
    cohere.json
    cerebras.json
    deepseek.json
    fireworks.json
    sambanova.json
    huggingface.json
    cloudflare.json
    ollama.json

  schema/                   # machine-readable contract; CI validates against these
    provider.schema.json
    catalog-index.schema.json

  docs/
    CONSUMING.md            # start here as a consumer
    VERSIONING.md
    SCHEMA.md
    CAPABILITY-FLAGS.md
    FREE-PAID-CLASSIFICATION.md
    CONFIDENCE-LEVELS.md
    PROVIDER-SOURCES.md
    EMAIL-TRIGGERS.md
    MCP-AI-INTEGRATION.md
    API-KEYS-AND-TESTING.md

  scripts/
    catalog_lib.py          # shared helpers for the scripts below
    update_openrouter.py    # one updater per provider
    update_pollinations.py
    update_openai.py
    update_anthropic.py
    update_gemini.py
    update_groq.py
    update_mistral.py
    update_together.py
    update_cohere.py
    update_cerebras.py
    update_deepseek.py
    update_fireworks.py
    update_sambanova.py
    update_huggingface.py
    update_cloudflare.py
    update_ollama.py
    build_catalog.py        # generates catalog-index.json + summary
    validate.py             # schema validation (jsonschema, structural fallback)
    check_provider_secrets.py

  .github/
    workflows/
      validate.yml          # every push/PR: schema validation
      update-catalog.yml    # weekly + manual + provider-announcement dispatch
      check-free-keys.yml   # manual: report which key secrets are configured
```
