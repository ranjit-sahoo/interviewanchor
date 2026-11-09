# InterviewAnchor release check, November 9, 2026

Status: not yet ready for Play submission. User approval is required after readiness is reported. No Play Console upload performed.

## Completed evidence

- Exact InterviewAnchor branding across current app/repo/Android labels; package and existing signing certificate preserved for compatibility.
- Signed AAB/APK 1.0.6, code 7, target SDK 36. Signature identity checked against the original compatible key. This does not prove runtime install/update.
- Python 3.11 with production requirements: 277 automated tests pass, including mail transport, privacy-log formatting and authorization tests.
- Dependency audit: 72 installed packages, no known vulnerabilities in the audit result after pypdf 6.21.4 update. This is a point-in-time advisory check, not a security certification.
- Browser UI rounds 1-4: guest interview/report/PDF, accounts, tools, mobile journey pass in mock mode. Rounds 5-8: security probes, keyboard/reduced-motion, layout and sampled contrast pass.
- Stale tests corrected to actual contracts: guest interview IDs are secret bearer capabilities; another browser with the same bearer can intentionally resume. A changed bearer is rejected. Admin token failures are concealed as 404. Escape closes the navigation drawer, not an inline account form.
- Ten pages at four widths: no horizontal overflow; sampled CLS within 0.1. Mobile header wrapping after the longer brand name fixed and checked in screenshots.
- Practice voice now uses saved accent/rate, default en-US/1.00x; mocked browser speech tests cover US/GB and malformed saved preferences. Real speech quality is not established by these tests.
- Real live-AI synthetic QA interview: three questions, answers, scoring and final report completed, with mock_mode=false. Other local mock UI tests do not prove every live AI feature.
- Generated report, prep and resume PDFs inspected visually for readability and correct brand.
- Fixed actual live-log bug: prior bearer-path redaction broke Uvicorn AccessFormatter by clearing its five arguments. New filter preserves argument shape; regression tests exercise the real formatter. Screening private-link paths are also redacted.
- IA feature graphic, store icon, four phone-sized browser screenshots, English listing/release notes/data-safety draft prepared and privately backed up. Browser captures show the TWA web UI, not an Android system runtime.

## Still open

- Brevo free signup approved and Google sign-in completed. Postal address requested by onboarding has not been supplied/approved; no address inferred or exposed. No card/paid plan. HTTPS integration is implemented but not enabled. Real inbox delivery/code verification still untested.
- Physical Android install, in-place update from the prior compatible release, microphone permission, real transcription/playback, file upload and PDF download need a device check. No available emulator runtime established.
- Play Console must validate account/app-access, IARC, data safety and the uploaded bundle after the user's upload approval. App signing certificate/assetlinks may need the Console's actual signing certificate.
- Naming/trademark knockout research is not legal clearance.
- AI output remains fallible: a live rewrite introduced example details not given by the synthetic candidate. Existing invented-detail warnings remain important; no factuality guarantee.
- Local load tests are SQLite-only and not proof of production/free-host capacity.

## Sources

- Render SMTP restriction: https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports
- Brevo free API: https://www.brevo.com/features/email-api/
- Brevo transport schema: https://developers.brevo.com/reference/send-transac-email
- Play assets: https://support.google.com/googleplay/android-developer/answer/9866151
- Play listing limits: https://support.google.com/googleplay/android-developer/answer/9859152?hl=en
- Play data safety: https://support.google.com/googleplay/android-developer/answer/10787469
