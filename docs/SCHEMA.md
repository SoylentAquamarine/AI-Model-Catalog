# Schema

The catalog schema is designed to be generic and reusable.

## Main Concepts

```text
provider
  the company or service offering model access

baseModel
  the underlying model identity

offering
  a provider-specific version of a model

capability
  a task or interface the model/offering supports

evidence
  how the catalog knows a field is true, false, likely, or unknown
```

## Provider Offering

A provider offering should include:

```text
id
providerId
providerModelId
displayName
baseModelRef
status
cost
limits
capabilities
source
```

## Capability Values

Capabilities should not be plain booleans only.

Use:

```text
true
false
unknown
likely
partial
```

Every capability should include:

```text
value
source
confidence
lastChecked
notes
```

## Source and Confidence

Every important claim should say where it came from and how reliable it is.

Example:

```json
{
  "value": "likely",
  "source": "inferred_from_base_model",
  "confidence": "medium",
  "lastChecked": null,
  "notes": "Provider endpoint has not confirmed this feature."
}
```
