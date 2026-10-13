# TASK-008 verification

Date: 2026-09-16. Status: DONE. Local acceptance under ADR-007.
Cloud acceptance: NOT RUN, owned by TASK-021.

## Scope

Read AGENTS, PROJECT_STATUS, tasks, latest CHANGELOG and DECISIONS, ADR-007/010,
Technical Design 8.3/13.6, PRD document lifecycle, existing upload/query contracts,
handlers, integration tests and Terraform route/IAM. TASK-007 was locally DONE.
Working tree was clean at ba677121b9073d7ef6819d2fe9b467b04337d388.

Implemented soft deletion and retained the existing bound-template metadata/upload
path. No processing pipeline, physical object deletion, frontend UI or cloud
deployment was added. ADR-011 records the lifecycle and retry contract.

## Acceptance evidence

- Persisted metadata: initial upload, terminal tombstone, one audit, unchanged
  historical metadata/S3 bytes, retry no-op and new-ID replacement.
- Template/filename: existing historical-template tests and filename-independent
  key assertions remain in the document suite and are rerun.
- Immutable states: all seven nonmutable implemented Case states reject both owner
  and admin deletion; current state is checked on retries too.
- Authorization: requester owner/admin permitted; other requester and reviewer/no
  role denied; document IDs cannot select another Case partition.
- Concurrency: Case status/owner/version and document status/version/updatedAt races
  roll back the entire delete/audit; racing duplicate deletes yield one audit.
- Queries: tombstones are omitted, replacement is visible, raw history stays intact.
- Isolation: delete entry point constructs only the DynamoDB client; no bucket
  variable or S3 capability is needed.

## Checks

| Check | Result | Evidence / reason |
| --- | --- | --- |
| backend/.venv/Scripts/python.exe -m pytest backend/tests/integration/test_documents.py -q | PASS | 67 document tests, 28 added in TASK-008 |
| py -3.13 scripts/dev.py check | PASS | 175 backend tests; Ruff lint/format; mypy 31 source/test files and 4 scripts; frontend format/lint/1 test/type/build; backend sdist/wheel |
| terraform fmt -check -recursive infra | PASS | Final configuration formatted |
| terraform validate | PASS | Existing initialized local modules/provider reused |
| terraform test | PASS | 16 mocked plan runs, extended DELETE/JWT/CORS/IAM assertions |
| scripts/package_cases.py | PASS | Two identical SHA256 digests; deletion.py included |
| Isolated py -3.13 -I -S ZIP invocation | PASS | Delete entry point imports and rejects missing auth without site-packages |
| Package size limits | PASS | Compressed <50 MiB; uncompressed <250 MiB |
| git diff --check | PASS | No whitespace errors |
| Live AWS/hosted CI/arm64 execution | NOT RUN | No cloud deployment authorized; local checks are not hosted/live evidence |

Initial lint checks flagged long expressions; formatting was corrected before the
complete passing check. No tests failed. Terraform init was not rerun because module
sources and provider requirements are unchanged.

## Limits

Moto and mocked plans are local evidence only. Real IAM, browser CORS, JWT,
transaction contention and event processing remain TASK-021.
The late-upload test uses a separate mocked S3 PUT, not live presigned HTTP.
TASK-010 must ensure delayed/duplicate processing cannot resurrect DELETED metadata.
No physical cleanup, retention TTL or upload URL revocation is implemented.

Unrelated carryovers: PRD resubmit state discrepancy is assigned to TASK-013;
Technical Design section 25 push-deploy prose is superseded by ADR-007 and scheduled
for TASK-021 synchronization.

## Exact changed files

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/common/cases/repository.py
- backend/src/document_api/command.py
- backend/src/document_api/deletion.py
- backend/tests/integration/test_documents.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/PRD.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/010-private-document-upload.md
- docs/adr/011-document-soft-delete.md
- docs/api/README.md
- docs/api/openapi.yaml
- docs/tasks.md
- docs/verification/TASK-008.md
- infra/README.md
- infra/environments/dev/tests/documents.tftest.hcl
- infra/modules/api/documents.tf
- infra/modules/api/main.tf
- infra/modules/lambda/database.tf
