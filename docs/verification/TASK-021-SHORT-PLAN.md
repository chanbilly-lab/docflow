# TASK-021 shortened acceptance preparation - 2026-09-29

> Privacy note (2026-10-14): account-specific billing/credit details and private support identifiers are withheld for public release. Historical technical outcomes are unchanged; redacted details are not live targets.

Status: BLOCKED (live acceptance); local implementation checks PASS.

Changed: scripts/cloud_session.py; backend/tests/unit/test_cloud_session.py;
PROJECT_STATUS.md; docs/tasks.md; docs/CHANGELOG.md; docs/DECISIONS.md;
docs/CLOUD_ACCEPTANCE.md; docs/runbooks/cloud-acceptance.md;
docs/runbooks/short-cloud-acceptance.md; this record.

Read-only MCP calls verified successful API execution: STS GetCallerIdentity,
Lambda GetAccountSettings, Free Tier GetAccountPlanState, Service Quotas
ListServiceQuotas. Expected project/region confirmed; account-specific billing/credit details withheld for privacy;
Lambda total/unreserved concurrency 10/10, zero functions. Regional quota
L-B99A9384 is adjustable. No request, deployment, email or billing mutation made.
Two initial MCP validation/naming attempts failed before a successful corrected
read; no cloud-write operation was attempted.

Tests (backend virtual environment Python):
- PASS: `-m pytest backend/tests/unit/test_cloud_session.py -q` (41 tests).
- PASS: `-m ruff check --config backend/pyproject.toml scripts/cloud_session.py backend/tests/unit/test_cloud_session.py`.
- PASS: project-config Ruff format; strict mypy on scripts/cloud_session.py.
- Initial root-config lint reported inherited rule differences; project-config
  rerun passed. No broad exception/logging safety behavior was weakened.
- NOT RUN: Terraform/cloud E2E; no infrastructure definition changed or new
  deployment approved. The guard uses mocked service responses locally.

The new guard fails closed for missing/invalid data and insufficient capacity,
stops bootstrap/deploy before initialization and rechecks before apply. Existing
protection-only cleanup tests pass without any deployment capacity dependency.
The 100+1 threshold is a conservative published-floor check, not discovery of the
managed project's exact minimum. Deployment-time races still require cleanup.
Operator time limits are a runbook schedule, not an automated cost/termination cap.
TASK-021 remains BLOCKED; no misleading completion commit/push.
