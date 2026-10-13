# TASK-013 verification

Date: 2026-09-16. Status: DONE. Local acceptance under ADR-007.
Cloud acceptance: NOT RUN, owner TASK-021.

## Scope and acceptance

Started from clean 04a9970eba30e82bb586c308a751254b2c54063d.
Read operating rules, project/task/changelog/decisions, relevant ADRs, design/PRD,
API/events, repository and document transactions before implementation.

ADR-016 explicitly resolves the task-owned resubmit discrepancy to SUBMITTED.
Both authorized commands validate the historical bound template; missing required
types, active invalid and not-ready documents return 422 without side effects.
Tombstones do not count; duplicate active pending/invalid documents block submission.

One conditional transaction stores Case/version/attempt/GSI state, audit, pending
fact and durable receipt. Replays survive lost responses and subsequent state
changes; cross-operation reuse conflicts. Authorization precedes receipt access.
Document revision updates share existing audited mutations, fencing insert/delete/
validation races during paginated reads. No key migration or dependency changes.

Tests cover same/different-key competing submit and resubmit interleavings,
owner/version/attempt/revision changes, actual upload/delete races, stable input/
execution name, receipt history, legacy zero counters, immutable template binding,
pagination, roles, body/key validation, conditional rollback and sanitized 503.
Real local S3/processor paths validate all required documents before submission and
deliver both new facts through the publisher to the domain bus only.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | 313 backend tests in 258.84s; Ruff lint/format; mypy 42 source/test files and 4 scripts; frontend Prettier/ESLint/Vitest 1/TypeScript/Vite; Python sdist/wheel |
| Targeted submission/domain/processor pytest | PASS | Initial 90 tests before final resubmit race expansion; final expansion included in full 313 |
| terraform fmt -check -recursive infra | PASS | Final format |
| terraform -chdir=infra/environments/dev validate -no-color | PASS | Dev configuration valid |
| terraform -chdir=infra/environments/dev test -no-color | PASS | 24 provider-mocked plan tests; JWT/CORS/invoke scopes and receipt/revision IAM checked |
| backend/.venv/Scripts/python.exe scripts/package_cases.py | PASS | Two identical builds; compressed 16,365,325 bytes / uncompressed 22,462,954 bytes |
| Isolated Python -I -S ZIP imports | PASS | Case command/submission/revision, document command/processor and outbox publisher import with only ZIP added to sys.path |
| git diff --check | PASS | Final whitespace check |
| AWS deployment/live acceptance/hosted CI | NOT RUN | No cloud deployment authorized; live evidence owned by TASK-021; local checks do not assert hosted CI |

Terraform executable: .tools/terraform-1.14.9/terraform.exe.
No new module/provider/dependency: existing initialized lock retained.
ZIP SHA256: 95a90e77fca11fe16701c8f85f4314b7f9f28b08c3623c379584d2bd8042f54d.

Initial lint line wrapping and one fixture mapping type annotation were corrected.
Initial Terraform run had 21 PASS, 1 FAIL and 2 skipped: a computed API ARN was
unknown during plan. An explicit plan-phase mock value fixed the assertion;
the full final run passed all 24. No failing acceptance checks remain.

## Limits and handoff

202 means submission accepted, not workflow started. Persist PENDING plus exact
deterministic name/input; workflowExecutionId stays null. TASK-014 must implement
actual Standard StartExecution, conditional ARN persistence and pending-start
recovery (including receipt replays). No fake execution or orchestration through
domain events. Do not deploy the intermediate phase before that implementation.

Local deterministic interleavings/Moto do not prove real AWS transaction isolation,
IAM enforcement, JWT/CORS or poller delivery. Live checks remain NOT RUN, TASK-021.
No AWS writes, credentials, customer documents or state are published.
Existing outbox stream-retention/replay limitations remain TASK-020/021.

## Exact changed files

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/case_api/api.py
- backend/src/common/cases/documents.py
- backend/src/common/cases/repository.py
- backend/src/common/cases/submission.py
- backend/src/document_api/command.py
- backend/src/document_api/deletion.py
- backend/src/document_processor/handler.py
- backend/src/outbox_publisher/handler.py
- backend/tests/integration/test_document_processor.py
- backend/tests/integration/test_domain_events.py
- backend/tests/integration/test_submission.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/PRD.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/010-private-document-upload.md
- docs/adr/011-document-soft-delete.md
- docs/adr/013-document-processing.md
- docs/adr/016-case-submission.md
- docs/api/README.md
- docs/api/openapi.yaml
- docs/events/README.md
- docs/events/case-submission.schema.json
- docs/events/domain-event.schema.json
- docs/tasks.md
- docs/verification/TASK-013.md
- infra/README.md
- infra/environments/dev/tests/cases.tftest.hcl
- infra/environments/dev/tests/document_processor.tftest.hcl
- infra/modules/api/cases.tf
- infra/modules/api/main.tf
- infra/modules/lambda/database.tf
- infra/modules/lambda/processor.tf
