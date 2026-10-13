# TASK-021 quota request and local verification - 2026-09-29

> Privacy note (2026-10-14): private account/resource identifiers and personal home paths have been redacted for the public-release candidate. Historical outcomes are unchanged; placeholders are not live targets.

Task status: BLOCKED. User explicitly authorized only the Lambda regional quota
request from 10 to 1000; no paid provisioned capacity, deployment or email.

## AWS evidence

MCP api_calls confirms PASS for STS GetCallerIdentity (expected project),
GetServiceQuota (10, adjustable), ListRequestedServiceQuotaChangeHistoryByQuota
(empty), RequestServiceQuotaIncrease, GetRequestedServiceQuotaChange and Lambda
GetAccountSettings. Region ap-southeast-2; project <REDACTED_AWS_ACCOUNT>.

- Quota: lambda / L-B99A9384 (Concurrent executions).
- Request ID: 67f8f7f522db429088c4d6029ac575cc5kM3zDV3.
- Submitted: 2026-09-29 05:28:00 UTC, desired 1000, initially PENDING.
- Latest request update: 2026-09-29 05:28:21 UTC, CASE_OPENED.
- AWS case: <REDACTED_SUPPORT_CASE>.
- Effective total/unreserved quota at readback: 10/10. Approval NOT RUN (not granted).

Reuse this request on follow-up; no duplicate or paid support subscription.
The service-created case is part of the authorized quota request. No separate
support correspondence was sent. No secrets, requester identity or tokens saved.

## Local verification

PASS: `py -3.13 scripts/dev.py check`:
backend Ruff check/format, mypy (73 source files plus 8 scripts), 560 pytest tests;
frontend Prettier/ESLint, 6 Vitest tests, TypeScript/Vite build; backend sdist/wheel.
PASS: `npm run check --prefix acceptance` (auth helper syntax).
PASS: `terraform fmt -check -recursive infra`.
PASS: dev and bootstrap `init -backend=false -input=false -lockfile=readonly`,
`validate`, `test`: dev 41 mock tests, bootstrap 1 mock test.

Terraform used isolated TF_DATA_DIR directories under build/task-021. Initial
provider downloads stalled; stopped only the two identified init processes and
retried using the existing locked 6.64.0 local provider directory via -plugin-dir.
Lockfiles were not modified. No remote backend initialization or real apply.

PASS: GitHub Actions run 36519484177, both baseline and terraform jobs succeeded
for published e405067c32a13b479a657303d87701ad1b20e72f. This is not hosted-CI evidence
for subsequent unpublished TASK-021 changes.

NOT RUN: new cloud deployment, real end-to-end journeys, cleanup of a new session,
retained-state reuse and outstanding 24-hour/14-day acceptance. Wait for effective
quota capacity and obtain separate deployment/test/cleanup authorization.

Files changed this turn: PROJECT_STATUS.md; docs/tasks.md; docs/CHANGELOG.md;
docs/CLOUD_ACCEPTANCE.md; docs/runbooks/short-cloud-acceptance.md; this record.
No application code change, no completion commit/push.
