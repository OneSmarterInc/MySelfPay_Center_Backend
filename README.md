# MySelfPay Center Pro backend

Django 5.2.18 + DRF 3.18.3 module, with Python 3.12 / PostgreSQL as the upstream-compatible production target. Current local checks used Python 3.14 and isolated SQLite. No company repository or database was modified.

## First setup (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py seed_owner_demo
.\.venv\Scripts\python.exe manage.py provision_local
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Setup, migrations and seeding have already been performed locally. Do not overwrite an existing .env when restarting. The seed commands retain existing sample edits and confirmations. All demo commands require DEBUG and ENABLE_DEV_LOGIN.

## Authentication

Owner/staff magic links are hashed at rest, expire after 15 minutes and are single-use. Verification checks current memberships, not URL role tags. Local mode returns a development link without email. SMTP is the configurable standalone adapter; existing MySelfPay authentication must replace/map this boundary before integration.

Real administrator login requires a Django superuser password and TOTP. In a private terminal, create the account with `manage.py createsuperuser`, then use `manage.py enroll_admin USERNAME` to verify enrollment. The enrollment URI is a secret and must not be shared. Encrypted TOTP secrets depend on DJANGO_SECRET_KEY; plan key rotation before deployment. Accepted codes cannot be replayed. MFA recovery is not implemented and requires a reviewed administrative procedure.

The sample admin account has no usable password and is reachable only through the explicitly enabled local-development endpoint. Do not expose this endpoint or a development database publicly.

## Modules

- `models.py` / `migrations/`: reviewable local schema.
- `services.py`: atomic staff confirmation, overlap checks, safe retries and audit.
- `views.py` / `serializers.py`: sessions, scoped bookings, pagination and audit.
- `owner_views.py`: owner-only prices, optimistic version conflicts, histories and outreach.
- `auth_flows.py`: magic links, rate limits and administrator MFA.
- `full_views.py`: admin assignments, working hours, slots, patient/referral requests, immutable estimate drafts, QR and integration-status views.
- `management/commands/`: sample setup and private admin enrollment.
- `tests.py`, `test_owner.py`, `test_complete.py`: workflow and permission tests.

Legacy `center_pro/holds.py` and `tests/test_holds.py` are obsolete earlier experiments and are not imported. There is no patient-payment or 72-hour payment hold flow.

## Checks

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test center_pro
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

54 tests pass (2026-11-23). A live Vite-proxy API smoke flow also passed: consented link -> patient request -> staff confirmation -> private patient status -> estimate draft, plus owner/admin reads. PostgreSQL simultaneous-write and Python 3.12 runtime validation remain release gates.

See INTEGRATION.md for endpoint contracts and incomplete external dependencies.
