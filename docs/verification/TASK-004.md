# TASK-004 verification

Date: 2026-09-16. Status: DONE (local acceptance under ADR-007).
AWS deployment and live service acceptance: NOT RUN, owned by TASK-021.

## Scope and source review

Read AGENTS, PROJECT_STATUS, tasks, current changelog/decisions, ADR-003/007 and the
template/audit/Case binding requirements in Technical Design and PRD. TASK-003 was
locally DONE; working tree was clean at task start. No other implementation task ran.

Implemented immutable Template/Check models, supplier-onboarding v1, boto3 DynamoDB
repository and preview-first loopback-only seed CLI. Preserve template/check keys;
new template audit items are explicitly documented in ADR-008. No public API,
Terraform resource or frontend behavior changed.

## Actual verification

| Command/check | Result | Evidence |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | Backend lint/format/mypy, 30 tests at this run; frontend lint/format/1 test/type/build; backend sdist/wheel build |
| Final backend python -m pytest | PASS | 34 tests: 26 unit/contract/CLI tests and 8 in-process DynamoDB integration tests |
| Final backend ruff check / ruff format --check | PASS | 24 files formatted; no lint errors |
| Final backend mypy | PASS | 20 source/test files |
| mypy --strict ../scripts | PASS | 3 scripts |
| pip check | PASS | No broken requirements |
| Seed CLI preview and external endpoint rejection | PASS | Preview JSON parsed; three nonlocal/deceptive endpoints rejected before client creation |
| Repository tests through boto3/Moto | PASS | Exact replay/no duplicate audit, numeric versions 1/2/10 and pagination, old-version reads, conflict preservation, atomic rollback, damaged data, racing identical publication, error propagation |
| Model tests | PASS | Invalid versions/IDs/documents/checks/transaction size rejected; frozen models; required/optional seed checks |
| Terraform checks | NOT RUN | No Terraform configuration changes; prior TASK-003 nine mock tests remain historical evidence |
| AWS seed/deployment/live integration | NOT RUN | User's local-first plan; no AWS calls or cloud writes during this task |
| Hosted CI / Linux runtime | NOT RUN | Local verification on Windows only |

Initial lint/type checks found line lengths, pagination TypedDict typing and missing
package type marker. These were fixed; final checks above passed. Runtime dependency
boto3 is pinned; DynamoDB stubs and Moto are development-only. Lockfile retains
resolved dependencies, with a Windows-only marker for pywin32.

## Limits and handoff

Moto exercises the actual SDK repository but cannot establish real AWS IAM, service
transaction isolation, eventual delivery or production concurrency behavior. The
simulated race covers repository recovery logic, not simultaneous cloud writers.
Those checks remain in docs/CLOUD_ACCEPTANCE.md.

Only SUPPLIER_ONBOARDING is currently mapped. Highest published numeric version is
active for new Cases; historical definitions never mutate. Template-management APIs,
draft/retire/rollback lifecycle and Case binding are not part of this task.
TASK-005 must persist the selected template ID/version in each Case.

The seed CLI can write only to an existing loopback DynamoDB table. Tests use an
in-process emulator; no persistent local database service was started. A future
authorized TASK-021 cloud harness can inject an AWS client into the same repository.

Known documentation carryover: Technical Design section 25 still contains older
push-triggered dev deployment prose, superseded by AGENTS 3.1 and ADR-007. Do not
implement automatic deployment from that historical prose; synchronize it in TASK-021.

## Final repository checks

PASS: diff formatting, task-status consistency, package contents/runtime dependency,
common credential-pattern scan and changed-file inventory. No unrelated files staged.

## Files changed

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/pyproject.toml
- backend/requirements-dev.txt
- backend/src/common/py.typed
- backend/src/common/templates/__init__.py
- backend/src/common/templates/models.py
- backend/src/common/templates/repository.py
- backend/src/common/templates/seed.py
- backend/tests/integration/test_templates.py
- backend/tests/unit/test_seed_cli.py
- backend/tests/unit/test_template_models.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/008-checklist-template-persistence.md
- docs/tasks.md
- docs/verification/TASK-004.md
- scripts/seed_templates.py
