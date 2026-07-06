# Consuming the Catalog

Everything a consumer needs is two kinds of files, fetched over plain HTTPS. No account, no API, no rate limits beyond GitHub's generous raw-file serving.

## Quickstart

```bash
# 1. Fetch the index - which providers exist, when the catalog was built
curl -s https://raw.githubusercontent.com/SoylentAquamarine/AI-Model-Catalog/main/catalog-index.json

# 2. Fetch the provider files it lists
curl -s https://raw.githubusercontent.com/SoylentAquamarine/AI-Model-Catalog/main/providers/openrouter.json

# 3. (optional) Verified capability rollup: how many models do what, with model lists
curl -s https://raw.githubusercontent.com/SoylentAquamarine/AI-Model-Catalog/main/capabilities.json
```

That is the entire consumption surface.

## Capabilities are verified, not declared

A model's `capabilities` are published **only after a live test confirms them** (`source: tested_by_catalog`).
Provider-declared flags live under `hints` on each model and are not confirmed — do not rely on them.
`catalog-index.json.capabilitySummary` gives per-capability counts; `capabilities.json` gives the model lists.
Counts grow over time as the weekly harness rotates through every model. Scripts, workflows, and docs in this repo are maintenance machinery — consumers never need them.

## Recommended Sync Flow

```text
1. GET catalog-index.json
2. Compare generatedAt to your last stored sync time
   unchanged -> done, nothing to download
3. GET each providers/<id>.json listed in the index
4. Check schemaVersion: if the major version is newer than what you
   understand, keep your previous copy and warn - do not break
5. Replace your local copies atomically (temp + swap)
```

## Latest vs Pinned

```text
Latest  raw.githubusercontent.com/.../main/...
        always the freshest data; schema changes arrive as they ship

Pinned  a release tag, e.g. .../v1.0.0/...
        reproducible; upgrade on your schedule
```

Pin if your application breaks when data changes underneath it. Use latest if you just want current model info (most consumers).

## Rules for Not Getting Broken

```text
Ignore fields you do not recognize - new fields arrive in minor versions.
Check schemaVersion major before trusting a file.
Treat capability values honestly: "likely" and "unknown" are not "true".
Never expect secrets, keys, or user-specific data - the catalog has none.
```

See `docs/VERSIONING.md` for the change policy.

## Using apiType and auth

Each provider file tells your program how to talk to that provider:

```text
apiType   which client driver to use (openai-compatible, anthropic, gemini, ollama)
apiBase   where to send requests (override locally for proxies/self-hosted)
auth      how to present YOUR credential:
            bearer -> Authorization: Bearer <key>
            header -> <auth.name>: <key>   (plus auth.extraHeaders verbatim)
            query  -> ?<auth.name>=<key>
            none   -> no credential needed
```

The credential itself is always yours, stored your way. The catalog only describes the shape of the door, never the key.

## Merging With Local State

The catalog answers "what exists, what does it cost, what can it do." It cannot know what *your* key can access, your rate-limit state, or your preferences. Keep those in your own local files and merge at load time. (VTX MCP-AI, one consumer of this catalog, pairs each `Catalog\<id>.json` with its own local `Providers\<id>.json` — the same pattern works anywhere.)

## Attribution

Catalog data is CC BY 4.0. If you redistribute the data (not just consume it at runtime), credit "AI Model Catalog (github.com/SoylentAquamarine/AI-Model-Catalog)". See `LICENSE.md`.
