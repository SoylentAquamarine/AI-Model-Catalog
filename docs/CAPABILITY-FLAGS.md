# Capability Flags

Capability flags describe what a model or provider offering can do.

## Initial Capability Names

```text
chat
completion
json
tools
vision
audio_input
audio_output
speech_to_text
text_to_speech
embeddings
rerank
image_generation
code
reasoning
streaming
batch
fine_tuning
```

## Values

Use these values:

```text
true      confirmed supported
false     confirmed not supported
unknown   no good information yet
likely    inferred but not confirmed
partial   supported with limits or caveats
```

## Sources

Common source values:

```text
provider_api
provider_docs
provider_pricing_page
manual_override
inferred_from_base_model
tested_by_catalog
not_confirmed
```

## Confidence

```text
high
medium
low
unknown
```

## Rule

Do not turn `likely` into `true` unless there is provider documentation, provider API metadata, or a catalog test proving it.
