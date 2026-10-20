# NaviJob backend

Django/DRF owns authenticated sessions, private career data, resume versions,
reviewed jobs and immutable applications. See the [architecture](../docs/UNDERSTANDING.md)
and [root README](../README.md) for setup and the complete local preview workflow.

Use `--settings=config.settings.preview` for local migrations, seeding and the
preview server. It isolates SQLite, uploads and console mail from configured remote
services. Use `--settings=config.settings.test` for system checks, migration checks
and tests. Do not migrate a configured remote database during local validation.

## Operations

A confirmed application account with staff status and the
`core.moderate_marketplace` permission can use `/operator` on the frontend. Company
identity, recruiter authority and publication decisions record reasons and evidence
methods. Methods shown on company profiles must contain no sensitive details.
Applications and audit records are read-only in admin; hiring changes go through
server-validated transition APIs. Review queues show the oldest 100 requests.

Production settings require a private secret of at least 50 characters and HTTPS.
Configure private upload storage and real email delivery, run `collectstatic`, and
review database, backup, retention and erasure arrangements before a live pilot.
The new initial migrations for legacy waitlist/payment/subscription tables are for
fresh databases; existing installations must compare their actual schemas before
applying or marking them as present. No remote migration was performed here.

Static files in `data/` are fictional demo fixtures. Claims such as verified startup
or a sample candidate's experience are synthetic data, not established facts.
Billing models remain dormant; no payment provider is enabled by their migrations.
