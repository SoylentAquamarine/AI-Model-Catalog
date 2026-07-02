# Free and Paid Classification

Free vs paid is not enough by itself.

The catalog uses a cost class plus pricing fields.

## Cost Classes

```text
free
paid
trial
local
unknown
```

## Meaning

### free

The model offering appears to be available at zero direct token cost through the provider.

Free does not mean unlimited.

Free models may still require an account, API key, quota, or rate limits.

### paid

The model offering has a known nonzero token cost or requires paid billing.

### trial

The provider appears to offer temporary credits or trial-limited access.

### local

The model runs locally or through a local runtime. There may still be hardware or electricity cost, but there is no provider token charge.

### unknown

The catalog does not have enough information.

## Required Pricing Fields

```text
inputPerMillion
outputPerMillion
currency
source
lastChecked
```

Use `null` when unknown.

## Do Not Store User Access

The public catalog should not say whether a specific user's API key can use a model.

That belongs in local software consuming the catalog.
