# Contributing

Contributions are welcome.

## Good Contributions

```text
provider source adapters
pricing corrections
capability corrections
manual overrides with evidence
schema improvements
documentation fixes
validation improvements
```

## Evidence Required

When adding or changing model facts, include source information where possible.

Good sources:

```text
official provider API
official provider documentation
provider pricing page
compatible open-source dataset
direct catalog test result
```

Avoid unsupported guesses.

Use `unknown` when the catalog does not have enough evidence.

## Capability Claims

Capability values should use:

```text
true
false
unknown
likely
partial
```

Do not mark an inferred value as `true` unless it is confirmed by provider docs, provider API metadata, or catalog testing.

## Public PR Safety

Do not include API keys, private keys, tokens, account data, or paid usage logs.

GitHub Actions that require provider secrets should run only from trusted branches or manual/scheduled workflows.
