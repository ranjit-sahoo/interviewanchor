# InterviewAnchor monetization stage - NOT LAUNCH READY

10 November 2026, India time. Private build backup, not a Play release.

## Implemented and checked
- Exact InterviewAnchor branding; package com.ranjitsahoo.mockrep and original signing identity preserved.
- Android 1.0.7/code 8, target SDK 36, Play Billing 8.3.0 dependency. Signed APK and AAB built. APK signatures verified.
- 318 automated tests passed. Local mobile 390px and desktop 1280px Plans page rendered, no horizontal overflow or page script errors, purchase button disabled.
- Yearly prepaid/no automatic renewal proposal: India Rs 499, US $49. Actual localized Google Play price is required before purchase.
- Purchase verification uses Google Publisher API, exact product/base plan, verified region IN/US, state/expiry, acknowledgement and receipt-to-account binding. Unknown/failed receipt checks cannot grant access. Replaced tokens cannot restore older access.
- Authenticated Pub/Sub notification receiver is implemented but not configured or tested against real pushes. It re-fetches purchase state, including voided-purchase notifications, rather than trusting the notification payload.
- Paid AI identity, daily/monthly usage and processing-cost reservation live in the persistent database. Parallel workers copy the request identity. Limits apply at the provider call boundary, not only visible buttons.
- Security mail remains free, with hashed recipient/global delivery caps.
- Account deletion removes receipt tokens and identifiable paid usage; anonymous anti-replay token fingerprints remain. Export never includes raw receipts.
- Sales hard-disabled until policy approval, real localized price verification, licensed purchase tests, real notifications and verified funded reserve are all ready.

## Cost policy under review, not approved for sale
- Zero startup AI spend. Budget defaults are US$0/day and US$0 total. Pending Play transactions or estimated ad income are not funds. Existing provider credits are not silently spent.
- Once actual funded reserve is verified, proposed plan allowance is 8 actual model calls/day, 60/month in both countries. Several calls may be needed for one task.
- Feature model-call sublimits (day/month): interview and reports 8/40; resume 3/15; prep/STAR/briefs 4/20; coding 3/20; negotiation 4/20; recruiter 3/15. All remain beneath the shared cap.
- Proposed rolling-366-day processing allowance: India US$1.20; US US$6. These are cost limits, not money balances. Whichever limit is reached first pauses AI. Needs final owner review.
- Request bounds: 48,000 UTF-8 input bytes across all prompt/input text, up to 4,000 output tokens, one economical model without escalation. Quality with this final model/length policy still needs testing when funded.
- Launch cohort hard maximum is two admissions and defaults to zero. Admission requires worst-case US allowance funding before checkout. Canceled checkouts do not automatically reopen capacity. Store/real-device tests still needed; this app gate alone cannot prove no external store purchase path exists.
- Cannot guarantee ads on every install, ad approval, income, profit, or large-user capacity. No ad income is assumed in budgeting. Free-host quotas can pause availability; upgrades are not authorized.

## Accounts
- AdSense publisher pub-1288620703713535 created on ranjitkumarsahoo77@gmail.com, India.
- Existing Individual payments profile ending 5974 linked. AdSense dashboard confirmed "We've got your info".
- Website mockrep.onrender.com requires review; not approved. Exact inert verification meta tag staged, not deployed. No ad-serving script is live.
- Play merchant setup is NOT submitted. Existing Individual profile selected. Approved public name RANJIT KUMAR SAHOO, support appsupportdesk.in@gmail.com, Computer Software category, statement name RANJITSAHOO. Home-address public use is prohibited; unchecking Google's reuse checkbox reveals public-address fields still requiring a permitted address.
- Support Gmail forwarding is NOT configured. Google accepted the saved password and captcha but asks for phone QR verification. User must complete verification.

## Remaining gates
1. Public merchant address decision, merchant submit and any subsequent bank/identity/tax requirements through secure entry or owner action.
2. Google phone verification, then support Gmail forward confirmation and save settings, inspect final state.
3. Final pricing/limits owner approval and a truthful zero-cost funding route. Do not sell unusable AI before reserve is available.
4. Play app/listing, India/US base-plan prices, service account and permissions, real RTDN topic/authenticated push, licensed test track/device tests for purchase/cancel/pending/restore/expiry/refund/revocation. Upload only after separate owner instruction.
5. AdSense site verification/review, ads.txt if applicable, ad slots only on public practice pages, US privacy message/opt-outs/restricted data processing, policy/cookie/Data Safety/contains-ads declarations, ad approval.
6. Full end-to-end testing after actual configured services and final model policy, not only mocked API tests.
7. Deliberate production deployment decision. Production remains the older 1.0.6/source94c94b9 AI preview; zero-cap live change is awaiting clarification.

## Sources
- https://developer.chrome.com/docs/android/trusted-web-activity/receive-payments-play-billing
- https://support.google.com/googleplay/android-developer/answer/140504?hl=en
- https://support.google.com/googleplay/android-developer/answer/112622
- https://developer.android.com/google/play/billing/security
- https://developer.android.com/google/play/billing/rtdn-reference
- https://cloud.google.com/pubsub/docs/authenticate-push-subscriptions
- https://support.google.com/adsense/answer/9560818?hl=en
- https://support.google.com/adsense/answer/10961479?hl=en
- https://support.google.com/adsense/answer/2490070?hl=en

Nothing uploaded to Google Play. No paid sale or ad serving enabled.
