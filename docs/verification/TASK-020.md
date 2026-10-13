# TASK-020 verification

Date: 2026-09-23. Status: DONE (local acceptance under ADR-007).
Cloud acceptance: NOT RUN, owner TASK-021.

## Scope

Started from clean 7e2d897468a7cc3f3bb675665c8efbe7e7b71fba, TASK-019 DONE.
Read AGENTS/status/tasks, latest changelog/decisions, relevant local-first/outbox/
workflow/notification ADRs, design observability requirements and current handlers,
queues/log modules/recovery runbooks. No unrelated changes or dependencies added.

## Acceptance evidence

- PASS: common allowlisted JSON schema/EMF, context reset on success and exception,
  no logged body/token/exception/address, Lambda request ID cannot be event-spoofed.
- PASS: upload reservation correlation reaches actual processor audit/outbox/log;
  submission workflow context and HTTP response correlation remain diagnostic links.
  Existing legacy document fallback remains deterministic.
- PASS: ten real producer fact cases verify required domain metric observations,
  normal DISPATCHED duplicate suppression and review duration for all three outcomes.
  Metrics are approximate; no atomic/exactly-once telemetry claim.
- PASS: paginated read-only monitor returns open review count and maximum pending
  ages, empty snapshot zeros; capped/error scans never emit a healthy heartbeat.
  Terraform restricts Scan to six status/time attributes on the exact table.
- PASS: mock plans represent both DLQ alarms; workflow failed/timed-out/aborted;
  Lambda >5% error rate with minimum ten invocations; partial-batch retry counters;
  durable pending ages; heartbeat missing; exact EventBridge rule dimensions;
  five-widget dashboard; native Lambda/Standard tracing and narrow telemetry IAM.
- PASS: IAM-only exact-fact outbox invocation dispatches once, repeated invocation
  does not publish again; malformed identity is rejected. Existing source retry,
  consumer isolation and E2E tests remain passing. No public endpoint added.
- PASS: operations runbook covers diagnosis, projected scan capacity, alarms,
  controlled original-queue redrive, exact-fact recovery and cloud evidence.
- API/event schema shapes, physical keys and business audit/transaction rules remain.
  Document gains internal correlation metadata; public DTOs remain whitelisted.

## Commands and outcomes

- PASS: py -3.13 scripts/dev.py check (exit 0).
  510 backend tests in 468.58 seconds; Ruff lint and format (77 files);
  mypy source/tests (72) plus scripts (4); frontend Prettier/ESLint/Vitest (1 test),
  TypeScript/Vite build; Python sdist/wheel build.
- PASS: from backend, .venv/Scripts/python.exe -m pytest
  tests/integration/test_observability.py -q --tb=short: 19 passed in 18.08 seconds.
- PASS: from backend, .venv/Scripts/python.exe -m mypy src tests ../scripts:
  76 source files, no issues.
- PASS: .tools/terraform-1.14.9/terraform.exe fmt -check -recursive infra.
- PASS: Terraform -chdir=infra/environments/dev init
  -backend=false -input=false -lockfile=readonly -no-color.
- PASS: Terraform -chdir=infra/environments/dev validate -no-color.
- PASS: Terraform -chdir=infra/environments/dev test -no-color:
  40 passed, 0 failed, final run includes per-rule EventBridge dimension correction.
  Mock providers only; no real Terraform plan/apply or credentials required.
- PASS: backend/.venv/Scripts/python.exe scripts/package_cases.py twice:
  SHA256 7814904a823bf90c14e81b541e1dcea853ac09534911f8dc65270cfe449cf53b.
  Compressed 16,395,213 bytes; expanded 22,546,561 bytes. Python -I -S imports from
  extracted ZIP for operations_monitor, notification_worker and outbox_publisher PASS.
- PASS: task-file inventory and Git diff whitespace checks.
- Initial failures corrected: decorator typing/metric mapping/import formatting;
  one new integration test used an invalid empty DynamoDB SK prefix (89 others
  passed that run). Corrected test and all production paths pass the final suite.
  Final AWS documentation review corrected EventBridge alarm dimensions before
  the last passing Terraform run.
- NOT RUN: hosted GitHub CI; local checks do not establish hosted results.
- NOT RUN: real EMF extraction, native traces and payload inspection, projected
  IAM enforcement, schedule/heartbeat, dashboard/alarm transitions/actions,
  actual Streams-expiry recovery or DLQ redrive. Owner TASK-021.

Ignored local logs: build/task-020-check.log and build/task-020-terraform.log.
No AWS writes, deployment, external notification or email was performed.

## Operational limits and next step

Domain counts and duration samples can duplicate or disappear at race/crash/log
boundaries. Strongly consistent scan pages do not form a transactional snapshot.
The 100-page/100-item monitor ceiling protects the initial dev workload; growth
needs review. Projection does not reduce DynamoDB read capacity consumed.
alarm_action_arns defaults empty (console/dashboard only); no notification recipient
or SNS subscription is invented. Native traces are sampled, not a single complete
async trace. Outbox recovery does not resend an already DISPATCHED fact to repair
target exhaustion. See ADR-022 and operations runbook for each boundary.

TASK-021 is READY for local preparation. Present concrete account/region/resources/
costs/tests/cleanup before seeking approval; real acceptance and approved cleanup
must pass before TASK-021 DONE and TASK-022.

## Exact files changed

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/case_api/command.py
- backend/src/case_api/health.py
- backend/src/case_api/query.py
- backend/src/common/logging/__init__.py
- backend/src/common/reviews/finalization.py
- backend/src/document_api/command.py
- backend/src/document_processor/handler.py
- backend/src/notification_worker/handler.py
- backend/src/operations_monitor/__init__.py
- backend/src/operations_monitor/handler.py
- backend/src/outbox_publisher/handler.py
- backend/src/review_api/command.py
- backend/src/review_api/query.py
- backend/src/workflow_create_review_task/handler.py
- backend/src/workflow_failure_handler/handler.py
- backend/src/workflow_finalize_case/handler.py
- backend/src/workflow_validate_case/handler.py
- backend/tests/integration/test_notifications.py
- backend/tests/integration/test_observability.py
- backend/tests/integration/test_outbox_publisher.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/022-operational-observability.md
- docs/runbooks/notifications.md
- docs/runbooks/operations.md
- docs/runbooks/workflow-recovery.md
- docs/tasks.md
- docs/verification/TASK-020.md
- infra/README.md
- infra/environments/dev/main.tf
- infra/environments/dev/operations.tf
- infra/environments/dev/tests/foundation.tftest.hcl
- infra/environments/dev/tests/operations.tftest.hcl
- infra/environments/dev/tests/workflow.tftest.hcl
- infra/modules/document_pipeline/outputs.tf
- infra/modules/lambda/main.tf
- infra/modules/notifications/main.tf
- infra/modules/notifications/worker.tf
- infra/modules/operations/alarms.tf
- infra/modules/operations/dashboard.tf
- infra/modules/operations/main.tf
- infra/modules/operations/variables.tf
- infra/modules/operations/versions.tf
- infra/modules/workflow/main.tf
- scripts/package_cases.py

## Documentation updated

- PROJECT_STATUS.md
- README.md
- backend/README.md
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/022-operational-observability.md
- docs/runbooks/notifications.md
- docs/runbooks/operations.md
- docs/runbooks/workflow-recovery.md
- docs/tasks.md
- docs/verification/TASK-020.md
- infra/README.md
