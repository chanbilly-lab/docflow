# TASK-010 verification

Date: 2026-09-16. Status: DONE. Local acceptance under ADR-007.
Real AWS retry/DLQ evidence: NOT RUN, owner TASK-021; no deployment authorized.

## Scope and acceptance

Started from clean fb23b1a566e7af2635cfca66b5aa086738b2fe46, TASK-009 locally DONE.
Read governance, status/tasks/changelog/decisions, ADR-004/007/010/011/012,
Technical Design 6.9/8.4/9 and PRD document flow plus existing code/infra.

- Deterministic claims, leased ownership and completion guard duplicate effects.
- Persisted UPLOADED/VALIDATING/VALID/INVALID transitions each have an audit.
- Final result/audit/outbox/COMPLETED claim are atomic; deletion and stolen-owner
  races reject completion without partial business effects.
- Size/MIME/extension/required metadata/signature validation and streaming SHA-256.
- Batch partial response keeps failed IDs only; queue mapping enables that response.
- Actual local SQS SDK forced-failure test receives a poison message five times,
  calls the processor batch handler each time, leaves failures unacknowledged and
  verifies Moto moves it to DLQ on the next poll. No production failure switch.
- Crash after VALIDATING resumes after lease expiry; terminal tombstones stay deleted;
  completed-claim TTL removal still cannot create another validation event.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | 211 backend tests; Ruff lint/format, mypy 35 source/test files and 4 scripts; frontend lint/format/1 test/type/build; Python sdist/wheel |
| pytest backend/tests/integration/test_document_processor.py -q | PASS | Final 29 processor tests; adds JPEG/PNG/version-pinned cases after full run (214 total cases) |
| Final targeted Ruff lint/format and mypy | PASS | All 3 processor source/test files pass after extra cases |
| Terraform init -backend=false -input=false -lockfile=readonly | PASS | Local module/test initialization; provider lock unchanged |
| Terraform fmt -check -recursive infra; validate | PASS | Final configuration valid |
| Terraform test | PASS | 20 mocked plan runs |
| scripts/package_cases.py twice | PASS | Matching SHA-256; processor included; compressed <50 MiB, uncompressed <250 MiB |
| py -3.13 -I -S isolated ZIP import and empty batch | PASS | No site-packages; imported worker and executed batch response |
| git diff --check | PASS | Final whitespace check |
| Real AWS/hosted CI | NOT RUN | No cloud deployment authorized; TASK-021 owns live evidence |

Terraform executable is .tools/terraform-1.14.9/terraform.exe; init/validate/test use
-chdir=infra/environments/dev. Python targeted checks use backend/.venv/Scripts/python.exe.
The full check preceded three additional tests; all final processor tests and their
lint/types were rerun. No production code changed after the full passing check.

## Limits and failure corrections

Initial tests found unquoted If-Match values; corrected conditional S3 reads.
JSON schema tests now serialize DynamoDB Decimal values into JSON numbers before
validation, as the outbox publisher must do. Terraform collection equality was
corrected to length/contains; a new test module required readonly init.
Formatting/type issues were corrected before final checks.

The test suite does not prove real service retry timing or Lambda polling.
Signature validation is not complete file parsing or malware scanning.
Malformed/missing/conflicting sources retry and can reach DLQ for diagnosis.
A crash can leave an expired IN_PROGRESS claim; redelivery safely takes it over.
No automated DLQ replay, object deletion or business rejection is introduced.
Existing unrelated TASK-013 resubmit discrepancy and TASK-021 push-deploy prose
carryovers remain unchanged.

## Exact changed files

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/document_processor/__init__.py
- backend/src/document_processor/handler.py
- backend/tests/integration/test_document_processor.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/PRD.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/013-document-processing.md
- docs/events/README.md
- docs/events/document-validation.schema.json
- docs/tasks.md
- docs/verification/TASK-010.md
- infra/README.md
- infra/environments/dev/document_processor.tf
- infra/environments/dev/tests/document_processor.tftest.hcl
- infra/modules/lambda/database.tf
- infra/modules/lambda/main.tf
- infra/modules/lambda/processor.tf
- infra/modules/lambda/variables.tf
- scripts/package_cases.py
