# TASK-005 verification

Date: 2026-09-16. Status: DONE (local acceptance under ADR-007).
Cloud deployment and live service acceptance: NOT RUN, owned by TASK-021.

## Scope

Reviewed AGENTS, PROJECT_STATUS, task criteria, latest changelog/decisions/ADRs,
Technical Design Case/audit/outbox/API/index/authorization contracts and existing code.
The working tree was clean. TASK-004 was locally DONE; only TASK-005 was implemented.

Four routes now have Lambda handlers and Terraform integrations. Case creation resolves
and stores the active template version, then conditionally transacts Case, audit and
CaseCreated outbox. Query responses are explicitly projected. No EventBridge publisher,
Case mutation lifecycle or frontend business UI was added.

## Actual checks

| Check | Result | Evidence |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | Backend lint/format/mypy; 59 tests; frontend formatting/lint/1 test/type/build; backend sdist/wheel |
| Backend integration/contract tests | PASS | 25 Case scenarios and 8 template tests in final 59-test run |
| Case creation | PASS | Stable PK/SK/GSI formats, active template binding, preserved historical version, atomic failure rollback, audit and schema-valid CaseCreated detail |
| Queries/security | PASS | Own-case pagination, cross-principal cursor rejection, empty filtered-page continuation, GSI2 admin query, detail/activity ownership, nested secret filtering and activity pagination |
| Boundary errors | PASS | Invalid JSON/case type/owner/status/limit/cursor, forbidden roles, untrusted bearer header, missing active template and separate command/query entry points |
| Contract checks | PASS | JSON Schema validates actual API response bodies and serialized event detail; latest schema check rerun after documentation refinement |
| terraform fmt -check -recursive infra | PASS | Final configuration formatted |
| terraform init -backend=false -input=false -lockfile=readonly | PASS | Existing provider lock reused |
| terraform validate | PASS | No warnings |
| terraform test | PASS | 12 plan-only provider-mocked runs, including all Case routes, transaction-only command IAM and read-only query IAM |
| pip check | PASS | No broken requirements |
| package_cases.py | PASS | Two identical SHA256 results; bundled pinned SDK; isolated -I -S import/invocation of command/query handlers without site-packages |
| Package limits | PASS | ZIP below 50 MiB and uncompressed content below 250 MiB; no .pyd/.so/.dll dependencies |
| package_health.py | PASS | Only standalone health module and package initializer included |
| AWS plan/apply, real JWT/IAM/API/E2E | NOT RUN | No cloud deployment authorized |
| Hosted CI / Linux and deployed arm64 execution | NOT RUN | Local verification on Windows; pure-Python packaging does not constitute cloud execution evidence |

Initial checks exposed type annotations and test-fixture issues (empty key prefix and
missing decode import); these were corrected before the final passing run. IAM transaction
conditions follow AWS documentation using ForAnyValue:StringEquals EnclosingOperation.

## Boundaries

GSI pagination is eventually consistent and not a snapshot. A page can be empty with a
cursor. Cursors are scoped positions, not signed authorization credentials; server-side
partition reconstruction and authorization are the security boundary.
Repeated successful create requests create distinct Cases; HTTP idempotency is not
guaranteed. Do not promise safe deduplication after ambiguous network outcomes.

Pending outbox records have no TTL; TASK-011 owns actual dispatch and retention.
TASK-006 extends authorization tests. Documents/reviews are read with whitelists but
their mutations remain assigned to later tasks. No new AWS resource was deployed.

Known documentation carryover: Technical Design section 25 contains older push-deploy
prose superseded by AGENTS 3.1 / ADR-007. TASK-021 must synchronize it before deployment
automation. Current GitHub workflow performs validation only.

## Exact changed files

- `.github/workflows/pull-request.yml`
- `PROJECT_STATUS.md`
- `README.md`
- `backend/README.md`
- `backend/pyproject.toml`
- `backend/requirements-dev.txt`
- `backend/requirements-runtime.txt`
- `backend/src/case_api/api.py`
- `backend/src/case_api/command.py`
- `backend/src/case_api/query.py`
- `backend/src/common/cases/__init__.py`
- `backend/src/common/cases/repository.py`
- `backend/tests/integration/test_cases.py`
- `docs/CHANGELOG.md`
- `docs/CLOUD_ACCEPTANCE.md`
- `docs/DECISIONS.md`
- `docs/TECHNICAL_DESIGN.md`
- `docs/adr/006-health-authentication.md`
- `docs/adr/009-case-api-foundation.md`
- `docs/api/README.md`
- `docs/api/openapi.yaml`
- `docs/events/README.md`
- `docs/events/case-created.schema.json`
- `docs/tasks.md`
- `docs/verification/TASK-005.md`
- `infra/README.md`
- `infra/environments/dev/cases.tf`
- `infra/environments/dev/health.tf`
- `infra/environments/dev/tests/cases.tftest.hcl`
- `infra/modules/api/cases.tf`
- `infra/modules/api/variables.tf`
- `infra/modules/lambda/database.tf`
- `infra/modules/lambda/main.tf`
- `infra/modules/lambda/variables.tf`
- `scripts/package_cases.py`
- `scripts/package_health.py`
