# Versioning Policy

Every published file carries a `schemaVersion` (semver). This is the contract that lets strangers build against the catalog without getting broken.

## The Rules

```text
MAJOR  breaking change: field removed, renamed, or its meaning changed.
       Consumers may refuse files with a major they do not understand.

MINOR  additive change: new optional fields, new enum values consumers
       may ignore. Never breaks a well-behaved consumer.

PATCH  data corrections and doc fixes. No structural change.
```

## Consumer Obligations

```text
Ignore unknown fields (this is what makes minor bumps safe).
Check the major version; on a newer major, keep your previous copy
and warn rather than failing hard.
```

## Maintainer Obligations

```text
Never change a field's meaning without a major bump.
Update schema/*.json and docs/SCHEMA.md in the same change.
Tag a release at every major bump so pinned consumers keep working.
Announce breaking changes in the release notes.
```

## Current Versions

```text
provider files   1.0.0   (schema/provider.schema.json)
catalog index    1.1.0   (schema/catalog-index.schema.json)
                         1.1.0 added totalModels, totalFreeModels,
                         and per-provider freeModelCount - additive,
                         safe for 1.0.0 consumers to ignore
```
