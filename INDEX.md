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
  catalog-index.json        # generated - consumer entry point (incl. capabilitySummary)
  capabilities.json         # generated - verified capability counts + model lists

  providers/                # the published data, one file per provider
    openrouter.json
    pollinations.json
    gemini.json
    groq.json
    mistral.json
    together.json
    cohere.json
    cerebras.json
    sambanova.json
    huggingface.json
    cloudflare.json

  state/                    # machine-managed test state (committed by the harness)
    tested_capabilities.json      # verified results + raw per-probe log (outcome/detail)
    capability_test_state.json    # per-model last-tested timestamps (rotation)
    test_diagnostics.json         # per-provider comms health per run (pass/fail/error by detail)

  schema/                   # machine-readable contract; CI validates against these
    provider.schema.json
    catalog-index.schema.json
    capabilities.schema.json

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
    update_gemini.py
    update_groq.py
    update_mistral.py
    update_together.py
    update_cohere.py
    update_cerebras.py
    update_sambanova.py
    update_huggingface.py
    update_cloudflare.py
    build_catalog.py        # generates catalog-index.json + capabilities.json
    validate.py             # schema validation (jsonschema, structural fallback)
    check_provider_secrets.py
    probes.py               # live capability probes (openai-compatible + gemini)
    test_config.py          # per-provider cooldowns + probe policy
    test_capabilities.py    # weekly capability test harness (scheduler)

  .github/
    workflows/
      validate.yml          # every push/PR: schema validation
      update-catalog.yml    # weekly + manual + provider-announcement dispatch
      test-capabilities.yml # weekly + manual: live capability verification
      check-free-keys.yml   # manual: report which key secrets are configured
```
