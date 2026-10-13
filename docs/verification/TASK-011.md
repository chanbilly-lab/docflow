# TASK-011 verification

Date: 2026-09-16. Status: DONE. Local acceptance under ADR-007.
Cloud checks: NOT RUN, owner TASK-021.

## Scope and acceptance

Started from clean 1abf10a2e32becb8056600ddba3828a0e2c622e6 with TASK-010 locally DONE.
Read AGENTS, PROJECT_STATUS, tasks, CHANGELOG, DECISIONS, ADR-004/007/013,
Technical Design 6.8/8.5/19, PRD reliability and current event/producer contracts.

- Existing Case state/audit/outbox and document result/audit/outbox transactions
  remain intact and their integration regressions run. No direct command publishing.
- Terraform filter matches INSERT/MODIFY plus typed NewImage OUTBOX/PENDING only.
- Actual local DynamoDB Streams records from a committed Case reach the handler.
- Local SDK EventBridge accepts Case/document events with preserved business IDs
  and schema-valid serialized integer values; current state becomes DISPATCHED.
- DISPATCHED replay sends nothing; accepted-send/failed-mark replay retains identical
  detail and eventId. Concurrent dispatch succeeds; mutated fact prevents marking.
- Failed/empty/malformed EventBridge entry results, network error, missing bus and
  invalid outbox do not mark dispatched. First batch failure returns its sequence.
- Safe logging and default-bus rejection have tests. No new runtime dependencies.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | 250 backend tests including 36 publisher tests; Ruff lint/format; mypy 38 source/test files plus 4 scripts; frontend lint/format/1 test/type/build; Python sdist/wheel |
| terraform init -backend=false -input=false -lockfile=readonly | PASS | New local module/test paths initialized; lock unchanged |
| terraform fmt -check -recursive infra | PASS | Final format |
| terraform validate | PASS | Final dev configuration |
| terraform test | PASS | 22 mocked plan runs including exact publisher IAM/filter/retry and disabled dev mapping |
| scripts/package_cases.py twice | PASS | Identical SHA-256; publisher included; compressed <50 MiB and uncompressed <250 MiB |
| py -3.13 -I -S isolated ZIP import/empty stream batch | PASS | Publisher runs without site-packages |
| git diff --check | PASS | Final whitespace check |
| Live AWS and hosted CI | NOT RUN | No deployment authorized; deferred TASK-021 |

Terraform executable .tools/terraform-1.14.9/terraform.exe; init/validate/test use
-chdir=infra/environments/dev. Packaging uses backend/.venv/Scripts/python.exe.
The pre-final targeted test had 27 passes and one fixture failure, corrected before
the full passing run. No failing checks are left unresolved.

## Corrections and limits

Initial missing-bus test removed a Moto bus by ARN, which Moto does not normalize;
corrected fixture deletion to its name. Terraform filter block is a set, so the
assertion uses one(). Packaging formatting uses backend's canonical config.
AWS IAM reference confirmed ListStreams needs Resource *; data reads stay scoped.

No local test proves AWS IAM, shard ordering, stream retry/checkpoint timing,
EventBridge delivery or hosted CI. No AWS resources deployed. Dev stream mapping
is intentionally disabled until TASK-012 creates the actual bus and enables it.
At-least-once duplicates are possible between accepted send and dispatch update.
Stream retention is 24 hours; retained PENDING rows require controlled recovery
after missed/expired stream delivery. TASK-020/021 own monitoring/runbook/live proof.
See ADR-014 for the bus preflight race and recovery boundary.

## Exact changed files

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/outbox_publisher/__init__.py
- backend/src/outbox_publisher/handler.py
- backend/tests/integration/test_outbox_publisher.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/014-outbox-stream-publication.md
- docs/events/README.md
- docs/tasks.md
- docs/verification/TASK-011.md
- infra/README.md
- infra/environments/dev/outbox.tf
- infra/environments/dev/tests/outbox.tftest.hcl
- infra/modules/database/outputs.tf
- infra/modules/lambda/database.tf
- infra/modules/lambda/main.tf
- infra/modules/lambda/outbox.tf
- infra/modules/lambda/outputs.tf
- infra/modules/lambda/variables.tf
- scripts/package_cases.py
