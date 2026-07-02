# Email-Triggered Updates

Providers announce model changes by email ("we're deprecating X", "new model Y"). Those announcements can trigger a catalog refresh instead of waiting for the weekly run.

## How It Works

The update workflow accepts an external trigger via GitHub's `repository_dispatch` API:

```text
provider email arrives
  -> forwarded to an automation (Cloudflare Email Worker, Zapier, Power Automate, ...)
    -> automation POSTs to the GitHub API with event_type "provider-announcement"
      -> Update Catalog workflow runs immediately
      -> an issue is opened recording the announcement (provider, subject, summary)
      -> the run's diff shows what actually changed in the machine-readable data
```

The issue matters: updaters only see what provider APIs expose. If the email announces something the APIs don't show (a pricing change, a sunset date), the issue is the curation to-do for updating the catalog by hand.

## Triggering Manually

Anyone with repo access can fire the same trigger from a shell:

```bash
gh api repos/SoylentAquamarine/AI-Model-Catalog/dispatches \
  -f event_type=provider-announcement \
  -f 'client_payload[provider]=openai' \
  -f 'client_payload[subject]=Deprecation notice for gpt-4-0613'
```

Or just run the workflow from the Actions tab (`workflow_dispatch`) if you don't need the announcement recorded.

## Payload Fields

All optional; whatever is present gets recorded in the issue:

```json
{
  "event_type": "provider-announcement",
  "client_payload": {
    "provider": "openai",
    "subject": "the email subject line",
    "from": "noreply@openai.com",
    "received": "2026-07-02T12:00:00Z",
    "summary": "optional extracted/parsed announcement text"
  }
}
```

## Cloudflare Email Worker Recipe

Cloudflare Email Routing can forward a dedicated address (e.g. `announcements@yourdomain`) to a Worker. Subscribe that address to provider newsletters/status lists, and every announcement becomes a trigger:

```js
const PROVIDER_DOMAINS = {
  "openai.com": "openai",
  "anthropic.com": "anthropic",
  "google.com": "gemini",
  "groq.com": "groq",
  "openrouter.ai": "openrouter",
};

function guessProvider(from) {
  const domain = (from.split("@")[1] || "").toLowerCase();
  for (const [suffix, provider] of Object.entries(PROVIDER_DOMAINS)) {
    if (domain.endsWith(suffix)) return provider;
  }
  return "unknown";
}

export default {
  async email(message, env) {
    await fetch(
      "https://api.github.com/repos/SoylentAquamarine/AI-Model-Catalog/dispatches",
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${env.GITHUB_PAT}`,
          "Accept": "application/vnd.github+json",
          "User-Agent": "catalog-email-trigger",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          event_type: "provider-announcement",
          client_payload: {
            provider: guessProvider(message.from),
            subject: message.headers.get("subject") || "(no subject)",
            from: message.from,
            received: new Date().toISOString(),
          },
        }),
      },
    );
  },
};
```

Setup:

```text
1. Create a fine-grained GitHub PAT scoped to ONLY this repository with
   Contents: Read and write (required for repository_dispatch).
2. Store it as a Worker secret: wrangler secret put GITHUB_PAT
3. Add an Email Routing rule: announcements@yourdomain -> this Worker.
4. Subscribe that address to provider announcement emails.
```

## Roadmap: Interpreting Email Content

V1 uses the email as a trigger plus a recorded issue. The next step is parsing the announcement body into structured hints (model ids, deprecation dates, price changes) included in `client_payload.summary` — the Worker can do this with simple pattern matching, or by routing the email text through an AI model before dispatching. Parsed hints land in the issue for human review; they never modify catalog data directly, because announcement text is not a machine-confirmed source (see `docs/CONFIDENCE-LEVELS.md`).
