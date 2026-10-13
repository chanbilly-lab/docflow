# TASK-017 verification

Started: 2026-09-17. Completed: 2026-09-20. Status: DONE. Local acceptance under ADR-007.
Cloud acceptance: NOT RUN, owner TASK-021.

## Scope and acceptance evidence

Started from clean a0aa638bdec82ad1ded80e12111489e5c76a56b9, TASK-016 DONE.
Read AGENTS/status/tasks/changelog/DECISIONS, ADR-007/018/019, task-related
design/PRD/contracts and review/workflow/publisher/IAM code before implementation.

- First valid decision wins: assigned subject, current Case version/state/attempt
  and task decision/status/checkRevision guards. Tests interleave competing
  different/same decisions, checklist edits, technical failure and attempt changes.
- Repeated requests: UUID key plus canonical payload hash, stored on immutable task.
  Same request replays; changed key/body rejects. One decision audit is retained.
- Persisted callback retry: durable COMPLETED/PENDING task before SendTaskSuccess.
  Failures retain exact output; same request resends it. Closed/expired token is
  not delivery proof. Accepted-send/lost-response and failed acknowledgement recover
  from matching workflow finalization. No background scheduler is claimed.
- Token boundary: only backend stored token is sent to AWS. HTTP DTOs and event
  contracts omit token, execution ARN, key/hash, callback output and internal state.
- Three outcomes: actual checked-in ASL choice points to the finalizer with original
  input/execution and saved output. Case/task/audit/outbox commit atomically.
  Replays emit no new outcome; mismatched execution/attempt/decision fails closed.
  Concurrent finalizer, delivery acknowledgement and failure roll back and retry.
- Task history: findings cannot change after decision; technical failure closes
  task without erasing accepted decision, and excludes failed task from queues.
  Pending completed task permits guarded fresh-token generation refresh.
- All eleven real local producers pass routed schemas and custom-bus publication.
  Direct event publication remains exclusive to the existing publisher.
- ADR-020 resolves task-owned admin assignment and NULL/absent compatibility;
  API 0.9.0, finalization event schemas, design/PRD and runbook are synchronized.

## Commands and results

- PASS: targeted decision/event integration suite, 51 tests before additional
  acknowledgement/finalizer-race coverage.
- PASS: backend Ruff lint, Ruff format, mypy including scripts after final audit
  attribution correction.
- PASS: py -3.13 scripts/dev.py check on 2026-09-20: 471 backend tests,
  Ruff lint/format, mypy, frontend Prettier/ESLint/Vitest (1 test)/TypeScript/Vite,
  Python sdist/wheel builds. Rerun after interrupted process output was unavailable.
- PASS: final targeted decision regression, 39 tests, including acknowledgement
  loss, finalizer races and compatibility cases.
- PASS: Terraform readonly locked init with backend disabled, fmt -check -recursive,
  validate and test: 34 provider-mocked tests. Added assertions cover four JWT
  command routes, callback action scope and three original-context finalizers.
- PASS: final package_cases.py twice produced SHA256
  a69e203f6af4e936ba1abaf18a01bf300358c9d2d44908153b60d556208548fd.
  Compressed 16,388,321 bytes; expanded 22,527,557 bytes, within 50/250 MiB limits.
- PASS: Python -I -S imports review command, finalizer, failure handler, creator
  and publisher from build/cases.zip with no site packages.
- PASS: git diff --check.
- NOT RUN: real AWS deployment, Standard waiting/callback behavior, JWT/IAM
  enforcement, DynamoDB concurrency/GSI propagation and service delivery.
  Explicitly deferred to TASK-021; no plan/apply or cloud write executed.
- NOT RUN: hosted CI result. Local checks do not establish hosted execution.

Initial local failures were test-only Decimal schema validation before wire
serialization, formatting/type issues; fixed and rerun. A later audit attribution
correction uses the actual review command worker and original decision correlation;
the final 39-test regression passed after that correction.

## Limits and handoff

No runtime dependencies added. Tests use real application transactions over Moto
and controlled Step Functions doubles/SDK Stubber, not a hosted Standard service.
Pending callback recovery requires the same authenticated key/body API replay.
TASK-018 owns replacement/resubmission/new-attempt E2E. Live acceptance and explicit
short-lived deployment/cleanup approval remain TASK-021 under ADR-007.

Full rerun log is local-only build/task-017-check.log (ignored). Previous Terraform
and ZIP evidence was collected September 17 against the same implementation.

## Files changed

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/common/cases/workflow_state.py
- backend/src/common/reviews/creation.py
- backend/src/common/reviews/decisions.py
- backend/src/common/reviews/finalization.py
- backend/src/common/reviews/query.py
- backend/src/outbox_publisher/handler.py
- backend/src/review_api/command.py
- backend/src/workflow_finalize_case/__init__.py
- backend/src/workflow_finalize_case/handler.py
- backend/tests/integration/test_domain_events.py
- backend/tests/integration/test_review_commands.py
- backend/tests/integration/test_review_decisions.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/PRD.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/020-review-decisions.md
- docs/api/openapi.yaml
- docs/events/README.md
- docs/events/additional-information-requested.schema.json
- docs/events/case-approved.schema.json
- docs/events/case-rejected.schema.json
- docs/events/domain-event.schema.json
- docs/runbooks/workflow-recovery.md
- docs/tasks.md
- docs/verification/TASK-017.md
- infra/README.md
- infra/environments/dev/tests/reviews.tftest.hcl
- infra/environments/dev/tests/workflow.tftest.hcl
- infra/environments/dev/workflow.tf
- infra/modules/api/review_commands.tf
- infra/modules/lambda/database.tf
- infra/modules/lambda/main.tf
- infra/modules/lambda/review_callback.tf
- infra/modules/workflow/definition.asl.json
- infra/modules/workflow/main.tf
- infra/modules/workflow/variables.tf
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
- docs/adr/020-review-decisions.md
- docs/api/openapi.yaml
- docs/events/README.md
- docs/events/additional-information-requested.schema.json
- docs/events/case-approved.schema.json
- docs/events/case-rejected.schema.json
- docs/events/domain-event.schema.json
- docs/runbooks/workflow-recovery.md
- docs/tasks.md
- docs/verification/TASK-017.md
- infra/README.md

## GitHub publication

Automatic commit/push follows complete local verification under AGENTS section 7.1.
The completion response reports the commit and verified remote hash. Publication
does not authorize or trigger AWS deployment.
