# Center Pro integration and release status

## Implemented locally

| Area | Behavior |
| --- | --- |
| Owner/staff access | Single-use hashed email links, current assignment checks, session/CSRF, rate limits, center selection |
| Administrator | Password + TOTP endpoint, encrypted enrollment, replay checks, centers, assignments/revocation, last-owner guard, audit |
| Scheduling | Weekly hours, future resource slots, timezone/DST validation, overlap checks, block/unblock, protected confirmed slots |
| Requests | Search/filter/sort/pagination, staff manual confirmation, immutable booking price, safe duplicate confirmation |
| Pricing | Owner-only reviewed changes, expected-version conflict protection, old/new price and actor/reason history |
| Outreach | Owner-only targets, notes, status, paginated history; external rate-sheet sharing can be recorded |
| Patient | Consented self-pay link, price snapshot, exactly three date-and-period preferences, request queue, private status/confirmation; QR referral request |
| Estimates | Immutable versioned DRAFT records from the booking snapshot, printable draft output; no GFE issuance |
| Referral pad | Real QR code pointing at configured frontend origin and center referral page, printable layout |
| Owner summaries | Saved-data counts; no invented collected revenue |
| Market/billing | Clearly labelled scenario or unconnected state; no fabricated live feed, invoice or payment |

## Not production-complete

The following require external information/configuration or review and have not been substituted with fake success:

1. Existing MySelfPay identity, center, offer, booking and availability API/model mapping. Local models are a development implementation; do not blindly migrate duplicate identity/center/booking tables into the company database.
2. Existing custom hash router integration and agreed `/center-pro` deployment rewrites.
3. Production email provider and domain. SMTP adapter is implemented but unconfigured. SMS transport, retries/delivery callbacks and notifications are not implemented against a provider.
4. Public MySelfPay offer publishing, verified market/ZIP/hospital feeds, weekly target sourcing and revenue reports. Local price saves do not update the live website.
5. Stripe owner subscription account/product/customer mapping, integration and webhook/retry policy. Subscription UI remains unconnected. Patient payment is entirely out of scope.
6. Obtain the exact GFE wording/template reported as verified by the project owner; map provider identifiers and itemization, and implement timing and delivery. Drafts cannot be issued as compliant GFEs. Patient summaries explicitly say this.
7. Scheduled digest email generation/delivery, admin MFA recovery, real center contact/resource data and final permission mapping.
8. AWS/domain/secrets/HTTPS/proxy/database TLS setup, operational logging with token redaction, backup/retention and deployment checks. No deployment performed.
9. Browser interaction/visual acceptance, production Python 3.12 execution and PostgreSQL concurrent-write testing.

## API prefix and identity

All endpoints start `/api/center-pro`. Private APIs require session authentication, CSRF on writes and current center membership. Owner endpoints require owner; scheduling/estimates require staff. Admin endpoints require superuser plus MFA session flag. Cross-center identifiers are rejected. Role tags and request payloads do not grant privileges.

The isolated host uses Django SessionAuthentication and X-CSRFToken. Integrate with the existing `SelfPaySessionAuthentication` and X-Center-CSRF adapter before merging; do not run two competing account systems.

## Routes

- GET `/session`; POST `/logout`; development-only POST `/development-login`.
- POST `/auth/request` `{email}`; POST `/auth/verify` `{token}`; POST `/auth/admin` `{username,password,code}`.
- GET `/admin/centers`, `/admin/audit` (paginated).
- GET/POST `/admin/centers/:center/assignments`; POST `/admin/centers/:center/assignments/:membership/revoke`.
- GET `/centers/:center/overview`.
- GET `/centers/:center/requests?search=&status=&ordering=&page=&page_size=` (default 5, max 20); GET `/requests/:id`; POST `/requests/:id/confirm` `{slot_id}`.
- GET `/centers/:center/slots` candidate availability; confirmation always rechecks.
- GET/POST `/centers/:center/hours` (seven weekday objects, Monday=0).
- GET/POST `/centers/:center/availability`; POST `/availability/:slot/block` `{blocked}`. Naive entered times are interpreted in the center timezone. DST transition ambiguity is rejected.
- GET `/centers/:center/offers`; GET/POST `/offers/:id` `{price,expected_version,reason}`; GET `/offers/:id/history`.
- GET `/centers/:center/outreach`; GET `/outreach/:id`; GET/POST `/outreach/:id/activities` `{kind,note}`.
- GET `/centers/:center/rescue/offers`; POST `/rescue` `{offer_id,consent}` creates a seven-day bearer link and explicitly returns `delivery:not_sent`.
- GET/POST `/patient/:token` is bearer-authorized without account login; POST accepts `{patient_name,preferences}`. Repeated POST returns the existing request. Price and center come from the link, not the payload.
- GET/POST `/referral/:center` is public; POST validates `{offer_id,patient_name,preferences}` and returns an unguessable status link. Do not log or share bearer tokens.
- GET/POST `/centers/:center/requests/:booking/estimates` returns/creates immutable draft versions.
- GET `/centers/:center/referrals`, `/market`, `/subscription`, `/digest`.

History and list endpoints use `{count,next,previous,results}` where paginated. Validation returns 400, missing/other-center resources 404, permission denial 403, stale prices or unavailable slots 409, auth throttles 429. API clients handle errors and do not declare writes successful before the backend responds.

## Current validation

54 backend tests; 8 frontend tests; production frontend build; no pending model migrations. These do not replace browser QA or production integration/concurrency tests. See [DEVELOPER_HANDOFF.md](DEVELOPER_HANDOFF.md) for the completion sequence and acceptance criteria.

## Patient date and period preferences
New patient and referral submissions use `preferences`, exactly three distinct objects:
`[{"date":"2099-11-23","period":"morning"},{"date":"2099-11-23","period":"afternoon"},{"date":"2099-11-24","period":"morning"}]`.
Morning is 08:00–12:00; Afternoon is 12:00–17:00 in the sending center timezone, intersected with its working hours. Closed days, unavailable periods, ended periods and duplicates are rejected. There is no Evening option.
Staff receive three preference groups with matching center slots and overlap details, then manually confirm one exact slot. The full appointment must fit the selected period and current working hours. Legacy exact-time and slot-ID submissions remain supported for existing requests. No database migration is required.


## Final local review - 2026-11-23
- Backend: 54 regression tests pass; no pending model migration changes; pip dependency check passes.
- Frontend: production build and 8 tests pass; npm production dependency audit reports zero vulnerabilities.
- Fixed malformed non-ASCII administrator MFA input returning a server error.
- Patient preference slot groups now paginate at 20 slots, using zero-based `preference_page_0`, `preference_page_1`, and `preference_page_2` query keys with one-based page values. Each group includes count/page/page_size. Results after slot 60 are reachable; pagination buttons do not submit confirmation.
- Existing coverage includes membership isolation, role permissions, magic-link expiry/reuse, MFA replay, consent, working hours, preferred periods, price snapshots and appointment conflicts. Tests run against local SQLite; concurrent PostgreSQL behavior remains a release gate.
- Current development settings produce six expected deployment warnings (DEBUG, local key, HTTPS redirect, secure cookies and HSTS). A temporary production-settings check removes those six; HSTS include-subdomains and preload remain explicit deployment/domain-owner decisions. No real production database or deployment was tested.
- No fresh browser visual/interactivity pass was performed. Desktop/mobile and keyboard walkthroughs remain required before release.
- Official GFE issuance is NOT implemented: the local Center model only has name/timezone. Map authoritative legal name, address, contact details, provider identifiers, patient fields and service itemization from MySelfPay; validate completeness and save immutable issued snapshots before enabling patient delivery. Current estimates remain drafts.
- Still external: MySelfPay API/session mapping, production email/SMS, pricing/market synchronization, subscription billing, AWS/domain configuration and manager acceptance.
