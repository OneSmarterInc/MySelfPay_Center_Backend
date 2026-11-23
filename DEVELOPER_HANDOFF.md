# MySelfPay Center Pro: developer handoff and completion guide

Updated: 23 November 2026

## 1. Status and repositories

This is a working local implementation for integration review, not a production release. Core workflows and automated tests are implemented. External integrations and release acceptance remain incomplete.

- Frontend: https://github.com/OneSmarterInc/MySelfPay_Center_Frontend
- Backend: https://github.com/OneSmarterInc/MySelfPay_Center_Backend
- Delivery branch in both repositories: `codex/initial-implementation`.
- Existing application: https://github.com/OneSmarterInc/Myselfpay_Frontend and https://github.com/OneSmarterInc/MyselfPay_Backend.

The intended destination is routes/modules within existing MySelfPay. Separate repositories were used to develop without modifying the existing application. Do not deploy a second account or center database without agreeing the integration design.

## 2. Confirmed product rules

- Patient payments are handled by the center outside this portal. Do not implement patient Stripe checkout, payment-dependent booking confirmation, or the obsolete 72-hour payment hold.
- Patients submit exactly three distinct date-and-period combinations. Morning is 08:00-12:00 and Afternoon is 12:00-17:00 in the center timezone. There is no Evening option.
- Intersect periods with the sending center's saved working hours. Reject closed days, unavailable periods, ended periods and duplicate combinations.
- Staff select an actual resource/time within a submitted period, inspect overlaps and manually confirm. The full appointment must fit the period and current working hours. Patient preferences alone never reserve a slot.
- Requests from MySelfPay, self-pay links and QR referrals belong in the same queue. Confirmed appointments are accessible through the queue's status filter.
- Multiple owners have equal owner permissions. Staff currently have one staff role. Liaison/outreach is owner-only; there is no separate liaison/manager account.
- Super admin assigns/revokes owner and staff memberships. Role labels in a URL must never grant access.
- One assigned center: open its overview and hide Switch center. Two: switch directly. More than two: show the selector. Switching from a record detail or between roles opens Overview.
- Preserve prices on existing links, bookings and issued documents. New offer prices apply to new transactions.
- Collected revenue must come from an authoritative payment record; never calculate it from bookings or market forecasts. Completed scans also require an authoritative source.
- The proposed $100-per-center monthly owner subscription is separate from patient payments. Provider/product/account setup and final billing behavior remain unresolved.
- Keep the approved compact MySelfPay appearance, hamburger navigation, accessible labels and paginated tables. Manager approves final UI acceptance.

## 3. Stack and development setup

| Layer | Current implementation |
| --- | --- |
| Frontend | React/React DOM 19.3.1, JavaScript/JSX, plain CSS |
| Tooling | Vite 7.3.7, React plugin 5.2.0, Vitest 5.0.5 |
| Backend | Django 5.2.18, Django REST Framework 3.18.3 |
| Production target | Python 3.12, PostgreSQL/psycopg 3.3.6, Gunicorn 23.0.0 |
| Local tests to date | Python 3.14 and isolated SQLite; not production concurrency validation |

Backend pinned dependencies match the existing MySelfPay backend lockfile at handoff. Frontend shared framework/tool versions match its lockfile; feature-specific packages are not all required by Center Pro.

Clone both delivery branches into sibling frontend/backend directories. Use Python 3.12 for the receiving developer's environment. The following commands are for a NEW, ISOLATED development setup only:

```powershell
# Backend repository
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py seed_owner_demo
.\.venv\Scripts\python.exe manage.py provision_local
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Do not overwrite an existing `.env`, seed a company database, or apply the isolated schema to production. Demo commands require DEBUG and ENABLE_DEV_LOGIN. Sample account buttons are available locally; owner/staff sample emails are `owner@example.test` and `staff@example.test`. No sample credentials are production credentials.

```powershell
# Frontend repository, separate terminal
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to port 8000. `index.html` mounts React; screens are in `src/*.jsx`. The old standalone HTML preview is excluded from Git and the build.

## 4. Complete integration in this order

Ownership below is proposed; the developer and project owner must agree assignments and release scope.

### A. Identity, data and route mapping - first priority

- [ ] Inventory existing center, user, offer, request, resource, working-hours and payment models/APIs. Produce a field/ID mapping before migrations.
- [ ] Confirm the existing authentication and CSRF contract. Center Pro currently uses Django sessions and `X-CSRFToken`; adapt it to the existing MySelfPay session boundary rather than duplicating accounts.
- [ ] Preserve the agreed owner/staff magic-link experience while enforcing assignments on the server. Integrate super-admin password/TOTP, enrollment and a reviewed recovery process.
- [ ] Mount Center Pro routes in the existing frontend router, resolve hash/route collisions and establish the production API proxy. Current standalone routes such as `#/overview` are not a final deployment prefix.
- [ ] Replace sample fixtures/metrics with authoritative APIs. Agree synchronization direction and idempotent import identifiers; do not create duplicate booking requests on retries.
- [ ] Review migrations against the company schema. The local Center model currently contains only `name` and `timezone`.

Acceptance: real assigned users can access only their centers and permitted actions; revoked access fails on the next protected request; existing MySelfPay routes still work; all imported records have stable identity mapping.

### B. Booking and scheduling

- [ ] Map the existing patient booking payload to the current preference contract below.
- [ ] Map each scanner/room to a stable resource identifier. Do not infer that two resources with different display names are interchangeable.
- [ ] Populate working hours and real slot availability. Define how staff request new preferences when no submitted period works; the full patient follow-up workflow is not implemented.
- [ ] Exercise simultaneous confirmations against PostgreSQL. One resource cannot receive overlapping appointments, including requests from different channels.
- [ ] Preserve idempotent confirmation and immutable booking price snapshots.

Acceptance: patient request -> shared queue -> staff slot selection -> overlap check -> confirmation -> patient tracking page works with real data, including two competing staff confirmations.

### C. Messaging

- [ ] Configure production SMTP/provider and verified sender domain for magic links. DEBUG intentionally returns a local link and sends no email.
- [ ] Implement SMS delivery for consented self-pay links and appointment notifications using the selected provider.
- [ ] Define retry limits, delivery callbacks, idempotency, failure visibility and opt-out/consent handling. A generated link is not a delivered message.
- [ ] Implement owner digest scheduling/delivery if in first-release scope.

Acceptance: success is displayed only after the appropriate provider response; delivery failures are visible/recoverable; retries do not create duplicate requests or send uncontrolled duplicates.

### D. Patient-facing GFE - required before issuing documents

The project owner states the document wording has been verified. Obtain and attach that exact approved version. The current code only creates immutable estimate DRAFTS; it does not issue or deliver a completed GFE.

- [ ] Fetch center legal/provider information from the authoritative database/API: legal name, address/location, contact details and required provider identifiers. Confirm field availability; do not substitute the display name for legal identity.
- [ ] Map required patient information, scheduled/requested service details, itemized codes/charges and applicable inclusions/exclusions.
- [ ] Implement a completeness check that blocks issuance when required fields or approved wording are missing. Never promote demo values into patient documents.
- [ ] Store an immutable issued snapshot with document ID/version, source data, issue timestamp, actor and delivery status. Later price/provider edits must not rewrite an issued document.
- [ ] Render the approved patient template without sample/draft wording only for completed issued records. Preserve necessary estimate and patient-rights wording.
- [ ] Implement authorized download/delivery, audit history and correction/reissue behavior; agree timing with the provider's approved process.

Acceptance: issuing a complete record produces the approved patient document; incomplete data blocks issuance with actionable errors; old issued versions remain unchanged and access is scoped. Do not certify readiness by simply renaming `EstimateDraft` or removing notices.

### E. Owner pricing, outreach, reporting and subscription

- [ ] Connect reviewed offer updates to the public MySelfPay pricing source with version conflict handling. Local updates currently do not publish live prices.
- [ ] Supply verified local/hospital price benchmarks with source/date. Preserve unavailable states when evidence is absent.
- [ ] Connect weekly outreach target sourcing, agreed radius/eligibility and saved owner actions. Synthetic targets are not a live discovery process.
- [ ] Populate completed scans and any collected revenue from authoritative sources. Market opportunity remains an explicitly labelled scenario.
- [ ] Confirm subscription scope, account ownership, product/price/customer mapping and cancellation/failure rules. If approved, implement signed, idempotent subscription webhooks and reconciliation. Patient payment remains outside this portal.

Acceptance: public prices synchronize, historical price snapshots survive, metrics have traceable sources, and billing UI does not claim an unconnected action succeeded.

### F. Production deployment and operations

- [ ] Validate the app under Python 3.12/PostgreSQL and the target Docker image. Local Python 3.14/SQLite results are insufficient for this gate.
- [ ] Configure AWS hosting, domain, HTTPS, reverse proxy, database TLS, secrets and backups. The included Dockerfile is a starting point, not a verified AWS deployment.
- [ ] Set DEBUG=false and ENABLE_DEV_LOGIN=false. Configure strong DJANGO_SECRET_KEY, ALLOWED_HOSTS, FRONTEND_ORIGIN, CSRF_TRUSTED_ORIGINS and production DATABASE_URL.
- [ ] Confirm proxy/secure-cookie behavior, health checks, monitoring, error reporting, data retention and restore/rollback procedure.
- [ ] Redact patient-link and magic-link bearer tokens and sensitive patient data from logs. Establish appropriate access controls for database, object storage and document delivery.
- [ ] Decide HSTS subdomain/preload settings with the domain owner; do not enable them blindly across company domains.

Acceptance: staging deployment passes the complete workflow with production-like settings, recovery is documented, and no demo-login route or demo data is exposed.

## 5. Current API contract and code map

All current endpoints begin `/api/center-pro`. See `center_pro/urls.py` for exact routes and `INTEGRATION.md` for the endpoint inventory.

New public request body:

```json
{
  "patient_name": "<actual patient name>",
  "preferences": [
    {"date": "2099-11-23", "period": "morning"},
    {"date": "2099-11-23", "period": "afternoon"},
    {"date": "2099-11-24", "period": "morning"}
  ]
}
```

Dates above illustrate the format only. Patient link: POST `/patient/:token`. QR referral: POST `/referral/:center` with `offer_id` added. Price/center come from the server. Send exactly one preference format; legacy `preferred_times` and `preferred_slot_ids` remain compatibility inputs. Do not send `preferred_windows` as the new public payload.

Staff fetch GET `/centers/:center/slots?booking_id=:booking`. Period groups contain `slots`, `count`, `page`, `page_size` and overlap metadata. Use `preference_page_0`, `_1`, `_2` with one-based page values; groups paginate at 20 slots. POST `/centers/:center/requests/:booking/confirm` with `{ "slot_id": 123 }`. Confirmation rechecks membership, submitted preferences, working hours and conflicts.

General paginated responses use `{count,next,previous,results}`. Preserve 400 validation, 403 permission, 404 inaccessible/not-found, 409 conflict and 429 throttle handling. Never trust a role or center supplied by the browser without server authorization.

| Area | Files |
| --- | --- |
| Router, session and center switching | Frontend `src/App.jsx`, `src/api.js`, `src/useResource.js` |
| Patient form, admin, hours, estimates | Frontend `src/CompletePages.jsx` |
| Queue and scheduling confirmation | Frontend `src/Requests.jsx`, `src/RequestDetails.jsx` |
| Owner screens and dashboard | Frontend `src/OwnerPages.jsx`, `src/Dashboard.jsx`, `src/MarketSummary.jsx` |
| Shared UI | Frontend `src/components.jsx`, `src/Icon.jsx`, `src/styles.css` |
| Atomic booking confirmation | Backend `center_pro/services.py` |
| Period/working-hour intersection | Backend `center_pro/preferences.py` |
| Auth, MFA and throttling | Backend `center_pro/auth_flows.py` |
| API and local models | Backend `center_pro/views.py`, `full_views.py`, `owner_views.py`, `models.py` |

`center_pro/holds.py` and `tests/test_holds.py` are retired experiments, not the current booking flow. Do not wire them into production.

## 6. Verification and release checklist

```powershell
# Backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test center_pro --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pip check
# Run with actual staging production settings, not the demo .env:
.\.venv\Scripts\python.exe manage.py check --deploy

# Frontend
npm ci
npm test
npm run build
npm audit --omit=dev
```

Latest recorded results: 54 backend tests, 8 frontend tests, frontend build, migration drift check and backend dependency consistency pass. Frontend production dependency audit reported zero vulnerabilities at the time of checking. These are not evidence of completed browser, AWS, real-provider or PostgreSQL concurrent-write validation.

- [ ] Staff, owner and admin browser walkthrough; desktop and mobile; keyboard navigation and readable print/PDF output.
- [ ] One/two/many-center behavior; role changes; revoked access; expired sessions and magic links; direct unauthorized URLs.
- [ ] Patient self-pay and QR requests; duplicates; past/closed periods; timezone boundaries; unavailable slots; same/different-resource overlaps; paginated slot results beyond 60.
- [ ] Network failure, retry, validation messages, double-click/repeated POST and stale-price conflicts.
- [ ] Real provider notifications, approved GFE issuance/delivery and enabled subscription actions tested in staging.
- [ ] PostgreSQL concurrency, migrations, backup restore and deployment rollback verified.
- [ ] Remaining scope and ownership agreed; developer review and manager UI/workflow approval recorded.

Release only after the relevant checks pass or exclusions are explicitly agreed and the unavailable features remain clearly disabled. Share this handoff with the receiving developer now; do not describe the current repositories as a finished patient-production deployment.
