# Play-installed app browser-bar defect

Observed by owner after installing closed test 1.0.9 on November 10, 2026: Custom Tab close/address/share toolbar visible. Launcher is a Trusted Web Activity with Custom Tab fallback. Live HTTPS assetlinks response omitted the actual Play distribution signing certificate.

Verified against Play Console App signing page and its Digital Asset Links JSON on November 10:
https://play.google.com/console/u/0/developers/7294802767666625168/app/4975110175712918527/keymanagement

Added the exact Console-provided fingerprint in app/android_assetlinks.json, preserving the upload and legacy fingerprints for existing installs. Removed the shadowed hub route so only one association response exists. Server serves application/json without redirects and with a five-minute HTTP cache. Android package, launch URL, signing key, version and free feature set unchanged. No new Play bundle.

Tests: 82 association/security/privacy/monetization checks pass with test rate limits configured before app import. First combined run imported the app before test rate-limit overrides and caused 12 rate-limit failures; corrected invocation passes all 82 without production changes. Four viewport browser walks pass; notes persistence and offline reload pass, zero script errors and zero API requests. Physical Play-installed Android toolbar result still needs owner confirmation after server deployment and relaunch. No connected Android device available locally.
