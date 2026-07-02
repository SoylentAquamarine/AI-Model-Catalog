# MCP-AI Integration

This catalog is generic, but VTX MCP-AI is an intended consumer.

## Public Catalog Role

The public catalog should answer:

```text
what models exist
which provider offers them
free/paid/trial/local/unknown status
known pricing
known or inferred capabilities
context and output limits
source and confidence
```

## Local MCP-AI Role

MCP-AI should merge the public catalog with local user-specific state.

Local-only state includes:

```text
API keys
usableWithCurrentKey
cooldownUntil
rateLimited
disabledByUser
preferred model profiles
routing/fallback order
local model availability
```

## Suggested MCP-AI Commands

```text
ai_update_catalog
ai_refresh_provider_models
ai_check_access
ai_get_usable_models
ai_get_free_models
ai_get_provider_health
ai_route
ai_generate
```

## Routing Rule

MCP-AI should route by capability/profile first, then provider/model.

Example:

```text
Console asks for json_planner.
MCP-AI checks local profiles.
MCP-AI checks public catalog capabilities.
MCP-AI checks local access and cooldown state.
MCP-AI chooses the best available provider/model.
```

## Important Boundary

The public catalog does not know what a user's key can access.

A model can be public, paid, free, listed, or documented but still not usable with a specific account.
