# TASK-007 verification

Date: 2026-09-16. Status: DONE. Local acceptance under ADR-007.
Cloud deployment and live acceptance: NOT RUN, owned by TASK-021.

## Scope

Read AGENTS, PROJECT_STATUS, tasks, changelog/decisions, ADRs 007/008/009,
PRD upload flow and Technical Design document/S3/API/IAM sections.
TASK-006 was locally DONE. Working tree was clean at 826516ffafb1869bd16e926a223689d65170b156.

Implements metadata-only upload API, required initial Document/audit transaction,
private storage, signing IAM/CORS, route, packaging and OpenAPI. ADR-010 records
the implementation details. Deletion, processing, notifications and frontend UI
remain assigned to later tasks.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| backend/.venv/Scripts/python.exe -m pytest backend/tests/integration/test_documents.py -q | PASS | 39 tests |
| py -3.13 scripts/dev.py check | PASS | 147 backend tests; Ruff format/lint, mypy 30 backend/test files and 4 scripts; frontend 1 test/format/lint/TypeScript/Vite; backend sdist/wheel |
| Final test_upload_state_gate rerun | PASS | 9 tests after refining real signer-call assertions; backend-lint/backend-typecheck also PASS |
| terraform init -backend=false -input=false -lockfile=readonly | PASS | Existing provider lock reused; new local modules initialized |
| terraform fmt -check -recursive infra; terraform validate | PASS | Final configuration valid |
| terraform test | PASS | 16 provider-mocked plan runs, including privacy/encryption/CORS/policies, IAM and upload route |
| scripts/package_cases.py | PASS | Two identical SHA256 results; document_api included |
| Isolated py -3.13 -I -S packaged invocation | PASS | Document handler imports without workstation site-packages and returns 401 for missing auth |
| ZIP limits | PASS | Compressed <50 MiB, expanded <250 MiB; no .pyd/.so/.dll |
| AWS deployment, real expiry/signatures/IAM/browser HTTP, hosted CI/arm64 | NOT RUN | Deferred to TASK-021; no deployment authorized |

Initial checks found a long line and transaction-list typing issue; both corrected.
The first Terraform mock run lacked plan-time bucket ARN overrides; adding
override_during=plan fixed the fixture, and all 16 runs passed. A root-directory
Ruff invocation used different import classification; the canonical backend-root
commands and full check passed without unrelated script changes.

39 document tests cover:
- metadata/audit persist before signing; backend-generated key ignores filename;
- true boto3 SigV4 signature query has 600-second expiry and exact signed headers;
- a separate mocked S3 PUT transfers bytes; conditional replay fails;
- requester/admin/reviewer ownership and mutable-state matrix;
- file-size/MIME/filename/type/unknown-field rejection with no writes;
- historical template binding;
- status/owner/version race transaction rollback;
- sanitized signing failure, no URL persistence, and real Lambda entry point.

Expiry testing inspects actual SDK output, not wall-clock denial by AWS.
The separate S3 PUT uses the SDK against Moto, not the issued URL over HTTP.
No live expiry, HTTP/browser CORS, IAM, TLS or S3 signature-enforcement claim is made.

## Known limits

See ADR-010: URLs are bearer capabilities, temporary credentials may shorten
expiry, issuance does not imply upload/validation, late first uploads remain
possible, and failed signing leaves auditable metadata. No HTTP deduplication.
TASK-008 extends lifecycle/deletion; TASK-009/010 implement the upload pipeline.
Real cloud acceptance remains in docs/CLOUD_ACCEPTANCE.md.

Carryover: Technical Design section 25 push-deploy wording is superseded by
AGENTS 3.1/ADR-007; synchronize in TASK-021 before deployment automation.

## Exact changed files

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/document_api/__init__.py
- backend/src/document_api/command.py
- backend/tests/integration/conftest.py
- backend/tests/integration/test_cases.py
- backend/tests/integration/test_documents.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/010-private-document-upload.md
- docs/api/README.md
- docs/api/openapi.yaml
- docs/tasks.md
- docs/verification/TASK-007.md
- infra/README.md
- infra/environments/dev/documents.tf
- infra/environments/dev/health.tf
- infra/environments/dev/tests/documents.tftest.hcl
- infra/modules/api/documents.tf
- infra/modules/api/main.tf
- infra/modules/api/variables.tf
- infra/modules/lambda/database.tf
- infra/modules/lambda/main.tf
- infra/modules/lambda/storage.tf
- infra/modules/lambda/variables.tf
- infra/modules/storage/main.tf
- infra/modules/storage/outputs.tf
- infra/modules/storage/variables.tf
- infra/modules/storage/versions.tf
- scripts/package_cases.py
