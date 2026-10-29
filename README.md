# NaviJob

A Django/DRF and Next.js job platform with private candidate profiles, PDF resumes,
reviewed applications and company-scoped recruiter workspaces. The interface follows
the selected Sage & Forest design. See [the architecture](docs/UNDERSTANDING.md)
and [product scope](PRODUCT_PLAN.md).

## Run a fictional local preview

Use Python 3.10+ and Node.js 20.9+ with npm. From the repository root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements/base.txt
cd backend
.venv/bin/python manage.py migrate --settings=config.settings.preview
.venv/bin/python manage.py seed_preview --settings=config.settings.preview
.venv/bin/python manage.py runserver 127.0.0.1:8100 --settings=config.settings.preview
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev -- --hostname localhost --port 3100
```

Open `http://localhost:3100`. Next.js proxies `/api/` to Django at port 8100.
Use the same hostname throughout so session and CSRF cookies stay together.
`BACKEND_URL` overrides the proxy destination when starting Next.js.

Seeding is opt-in and repeatable. It preserves existing credentials and workflow
states. It creates these fictional accounts with the initial password
`NaviJob-Preview-42!` (override with `seed_preview --password ...`):

| Account | Workspace |
| --- | --- |
| `candidate@sample.navijob.test` | `/candidate` |
| `recruiter@sample.navijob.test` | `/recruiter` |
| `operator@sample.navijob.test` | `/operator` |

Preview settings always use `backend/.preview.sqlite3`, console email and
`backend/.preview-uploads/`, regardless of configured database or email environment
variables. Seeding refuses normal/production settings and non-SQLite databases.
All seeded roles and companies are fictional and labeled as samples. Register a
new account to exercise onboarding; confirmation/recovery links print in the backend
terminal. Preview accounts and the fixed preview secret must stay local.

## Checks

```bash
cd backend
.venv/bin/python manage.py check --settings=config.settings.test
.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.settings.test
.venv/bin/python manage.py test --settings=config.settings.test --noinput
cd ../frontend
npm run lint
npx tsc --noEmit
npm run build -- --webpack
```

Tests use isolated SQLite and in-memory uploads. Do not use a configured remote
database for local validation. Production setup must provide a private secret,
database, email delivery, HTTPS origins and private file storage; environment names
are listed in the example files. Collect Django static files before serving admin.

The real-browser journeys require Node.js 22+, a running isolated preview and a
Chrome debugging session. They create fictional local accounts and exercise actual
forms and cookies. Screenshots stay under `/tmp/navijob-browser-artifacts`.

```bash
google-chrome --headless=new --disable-gpu --remote-debugging-port=9341 --user-data-dir=/tmp/navijob-browser-review about:blank
cd frontend
npm run test:browser
npm run test:accessibility
```

Use `CDP_URL`, `NAVIJOB_BROWSER_URL`, `NAVIJOB_SAMPLE_PASSWORD` and
`NAVIJOB_BROWSER_ARTIFACTS` to override local defaults. Journeys refuse a nonlocal
frontend URL. The preview database must be seeded first; normal/remote databases
are never used by the journey token helpers.

## Data and operations

Candidates choose what to share through a signed application review. Submissions
keep immutable profile and PDF copies. Recruiters require separate company and
authority review; private notes stay separate from candidate-visible history.
Operators need a confirmed application account, staff status and the `core.moderate_marketplace`
permission. `/operator` provides company, authority and job review queues, listing
report resolution and deletion-request review with recorded reasons.

Privacy settings provide an account-owned JSON export and a deletion-request
workflow. Approval disables access; physical erasure, retention decisions, backups
and employer-downloaded copies need an operational process. No complete erasure
or hiring outcome is implied. Application inbox updates are in-product only.

This local product is not a live hiring pilot. Production email, storage durability,
malware scanning, backup/restore, retention/erasure operations and real employer
participation require separate verification before launch. AI screening, external
ATS automation and payments are deferred.
