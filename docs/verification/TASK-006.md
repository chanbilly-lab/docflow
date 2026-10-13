# TASK-006 verification

Date: 2026-09-16. Status: DONE. Local acceptance under ADR-007.
Live AWS acceptance is NOT RUN, owned by TASK-021.

## Scope and sources

Read AGENTS.md, PROJECT_STATUS.md, docs/tasks.md, latest CHANGELOG/DECISIONS,
ADRs 006/007/009, Technical Design section 14, PRD personas, API contracts,
existing handlers/repository and integration tests. TASK-005 was DONE and the
working tree was clean at ddcd66f2c1c9da3a81c62302113f63a04c014ade.

This task adds 49 authorization regression cases to the existing integration
suite. Production behavior, infrastructure, API contracts and dependencies are
unchanged; no new architectural decision is required.

## Acceptance coverage

| Criterion | Local evidence |
| --- | --- |
| Requester A cannot access B | Both detail and activity enforce ownership; inaccessible and missing Cases return the same 404 response; list results remain in the caller partition |
| Reviewer/admin matrix | Both read routes cover owner/non-owner requester, assigned/unassigned reviewer, reviewer who owns but is not assigned, assigned user without reviewer role, admin and combined roles |
| Backend enforcement | Real HTTP boundary and boto3 repository execute against Moto; no frontend authorization assumptions |
| Persisted assignment | Assignment on another Case cannot grant access; adding/removing/reassigning an assignment changes the next request outcome |
| Create permissions | Requester/admin and combined requester/reviewer create as their own sub; reviewer/unknown/no-role requests return 403 without changing any table item |
| List permissions | Requester mine only, reviewer denied, admin mine/all; exact IDs and error codes are asserted |
| Identity spoofing | Headers cannot change caller/role; requesterId/role query injection is rejected; audit/outbox actor and owner derive from trusted claims |
| Claim boundary | Missing/ID-token/invalid-sub and insufficient/malformed roles reject before SDK client creation; supported group string formats do not grant admin |
| Cursor forgery | Recomputed public fingerprint with another user's Case position cannot select their partition; returned IDs and actual query partition are checked |
| Response protection | Private comments and workflow placeholders never appear for any successful role; rejected reads do not invoke detail/activity loaders |

The matrix covers the four implemented Case routes. Upload, submit, review queue,
claim/start/checklist/decision and template administration APIs remain in their
planned tasks. This task does not add those endpoints or claim they were tested.
Assignment removal is exercised by direct test fixtures, not a new reassignment API.

## Verification results

| Check | Result | Evidence / reason |
| --- | --- | --- |
| backend/.venv/Scripts/python.exe -m pytest backend/tests/integration/test_cases.py -q | PASS | 74 passed, including 49 new cases |
| py -3.13 scripts/dev.py check | PASS | 108 backend tests; Ruff lint/format; mypy 26 backend/test files and 4 scripts; frontend format/lint/1 test/TypeScript/Vite build; backend sdist/wheel |
| git diff --check | PASS | No whitespace errors |
| Terraform fmt/validate/test and Lambda ZIP checks | NOT RUN | No infrastructure, production code, dependency or packaging changes; TASK-005 evidence remains separate |
| Real AWS JWT/IAM/HTTP and hosted CI | NOT RUN | No deployment authorized; local checks do not establish hosted CI outcome |

All executed checks passed; no failing regression required a production fix.

## Limits and handoff

Moto does not establish real IAM enforcement, JWT signatures/expiry/issuer/client
validation, or AWS consistency/concurrency. Tests use fabricated claims at the trusted
Gateway boundary; they do not bypass production Gateway signature checks. Cloud
coverage remains in docs/CLOUD_ACCEPTANCE.md for TASK-021. No deployment occurred.

Read permissions follow ADR-009's persisted assignment rule. Active-task lifecycle
and decision ownership tests remain in TASK-016/017. Cursor fingerprints are public,
not an integrity or authorization guarantee. No production change was needed.

Carryover: Technical Design section 25 push-deploy prose remains superseded by
AGENTS 3.1 / ADR-007, with synchronization assigned to TASK-021.

## Exact changed files

- PROJECT_STATUS.md
- backend/tests/integration/test_cases.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/api/README.md
- docs/tasks.md
- docs/verification/TASK-006.md
