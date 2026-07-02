# Confidence Levels

Confidence tells consumers how much to trust a catalog claim.

## Levels

```text
high
medium
low
unknown
```

## Guidance

### high

Use when the value comes from a provider API, official documentation, or a direct catalog test.

### medium

Use when the value is inferred from a known base model or a reputable secondary source.

### low

Use when the value is weakly inferred, stale, incomplete, or uncertain.

### unknown

Use when the source cannot support a real confidence level.

## Data Integrity Rule

A guessed value with high confidence is worse than an unknown value.

Use `unknown` honestly.
