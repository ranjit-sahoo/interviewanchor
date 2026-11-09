# InterviewAnchor monetization stage - NOT LAUNCH READY

10 November 2026, India time. Private build backup, not a Play release.

## Implemented and checked
- Exact InterviewAnchor branding; package com.ranjitsahoo.mockrep and original signing identity preserved.
- Android 1.0.7/code 8, target SDK 36, Play Billing 8.3.0 dependency. Signed APK and AAB built. APK signatures verified.
- 326 automated tests passed after the new policy change. Legacy functionality tests replace the payment boundary only in the test process; dedicated billing integration tests keep it active. Local mobile 390px and desktop 1280px Plans page rendered, no horizontal overflow or page script errors, purchase button disabled.
- Yearly prepaid/no automatic renewal proposal: India Rs 599, US $49. Actual localized Google Play price is required before purchase.
- Purchase verification uses Google Publisher API, exact product/base plan, verified region IN/US, state/expiry, acknowledgement and receipt-to-account binding. Unknown/failed receipt checks cannot grant access. Replaced tokens cannot restore older access.
- Authenticated Pub/Sub notification receiver is implemented but not configured or tested against real pushes. It re-fetches purchase state, including voided-purchase notifications, rather than trusting the notification payload.
- Paid AI identity, daily/monthly usage and processing-cost reservation live in the persistent database. Parallel workers copy the request identity. Limits apply at the provider call boundary, not only visible buttons.
- Security mail remains free, with hashed recipient/global delivery caps.
- Account deletion removes receipt tokens and identifiable paid usage; anonymous anti-replay token fingerprints remain. Export never includes raw receipts.
- Sales hard-disabled until policy approval, real localized price verification, licensed purchase tests, real notifications and verified funded reserve are all ready.

## Cost policy under review, not approved for sale
- Owner revised the policy at 2:13-2:14 AM IST: up to US$20 overall AI spend is approved with a hard stop. Code clamps the total to at most US$20 even if an old environment value is higher. Default daily safety cap is US$3. Live old production remains capped at zero until a separately approved gated deployment. Pending Play transactions or estimated ad income are not funds.
- Once actual funded reserve is verified, proposed plan allowance is 8 actual model calls/day, 60/month in both countries. Several calls may be needed for one task.
- Feature model-call sublimits (day/month): interview and reports 8/40; resume 3/15; prep/STAR/briefs 4/20; coding 3/20; negotiation 4/20; recruiter 3/15. All remain beneath the shared cap.
- Proposed rolling-366-day processing allowance: India US$1.20; US US$1.20. These are cost limits, not money balances. Whichever limit is reached first pauses AI. Needs final owner review.
- Request bounds: 48,000 UTF-8 input bytes across all prompt/input text, up to 4,000 output tokens, one economical model without escalation. Quality with this final model/length policy still needs testing when funded.
- Launch cohort hard maximum is two admissions and defaults to zero. Admission requires worst-case per-subscriber allowance funding before checkout. Canceled checkouts do not automatically reopen capacity. Store/real-device tests still needed; this app gate alone cannot prove no external store purchase path exists.
- Cannot guarantee ads on every install, ad approval, income, profit, or large-user capacity. No ad income is assumed in budgeting. Free-host quotas can pause availability; upgrades are not authorized.

## Accounts
- AdSense publisher pub-1288620703713535 created on ranjitkumarsahoo77@gmail.com, India.
- Existing Individual payments profile ending 5974 linked. AdSense dashboard confirmed "We've got your info".
- Website mockrep.onrender.com requires review; not approved. Exact inert verification meta tag staged, not deployed. No ad-serving script is live.
- Play merchant setup was submitted at 2:16 AM IST with the existing Individual profile. Approved public name RANJIT KUMAR SAHOO, support appsupportdesk.in@gmail.com, Computer Software category, statement name RANJITSAHOO. Owner explicitly approved public use of his home address at 2:13:40 AM IST. That address was reused. India-only and cross-border payment accounts created; cross-border BillDesk PA-CB KYC is in progress, not complete. The15% fee enrollment is completed and verified after explicit owner approval; both associated-account declarations are No. BillDesk application2611094300 is at Personal Info: email OTP passed, Individual and resident Indian Yes selected under owner approval. PAN, PAN name, DOB, mobile, additional family/address details and consents remain unsubmitted. Owner must enter sensitive KYC details directly.
- Support Gmail forwarding is saved and verified to ranjitkumarsahoo77@gmail.com with a copy kept in the support Inbox. Settings-level verification completed; no test email sent.

## Remaining gates
1. BillDesk cross-border KYC and any bank/identity/tax requirements through secure entry or owner action; fee enrollment is completed.
2. Support forwarding is complete.
3. Final pricing/limits owner approval and the approved US$20 funded reserve. Do not sell unusable AI before reserve is available.
4. Play app/listing, India/US base-plan prices, service account and permissions, real RTDN topic/authenticated push, licensed test track/device tests for purchase/cancel/pending/restore/expiry/refund/revocation. Upload only after separate owner instruction.
5. AdSense site verification/review, ads.txt if applicable, ad slots only on public practice pages, US privacy message/opt-outs/restricted data processing, policy/cookie/Data Safety/contains-ads declarations, ad approval.
6. Full end-to-end testing after actual configured services and final model policy, not only mocked API tests.
7. Deliberate production deployment decision. Production remains older source94c94b9 with AI verified OFF via US$0 daily/total caps. The new branch permanently enables paid-only policy; the old environment switch cannot restore free AI. No deployment or upload yet.

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
