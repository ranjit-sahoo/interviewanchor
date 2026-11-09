# Ad readiness - staged only, ads remain off

November 10, 2026. This is an implementation/review plan, not approval to serve ads.

## Chosen technical route
The existing Android app is a Chrome Trusted Web Activity, not a WebView. Google explicitly lists Trusted Web Activities among supported viewing frames for AdSense web ads. Keep this route, subject to site approval and all program policies. Do not add an AdMob SDK merely because the wrapper runs on Android. No advertising ID permission or Mobile Ads SDK is currently included.

Publisher: pub-1288620703713535. The homepage has only an inert account verification meta tag. There is no ad-serving loader or ad slot. Site review and ad approval remain pending. No revenue is assumed in the AI budget.

## Safe placement design for the later approved implementation
- Use a separate public, read-only practice-content page with substantial original coaching content. Do not insert ads into the mixed homepage/tool interface: it can display private forms or reports at the same URL.
- Allowlist the approved content route. Deny all account, input, resume, report, recording, screening, share-card, payment, error, empty and legal pages. Never use pasted content or account data to target ads.
- Show at most one clearly labeled display placement after a complete practice section. Keep it away from navigation, record/start/download buttons. Reserve dimensions to avoid shifting buttons under a user's finger.
- No rewarded ads, interstitials, forced clicks or claims that viewing ads unlocks AI. Never click live ads during testing.
- Keep ad loading blocked until provider approval, privacy setup, route audit and final owner approval are recorded. Fail closed if region or consent is unknown. Do not cache ad responses in the service worker.
- Publish the exact ads.txt entry from the AdSense account only after confirming the seller relationship. A candidate is `google.com, pub-1288620703713535, DIRECT, f08c47fec0942fa0`, but it is not published by this build and must be confirmed from the account.

## Privacy work required before serving
Configure the actual AdSense Privacy & messaging controls, including applicable US state privacy messages and opt-outs/restricted data processing. A cookie notice or non-personalized setting alone is not a consent system. Public site visitors are not limited to the two Play sales countries: applicable EEA/UK/Switzerland consent rules still matter unless ad serving is reliably excluded there. Use Google's supported consent solution; deny ad requests where required consent is missing. Honor withdrawal and test it before activating ads.

Update privacy/cookie text with actual Google data/cookie use, purposes, retention/provider links and choices. Then update Play Contains ads and Data safety to match the ads-bearing version before its release. Current declarations correctly describe no ads, not this future implementation.

## Acceptance checks before an activation decision
1. AdSense site approved, account/payment/verification status reviewed.
2. Approved route contains original useful public content; no sensitive text enters a request or URL.
3. Fresh visitor, consent accept/reject/withdraw, unknown geography and applicable US opt-out paths checked on device.
4. Zero ad/network requests on every private/tool route and before consent; no caching/offline replay.
5. Labels, tap distance, layout shift and mobile placement visually checked.
6. Policy pages and Play declarations match the actual implementation.
7. Owner receives final ad behavior, uncertainty and spending/sales numbers before enabling.

## Official sources checked November 10, 2026
- https://support.google.com/adsense/answer/48182?hl=en - supported TWA viewing frame and placement policies.
- https://support.google.com/adsense/answer/3394713 - web-in-app implementation policy.
- https://support.google.com/adsense/answer/9573162?hl=en - ads.txt guidance.
- https://support.google.com/adsense/answer/10961068?hl=en - US state privacy messaging.
- https://support.google.com/adsense/answer/10961479?hl=en - consent platform requirements.
