# Base Models

Base model records describe the model identity separate from provider-specific offerings.

A base model record should describe what the model probably is, such as family, vendor, parameter size, modality, and broad expected abilities.

Provider-specific files describe how a provider exposes that model, including price, context window, endpoint features, free tier status, and availability.

Use inheritance carefully.

```text
Base-model facts can be inherited.
Provider/API features need provider-specific confirmation.
```

Never mark inferred capabilities as confirmed.
