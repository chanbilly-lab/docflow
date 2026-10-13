# TASK-019 verification

Date: 2026-09-21. Status: DONE, local acceptance under ADR-007.
Cloud acceptance: NOT RUN, owner TASK-021.

## Scope and acceptance evidence

Started from clean 90eebcd31151982638967236abafbb5782d5d679 (TASK-018 DONE).
Read operating contract, current state/tasks/changelog/decisions, relevant ADRs,
notification requirements, existing queue, publisher, auth and packaging code.

- PASS: Terraform represents two custom-bus rules routing the four approved
  docflow.case types as raw envelopes into encrypted notification SQS.
- PASS: worker compares envelopes with committed outbox facts and deduplicates
  business eventId, including transport-ID changes and reordered JSON keys.
  Conditional owner leases guard concurrent delivery; expired work can retry.
  Completed receipts have no TTL. No public event or API schema changes.
- PASS: configured reviewer recipient and exactly one enabled Cognito requester
  with matching sub and verified email; missing/ambiguous/unverified users retry.
- PASS: SES rejection returns a failed batch item and preserves all Case business
  rows/audits/outbox. Mixed batches retain successful acknowledgements.
- PASS: modeled main/DLQ redrive after five receives, 360-second visibility,
  four-day main/14-day DLQ retention, TLS enforcement and exact-resource IAM.
- PASS: empty email configuration disables rules and omits sender Lambda/mapping;
  configured topology is exercised with mock providers, including dev composition.
- Known delivery limit: an accepted email with lost response/failed receipt write
  can resend on retry. A dedicated test demonstrates this at-least-once boundary.
  SES acceptance does not establish inbox delivery. See ADR-021.
- No AWS writes, identity verification, deployment or email sends performed.

## Commands and real results

- PASS: py -3.13 scripts/dev.py check
  491 backend tests (424.66 seconds), Ruff lint/format, mypy (73 source files),
  frontend Prettier/ESLint/Vitest (1 test)/TypeScript/Vite, Python sdist and wheel.
- PASS: (from backend) .venv/Scripts/python.exe -m pytest
  tests/integration/test_notifications.py -q --tb=short: 18 passed in 40.63 seconds; final full run includes
  subsequent structured-log changes.
- PASS: backend/.venv/Scripts/python.exe scripts/package_cases.py, twice with
  identical SHA256 6bad410e100638770ca4a5c5f079643f147e3faf8feef4de02f8cce3c873b86b.
  ZIP 16,391,501 bytes; expanded 22,536,813 bytes. Isolated Python -I -S import of
  notification_worker.handler from extracted ZIP PASS.
- PASS: .tools/terraform-1.14.9/terraform.exe fmt -check -recursive infra
- PASS: Terraform -chdir=infra/environments/dev init
  -backend=false -input=false -lockfile=readonly -no-color
- PASS: Terraform -chdir=infra/environments/dev validate -no-color
- PASS: Terraform -chdir=infra/environments/dev test -no-color
  38 passed, 0 failed, mock providers only; no real plan/apply.
- PASS: Git diff whitespace and task-file inspection; no credential/state artifacts.
- Initial checks found Ruff wrapping, a boto3 typed-kwargs issue and unknown mock
  queue ARN values. These were corrected before the passing checks above.
- NOT RUN: hosted GitHub CI. Local checks do not establish its result.
- NOT RUN: live SES acceptance/delivery/sandbox, real Cognito lookup/IAM, actual
  EventBridge/SQS/Lambda retries, DLQ/redrive and timing. Owner TASK-021.
  Mock tests do not establish real service guarantees.

Local ignored logs: build/task-019-check.log and build/task-019-terraform.log.
No dependency changes. Source packaging includes the new worker.

## Exact files changed

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/notification_worker/__init__.py
- backend/src/notification_worker/handler.py
- backend/tests/integration/test_notifications.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/PRD.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/021-domain-notifications.md
- docs/events/README.md
- docs/runbooks/notifications.md
- docs/tasks.md
- docs/verification/TASK-019.md
- infra/README.md
- infra/environments/dev/notifications.tf
- infra/environments/dev/tests/notifications.tftest.hcl
- infra/modules/auth/outputs.tf
- infra/modules/notifications/main.tf
- infra/modules/notifications/variables.tf
- infra/modules/notifications/versions.tf
- infra/modules/notifications/worker.tf
- scripts/package_cases.py

## Documentation updated

- PROJECT_STATUS.md
- README.md
- backend/README.md
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/PRD.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/021-domain-notifications.md
- docs/events/README.md
- docs/runbooks/notifications.md
- docs/tasks.md
- docs/verification/TASK-019.md
- infra/README.md
