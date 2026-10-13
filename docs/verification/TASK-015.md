# TASK-015 verification

Date: 2026-09-17. Status: DONE. Local acceptance under ADR-007.
Cloud acceptance: NOT RUN, owner TASK-021.

## Scope and acceptance

Started from clean b99f307124276f709955094dd29d8500880f9dc3; TASK-014 DONE.
Read AGENTS/status/tasks/changelog/decisions, ADR-007/008/017, relevant design/PRD,
workflow/template/Case contracts, persistence, packaging and infrastructure.

- Callback worker validates original execution/submission identity and Case state.
  Deterministic task ID, bound immutable template and revision guard. Prepare up
  to 98 hidden NOT_REVIEWED skeletons, then publish Task/Case/audit/outbox atomically.
  Interruption, conditional race and concurrent creation recover with one task/fact.
- Same invocation is idempotent; newer callback generations refresh the backend
  token with audit; stale generations cannot overwrite it. Findings are preserved.
  Tokens are absent from HTTP DTOs, event detail, errors and logs.
- ASL uses lambda:invoke.waitForTaskToken and trusted context. Lambda returns taskId;
  Standard waits. Technical timeout is 14 days and is not retried as another wait.
  Catch keeps original identity; failure accepts REVIEW_PENDING/IN_REVIEW.
- Reviewer/admin available and mine GSI1 queries, scoped cursors and detail enforce
  current assignment and Case eligibility. Consistent base reads filter stale GSI
  candidates. No Scan; completed assigned history remains readable. Pre-claim
  detail does not widen Case GET. Requester-only users receive 403.
- Public detail includes task, Case, documents and sorted bound checklist instructions.
  API 0.7.0 and CaseReadyForReview routed/detail schemas agree with actual producers.
  Existing publisher delivers the seventh fact type through the custom bus.
- Terraform wires existing log groups, exact callback worker invocation, two JWT
  GET routes, CASE-transaction-only creator IAM and table/GSI1-only query reads.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | 374 backend tests in 299.49s; Ruff lint/format; mypy 57 source/test files + 4 scripts; frontend Prettier/ESLint/Vitest 1/TypeScript/Vite; Python sdist/wheel |
| Targeted review/workflow pytest | PASS | 56 tests in 72.39s; three further concurrent/history/access tests included in final full run |
| terraform init -backend=false -input=false -lockfile=readonly -no-color | PASS | Local modules initialized; existing AWS 6.64.0 lock unchanged |
| terraform fmt -check -recursive infra | PASS | Final infrastructure formatting |
| terraform validate -no-color | PASS | Dev composition valid |
| terraform test -no-color | PASS | 31 provider-mocked plans including callback timeout/retry/context, routes, creator/query IAM |
| scripts/package_cases.py twice | PASS | SHA256 identical; compressed 16,377,929 / expanded 22,495,521 bytes, below Lambda limits |
| Python -I -S isolated ZIP imports | PASS | New creator/query/common modules and existing command/publisher load using bundled dependencies |
| OpenAPI local refs / ASL graph | PASS | All references/targets resolve, FoundationComplete removed |
| git diff --check / changed-file credential-pattern review | PASS | No whitespace errors, credentials/state/private keys in task inventory |
| Live AWS / hosted CI | NOT RUN | No cloud write authorization; callback engine/IAM/GSI propagation evidence deferred to TASK-021 |

Terraform .tools/terraform-1.14.9/terraform.exe uses -chdir=infra/environments/dev
for init/validate/test. No real AWS plan/apply or deployment was run.
ZIP SHA256: a1efbeac68619174a76fefae69b61dc04bdc116a7e1e66b8bf48b4061d702076.

Initial formatting/SDK typing and documentation whitespace issues were corrected
before final passing checks. No dependency or provider-lock changes.

## Verification limits and handoff

Local DynamoDB/EventBridge use Moto. The checked-in ASL subset runner invokes real
workers and stops at callback waiting; it does not fabricate a callback completion.
Infrastructure assertions verify configuration, not the AWS engine or IAM runtime.
Real token reissuance/retry/timeout and GSI eventual consistency remain TASK-021.

TASK-016 owns claim/start/check mutations; require an existing task before changing
prepared checks, and conditionally update assignment/GSI1 with audit. No check result
may be reset during callback retry. Initial dueAt = submission +48h is independent
of the 14-day technical timeout. Hidden interrupted preparation rows have no TTL.

TASK-017 owns callback delivery/decision finalizers and terminal task lifecycle.
The intermediate ReviewCallbackReceived terminal is not business approval.
Failure may retain a PENDING/active task, but active queues exclude failed Cases.
No complete human-review lifecycle or real AWS acceptance is claimed.

## Exact files changed

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/common/cases/workflow_state.py
- backend/src/common/reviews/__init__.py
- backend/src/common/reviews/creation.py
- backend/src/common/reviews/query.py
- backend/src/outbox_publisher/handler.py
- backend/src/review_api/__init__.py
- backend/src/review_api/query.py
- backend/src/workflow_create_review_task/__init__.py
- backend/src/workflow_create_review_task/handler.py
- backend/tests/integration/test_domain_events.py
- backend/tests/integration/test_reviews.py
- backend/tests/integration/test_workflow.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/017-workflow-foundation.md
- docs/adr/018-review-tasks.md
- docs/api/openapi.yaml
- docs/events/README.md
- docs/events/case-ready-for-review.schema.json
- docs/events/domain-event.schema.json
- docs/runbooks/workflow-recovery.md
- docs/tasks.md
- docs/verification/TASK-015.md
- infra/README.md
- infra/environments/dev/health.tf
- infra/environments/dev/tests/reviews.tftest.hcl
- infra/environments/dev/tests/workflow.tftest.hcl
- infra/environments/dev/workflow.tf
- infra/modules/api/reviews.tf
- infra/modules/api/variables.tf
- infra/modules/lambda/database.tf
- infra/modules/lambda/main.tf
- infra/modules/lambda/variables.tf
- infra/modules/workflow/definition.asl.json
- infra/modules/workflow/main.tf
- infra/modules/workflow/variables.tf
- scripts/package_cases.py

## GitHub publication

Automatic commit/push follows completed local verification under AGENTS 7.1.
The task commit contains this exact inventory; publication result is reported in
the completion response. No AWS deployment is triggered by this authorization.
