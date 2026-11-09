# Data vendors and regions (zero-cost constraint)

Minimal sharing by design; every vendor processes only what the feature needs.

| Vendor | What it gets | Why | Region notes |
|--------|--------------|-----|--------------|
| Render (hosting + Postgres) | All server-side data (account, history, progress) | Runs the app | Current dashboard reports Oregon (verified 2026-10-30); no migration performed. An India/nearby region requires checking supported free inventory and a separate no-data-loss migration plan. |
| Nebius Token Factory (LLM) | Prompt text the user pastes (resume/JD) to generate answers | AI features | No account data sent; requests are per-call, not retained by us beyond the user's own saved history |
| Google (Sign-In) | Email + Google sub for users who choose Google login | Optional sign-in | Global |
| Google Play (future, premium only) | Purchase token + subscription state | Billing, disabled by default | Google-managed |
| Brevo HTTPS API (when BREVO_API_KEY is set), or configured SMTP relay | Recipient email + verification code; no resume or interview answers | Email verification | Brevo free plan: up to 300 emails/day; no paid fallback. Provider setup/delivery must be verified before enabling. |

No analytics vendor, no ads SDK, no crash-reporting vendor: analytics collection is disabled, and no automatic crash details are stored.
