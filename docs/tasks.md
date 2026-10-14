# docs/tasks.md — DocFlow Implementation Tasks

> Privacy note (2026-10-14): account-specific billing/credit details and private support identifiers are withheld for public release. Historical technical outcomes are unchanged; redacted details are not live targets.

## PRIVACY-PUBLISH-01 — Privacy review and public source

Status: DONE (2026-10-14). Owner approved retaining private history and publishing
the clean same-name source. New public repository ID 1418914087; old ID 1366248864
is PRIVATE/read-only as docflow-private-archive. Original checkout/mirror origins
point to the archive; D:/Projects/docflow-public is the clean public checkout.
Anonymous public page/metadata returned 200; archive and old Git object returned
404. Only the clean codex/privacy-release branch was uploaded; application CI=0.

Acceptance: reviewed private contacts/cloud identifiers/home paths and private
legacy metadata are excluded from public source; original work/history preserved;
remote visibility and source SHA actually checked. API, code, runtime and cloud
acceptance remain unchanged. See PRIVACY_REVIEW.md for scope/results and skipped
application checks.

## Owner exception - 2026-09-29 (ADR-029)

User elected to skip remaining TASK-021 acceptance and proceed to TASK-022 after
requesting AWS retirement. TASK-021 stays BLOCKED (skipped by owner, not passed).
Only the TASK-022 dependency gate is waived. No new deployment or test-email work.
Portfolio claims must preserve actual partial evidence and NOT RUN limitations.

## TASK-021 frontend publication amendment - 2026-09-29

TASK-021 remains BLOCKED; TASK-022 remains TODO. The user-requested frontend
design, GitHub publication and owner-private static preview are independently
delivered. This does not waive or complete cloud acceptance criteria. Frontend
format/lint/tests/type/build and browser verification PASS; details and preview
are in frontend/PUBLISHING.md and docs/verification/TASK-021-FRONTEND.md.

**Status vocabulary:** `TODO | READY | IN_PROGRESS | BLOCKED | DONE`

Normal execution prompt:

```text
执行 TASK-XXX。
```

`AGENTS.md` defines the rest.

---

## Execution plan - local development first (ADR-007)

TASK-003 through TASK-020 are completed against local implementation acceptance.
Their dependency chain refers to local DONE. Resource-existence criteria mean
Terraform representation locally; cloud behavior and actual service guarantees are
preserved in TASK-021, not treated as proven by mocks. Each task must implement its
full assigned behavior and pass meaningful local unit/contract/integration tests and
relevant infrastructure checks. No placeholder implementation qualifies as DONE.

For all acceptance criteria below, verify locally where possible and record real AWS
checks NOT RUN with explicit ownership in docs/CLOUD_ACCEPTANCE.md. This includes
TASK-010's real retry/DLQ requirement and TASK-018's live E2E lifecycle. Local evidence
and live evidence must remain separate in each verification record.
TASK-021 owns consolidated cloud acceptance; TASK-022 remains gated on that completion.

Default sequence: TASK-004 -> ... -> TASK-020 locally -> TASK-021 preparation ->
explicitly authorized short cloud session and cleanup -> TASK-022.
GitHub publication continues for locally DONE tasks; no push-triggered AWS deployment.

## Task overview

| Task | Title | Phase | Status | Depends On |
|---|---|---:|---|---|
| TASK-000 | Project governance + AI workflow | 0 | DONE | — |
| TASK-001 | Repository skeleton + baseline tooling | 1 | DONE | TASK-000 |
| TASK-002 | Terraform dev foundation | 1 | DONE | TASK-001 |
| TASK-003 | Cognito + API Gateway health path | 1 | DONE | TASK-002 |
| TASK-004 | Checklist Template persistence + seed | 2 | DONE | TASK-003 |
| TASK-005 | Case create/query APIs | 2 | DONE | TASK-004 |
| TASK-006 | Authorization + ownership tests | 2 | DONE | TASK-005 |
| TASK-007 | S3 document storage + presigned upload | 3 | DONE | TASK-006 |
| TASK-008 | Document metadata + delete rules | 3 | DONE | TASK-007 |
| TASK-009 | S3 → EventBridge → SQS pipeline | 4 | DONE | TASK-008 |
| TASK-010 | Document processor + idempotency + DLQ | 4 | DONE | TASK-009 |
| TASK-011 | Transactional Outbox + DynamoDB Streams | 5 | DONE | TASK-010 |
| TASK-012 | Custom domain event bus | 5 | DONE | TASK-011 |
| TASK-013 | Submit/Resubmit validation | 6 | DONE | TASK-012 |
| TASK-014 | Step Functions workflow foundation | 7 | DONE | TASK-013 |
| TASK-015 | Review task creation + queue queries | 7 | DONE | TASK-014 |
| TASK-016 | Claim/start/checklist APIs | 7 | DONE | TASK-015 |
| TASK-017 | Decision callback + finalization | 7 | DONE | TASK-016 |
| TASK-018 | Request-information + resubmission E2E | 7 | DONE | TASK-017 |
| TASK-019 | Domain notifications | 8 | DONE | TASK-018 |
| TASK-020 | Observability + alarms + runbook | 9 | DONE | TASK-019 |
| TASK-021 | CI/CD hardening + full E2E | 10 | BLOCKED | TASK-020 |
| TASK-022 | Portfolio documentation hardening | 10 | DONE | TASK-021 gate waived by ADR-029 |

---

# TASK-000 — Project governance + AI workflow

**Status:** DONE  
**Phase:** 0

## Goal
Establish persistent project state and a fixed Codex workflow.

## Deliverables
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `docs/tasks.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`
- architecture ADR baseline
- Technical Design synchronization

## Acceptance criteria
- A new session can recover phase/task/next step/blockers without chat history.
- Normal task prompt is only `执行 TASK-XXX。`.
- Every future task has mandatory verification and documentation synchronization.

---

# TASK-001 — Repository skeleton + baseline tooling

**Status:** DONE
**Phase:** 1  
**Depends on:** TASK-000

## Completion note - 2026-09-11

Repository skeleton and baseline tooling are implemented. Python 3.13.15 and project-local
Node 22.23.2 were verified. Root bootstrap/check commands pass: backend Ruff/mypy/pytest
(7 tests), frontend Prettier/ESLint/Vitest (1 test)/TypeScript/Vite build, and backend package build.
Directory inventory, ignore rules, common secret-pattern review and local production HTTP
smoke checks pass. README contains Windows and POSIX bootstrap commands.

The user explicitly authorized deferring the resubmission-state discrepancy to TASK-013;
no business-state interpretation was selected. Full verification and exact changed-file
inventory: `docs/verification/TASK-001.md`. GitHub-hosted CI and cloud checks have not run.

## Goal
Create application repository structure and local tooling without business features.

## Scope

Create:

```text
frontend/
backend/
infra/
scripts/
.github/workflows/
docs/adr/
docs/api/
docs/events/
```

Backend shared structure:

```text
backend/src/common/
  auth/
  logging/
  errors/
  ids/
  dynamodb/
  events/
  idempotency/
```

Add:

- Python project configuration
- backend formatter/linter/type-check/test config
- React/TypeScript frontend scaffold
- frontend lint/test/build scripts
- `.gitignore`
- `.editorconfig`
- example environment file without secrets
- root developer commands (`Makefile` or equivalent)
- local bootstrap instructions

## Out of scope
- Case APIs
- Cognito deployment
- DynamoDB business implementation
- AWS business resources
- frontend business pages

## Acceptance criteria
- Backend baseline test command runs.
- Backend lint and type check run.
- Frontend build/lint baseline runs.
- Directory structure matches Technical Design.
- No secrets are committed.
- README contains local bootstrap commands.

---

# TASK-002 — Terraform dev foundation

**Status:** DONE
**Phase:** 1  
**Depends on:** TASK-001

## Completion note - 2026-09-12

Dev composition, Terraform/provider constraints and lockfile, DynamoDB base table with
GSI1/GSI2, TTL/Stream/PITR and 14 baseline log groups are implemented in the existing
module boundaries. Terraform 1.14.9/AWS 6.64.0 fmt, readonly initialization, validate
(without warnings), and six provider-mocked plan tests pass. PR CI includes these checks.
ADR-005 records the initial local state boundary and mandatory migration before shared
or automated deployment. No AWS resources were deployed.

Exact commands, limitations and file inventory: `docs/verification/TASK-002.md`.

## Goal
Create Terraform structure and shared dev foundation.

## Acceptance criteria
- provider/version constraints exist
- dev composition exists
- DynamoDB base table/GSIs are represented
- baseline log groups exist
- `terraform fmt -check` passes
- `terraform validate` passes

---

# TASK-003 - Cognito + API Gateway health path

**Status:** DONE
**Phase:** 1
**Depends on:** TASK-002

## Local completion - 2026-09-15

Under the user-approved ADR-007 plan, local implementation acceptance is complete:
Cognito/auth/api/lambda modules, health handler, OpenAPI, packaging and CI integration.
Application checks, 14 backend tests and 9 mocked Terraform plans PASS.
AWS identity was verified with docflow-dev/us-east-1; account-specific billing/credit details withheld for privacy. No deployment took place. Evidence: docs/verification/TASK-003.md.

## Local acceptance criteria

- Cognito User Pool/App Client/groups and HTTP API/JWT route are represented in Terraform.
- Provider validation and mock tests cover issuer/audience/scope and least-privilege IAM.
- Handler tests cover authenticated context, missing/wrong claims and secret-safe responses.
- OpenAPI success-response contract, deterministic ZIP and application checks pass.

## Cloud acceptance transferred to TASK-021

- Cognito User Pool/App Client/groups and HTTP API/JWT authorizer exist in AWS.
- A real access token can be obtained and authenticated /api/v1/health returns 200.
- Invalid/missing tokens are rejected by the deployed endpoint.
- Additional negative cases and evidence are tracked in docs/CLOUD_ACCEPTANCE.md.
All cloud checks remain NOT RUN; local DONE is not a live verification claim.

---

# TASK-004 — Checklist Template persistence + seed

**Status:** DONE
**Phase:** 2  
**Depends on:** TASK-003

## Local completion - 2026-09-16

Immutable template persistence, numeric active-version resolution, exact historical
reads and repeatable supplier seed are implemented. Metadata/checks/audit use one
conditional transaction. Final backend tests: 34 PASS including 8 local DynamoDB
integration tests; application checks/builds PASS. No AWS deployment.
See ADR-008 and docs/verification/TASK-004.md. Real AWS acceptance stays in TASK-021.

## Goal
Implement immutable versioned checklist templates and first supplier-onboarding seed.

## Acceptance criteria
- active template resolves by case type
- historical version loads directly
- seed is repeatable/idempotent
- keys match Technical Design

---

# TASK-005 — Case create/query APIs

**Status:** DONE
**Phase:** 2  
**Depends on:** TASK-004

## Local completion - 2026-09-16

Four Case routes, immutable template binding, atomic Case/audit/outbox creation,
scoped pagination and explicit public projections are implemented and wired locally.
Application checks/builds and 59 backend tests PASS; 12 Terraform mock tests PASS.
See ADR-009 and docs/verification/TASK-005.md. No cloud deployment; live acceptance
remains in TASK-021. TASK-006 extends the authorization verification.

## Routes
- `POST /api/v1/cases`
- `GET /api/v1/cases`
- `GET /api/v1/cases/{caseId}`
- `GET /api/v1/cases/{caseId}/activity`

## Acceptance criteria
- active checklist version binds at creation
- PK/SK/GSI match design
- requester list paginates
- internal fields are not returned

---

# TASK-006 — Authorization + ownership tests

**Status:** DONE
**Phase:** 2  
**Depends on:** TASK-005

## Local completion - 2026-09-16

Added 49 backend authorization regression scenarios covering requester isolation,
reviewer/admin roles, assignment changes, spoofed identity/query/cursor inputs and
denied-write side effects. Existing production behavior passed without modification.
All 108 backend tests and full application checks/builds PASS. See
docs/verification/TASK-006.md. Real JWT/IAM/HTTP checks remain NOT RUN in TASK-021.

## Acceptance criteria
- Requester A cannot access Requester B Case
- reviewer/admin behavior follows matrix
- server-side enforcement is tested

---

# TASK-007 — S3 document storage + presigned upload

**Status:** DONE
**Phase:** 3  
**Depends on:** TASK-006

## Local completion - 2026-09-16

Private S3 configuration and metadata-only upload API are implemented. Initial
Document/audit creation, bound-template type validation and conditional Case gate
are prerequisites implemented here; TASK-008 extends their lifecycle/delete rules.
600-second SigV4 PUT binds exact MIME/length and create-only writes. Application
checks/builds and 147 backend tests PASS; 16 Terraform mock tests PASS; deterministic
isolated Lambda packaging PASS. See ADR-010 and docs/verification/TASK-007.md.
Live S3 expiry, browser CORS, IAM and upload behavior remain NOT RUN in TASK-021.

## Acceptance criteria
- bytes do not pass through API Gateway/Lambda
- presigned URL expires
- Block Public Access is enabled
- S3 key is backend-generated

---

# TASK-008 — Document metadata + delete rules

**Status:** DONE
**Phase:** 3  
**Depends on:** TASK-007

## Local completion - 2026-09-16

Implemented atomic, audited soft deletion with mutable Case/ownership gates,
document conflict detection, no-op retries, retained historical metadata and
tombstone filtering. Existing historical-template validation and filename-only
metadata tests pass. Replacement uses new IDs. 175 backend tests and full application
checks/builds PASS; 16 Terraform tests and isolated packaging PASS. See ADR-011 and
docs/verification/TASK-008.md. No S3 deletion or AWS deployment; live checks stay TASK-021.

## Acceptance criteria
- document metadata lifecycle is persisted
- documentType is checked against template
- delete is rejected in immutable states
- user filename remains metadata only

---

# TASK-009 — S3 → EventBridge → SQS pipeline

**Status:** DONE
**Phase:** 4  
**Depends on:** TASK-008

Local acceptance DONE: exact-bucket/prefix default-bus routing, standard queue/DLQ,
scoped publishing and redrive policy implemented. Full application checks with
185 backend tests and 18 Terraform mock runs PASS. See ADR-012 and
docs/verification/TASK-009.md. Real S3 delivery/IAM/retry checks NOT RUN, TASK-021.

## Acceptance criteria
- S3 uses EventBridge default bus
- intended event pattern only
- document queue and DLQ exist
- redrive policy is configured

---

# TASK-010 — Document processor + idempotency + DLQ

**Status:** DONE
**Phase:** 4  
**Depends on:** TASK-009

Local acceptance DONE: leased idempotency, audited validation, atomic result/outbox/
completion, partial batch handling and local forced-failure DLQ test implemented.
Full application check (211 tests) plus final 29 processor tests PASS; 20 Terraform
plans and isolated deterministic ZIP PASS. See ADR-013 and verification/TASK-010.md.
Real AWS retry/DLQ NOT RUN, retained under TASK-021. No deployment.

## Acceptance criteria
- duplicate delivery does not duplicate business effects
- VALID/INVALID persisted
- partial batch response enabled
- repeated forced failure reaches DLQ
- real retry/DLQ result documented

---

# TASK-011 — Transactional Outbox + DynamoDB Streams

**Status:** DONE
**Phase:** 5  
**Depends on:** TASK-010

Local acceptance DONE: existing atomic producers retained, filtered stream publisher,
per-entry success/conditional DISPATCHED and stable-ID retry behavior implemented.
250 backend tests (36 publisher), full application checks, 22 Terraform plans and
deterministic isolated ZIP PASS. See ADR-014 and verification/TASK-011.md.
Dev mapping stays disabled until TASK-012 creates/connects the custom bus.
Real delivery/checkpoint/IAM evidence NOT RUN, TASK-021; no deployment.

## Acceptance criteria
- business state + audit + outbox use one transaction where required
- stream filter targets PENDING outbox records
- publisher is duplicate-safe
- successful publish marks DISPATCHED

---

# TASK-012 — Custom domain event bus

**Status:** DONE
**Phase:** 5  
**Depends on:** TASK-011

Local acceptance DONE: custom bus module, actual-ARN publisher wiring and enabled
stream configuration, routed envelope schema and producer-to-bus isolation tests.
260 backend tests including 10 new domain tests, full application checks and
24 Terraform plans PASS. See ADR-015 and verification/TASK-012.md. Real AWS delivery
and IAM NOT RUN, TASK-021. No deployment; command Lambdas retain no publish grants.

## Acceptance criteria
- domain bus separated from default bus
- envelope matches design
- schemas exist for implemented events
- command Lambdas do not directly publish domain events

---

# TASK-013 — Submit/Resubmit validation

**Status:** DONE
**Phase:** 6  
**Depends on:** TASK-012

## Required design resolution

Resolved explicitly by ADR-016 / DEC-020: both operations persist SUBMITTED;
the workflow subsequently enters PROCESSING. PRD section 7, Technical Design
8.1/13.7/13.8 and API contracts are synchronized. This is the explicit resolution
of the discrepancy deferred from TASK-001 on 2026-09-11.

## Completion note - 2026-09-16
Local acceptance PASS under ADR-007: both routes, 422 gates, durable scoped
idempotency, atomic state/audit/outbox/receipt, revision fencing and concurrent
attempt guards implemented. 313 backend tests, full application checks, 24 mocked
Terraform plans and deterministic isolated Lambda packaging PASS.
Cloud checks NOT RUN, TASK-021. Actual workflow start/recovery belongs to TASK-014.
Exact evidence/files: docs/verification/TASK-013.md.

## Acceptance criteria
- missing doc -> 422
- processing doc -> 422
- invalid doc -> 422
- duplicate submit is idempotent
- attempt increment is concurrency-safe

---

# TASK-014 — Step Functions workflow foundation

**Status:** DONE
**Phase:** 7  
**Depends on:** TASK-013

## Required handoff from TASK-013
Implement actual Standard StartExecution using the persisted deterministic name
and immutable workflowInput. Persist the actual execution ARN conditionally and
recover committed PENDING starts after crashes, including HTTP receipt replays.
Do not use domain facts to orchestrate the workflow. See ADR-016.

## Completion note - 2026-09-17
Local acceptance PASS: Standard start/conditional ARN, closed-execution reconciliation,
HTTP/Stream/operator recovery, defensive validation and atomic technical failure
handling implemented. ADR-017 records the foundation-only terminal and TASK-015 handoff.
346 backend tests, full app checks, 28 mocked Terraform plans and reproducible
isolated Lambda packaging PASS. Real AWS NOT RUN, TASK-021. Exact evidence and
files: docs/verification/TASK-014.md.

## Acceptance criteria
- Standard workflow starts for valid submitted Case
- defensive validation exists
- technical failure does not produce business rejection

---

# TASK-015 — Review task creation + queue queries

**Status:** DONE

Local acceptance under ADR-007. ADR-018 implements callback creation, prepared
checklists, atomic public Task/Case/audit/outbox, token refresh and authorized GSI1
available/mine/detail queries. All local checks PASS; live callback/IAM/GSI checks
NOT RUN, owner TASK-021. See docs/verification/TASK-015.md.
**Phase:** 7  
**Depends on:** TASK-014

## Required handoff from TASK-014
Replace the checked-in ASL FoundationComplete terminal with real review creation
and backend-only callback waiting. Preserve original execution input on Catch,
attempt/revision guards and WORKFLOW_FAILED handling. No public task tokens.
TASK-014's successful execution only leaves the Case PROCESSING.

## Acceptance criteria
- task token is backend-only
- unassigned/assigned GSI queries work
- checklist result skeletons are generated

---

# TASK-016 — Claim/start/checklist APIs

**Status:** DONE

Local acceptance under ADR-007: atomic claim/start/check commands, assignment-only
authorization including admin, GSI transitions, audit/ReviewStarted outbox and
optimistic finding versions implemented. ADR-019 resolves the task-owned role/null
representation differences. 429 backend tests/full app checks and 34 mocked
Terraform tests PASS; live concurrency/JWT/IAM/delivery NOT RUN, TASK-021.
See docs/verification/TASK-016.md.
**Phase:** 7  
**Depends on:** TASK-015

## Acceptance criteria
- simultaneous claim gives exactly one winner
- only assigned reviewer can start/update
- starting review updates Case state with audit/event behavior

---

# TASK-017 — Decision callback + finalization

**Status:** DONE
**Phase:** 7  
**Depends on:** TASK-016

## Acceptance criteria
- first valid decision wins
- repeated API retry cannot create second decision
- callback retry uses persisted pending state
- task token never appears in API output

Local acceptance PASS under ADR-007: persisted first-winner decisions, same-key
callback retries, guarded three-branch finalization and technical task cleanup.
See docs/verification/TASK-017.md and ADR-020. Live AWS checks NOT RUN / TASK-021.

---

# TASK-018 — Request-information + resubmission E2E

**Status:** DONE
**Phase:** 7  
**Depends on:** TASK-017

## Acceptance criteria
Demonstrate:

```text
IN_REVIEW
→ NEEDS_INFORMATION
→ upload replacement/addition
→ resubmit
→ new review task
→ APPROVED
```

Previous review history remains immutable.

Local acceptance PASS (2026-09-21): replacement and additive upload journeys use
production handlers with Moto persistence and an explicit workflow service double.
Both reach second-attempt APPROVED; previous task/check/audit and source bytes
remain unchanged. See docs/verification/TASK-018.md. Live E2E NOT RUN / TASK-021.

---

# TASK-019 — Domain notifications

**Status:** DONE
**Phase:** 8  
**Depends on:** TASK-018

## Acceptance criteria
- EventBridge rules feed notification SQS
- worker is idempotent
- SES failure does not roll back Case state
- notification DLQ exists

Local acceptance PASS: 491 backend tests and 38 mocked Terraform tests; see
docs/verification/TASK-019.md and ADR-021. Real SES/delivery/IAM checks NOT RUN,
owned by TASK-021. Completed-event duplicates are suppressed; ambiguous SES
acceptance can cause repeat email.

---

# TASK-020 — Observability + alarms + runbook

**Status:** DONE
**Phase:** 9  
**Depends on:** TASK-019

## Acceptance criteria
- correlation ID propagation
- consistent structured logs
- required metrics
- DLQ/workflow alarms
- diagnosis/redrive runbook

Local acceptance PASS: common safe JSON/EMF, correlation, native tracing, bounded
read-only monitor, dashboard/alarms and controlled recovery. 510 backend tests,
full application checks/builds and 40 mocked Terraform tests PASS. See ADR-022
and docs/verification/TASK-020.md. Live cloud checks NOT RUN / TASK-021; its READY
status authorizes preparation only, not deployment.

---

# TASK-021 — CI/CD hardening + full E2E

User follow-up decision (2026-09-29): keep local results and defer deployment.
Proposed session task021-20260929c is not authorized or started. TASK-021 remains
BLOCKED by remaining non-omitted cloud evidence; TASK-022 TODO. No automatic retry.

Current amendment (ADR-028): user approved omitting actual >24-hour Streams expiry,
14-day callback timeout/closure and literal 85-day aging. Keep these NOT RUN with
duration-omission reason; they no longer gate DONE. Other cloud criteria and cleanup
remain mandatory. Fast supplement prepared under runbooks/fast-cloud-acceptance.md;
new live execution requires scoped approval. Status remains BLOCKED pending that
execution and remaining non-omitted evidence. Older full-duration requirements below
are historical where they conflict with ADR-028.

Latest session task021-20260929b: deployment, five live journeys/seven harness
checks, 12 notification completion receipts and cleanup PASS. All 189 application
resources and 19 fixture objects removed; empty state and independent inventories
verified by 06:20 UTC (about 37 minutes). See verification/TASK-021-20260929b-session.md.
Quota 10 works in ADR-027 opt-in mode. Remaining full matrix criteria (browser,
IAM/fault/retention/alarm/long-duration) prevent DONE; inbox confirmation NOT RUN.
TASK-022 remains TODO; no completion publication. Older notes below are historical
and superseded where they conflict with this session result.

Latest: ADR-027 implements user-requested concurrency-10 acceptance mode, monitor
unreserved only by explicit opt-in. Default contract remains unchanged. See
verification/TASK-021-LOW-QUOTA.md and short-session runbook. Local tests executed;
live evidence NOT RUN pending new-session approval, not waiting for quota increase.

Latest (2026-09-29): authorized quota increase submitted, request
67f8f7f522db429088c4d6029ac575cc5kM3zDV3, CASE_OPENED; actual quota still 10.
Full local verification PASS: backend 560, frontend 6, Terraform mock dev 41 and
bootstrap 1, format/lint/type/build. See verification/TASK-021-QUOTA.md.
Quota authorization is resolved; AWS processing and new-session approval remain.

Latest continuation: guarded retained-state-bucket reuse implemented under ADR-026;
50 operator tests/lint/format/type PASS. Cloud reuse/E2E NOT RUN; quota authorization
and new-session approval remain outstanding. TASK-021 remains BLOCKED.

2026-09-29 shorter-acceptance continuation: target 90 minutes, maximum 120 minutes,
cleanup starts by minute 60. Local-first checks and no optional paid additions.
See runbooks/short-cloud-acceptance.md. Capacity guard and 41 operator tests,
lint/format/type PASS. AWS reads confirm account-plan query execution (details withheld for privacy) and concurrency 10/10;
quota is adjustable but no request was submitted. All cloud criteria remain
mandatory; no new deployment or completion publication.

**Status:** BLOCKED
**Phase:** 10  
**Depends on:** TASK-020

## User-requested frontend continuation (2026-09-29)

Local frontend PASS: responsive Traditional Chinese review workspace, synthetic
in-memory data, search/status filters, document/checklist/activity details,
check-gated local approval, reason-required rejection/information requests,
create draft, template/help dialogs and JSON export. Six tests, lint/format,
TypeScript/Vite build and real desktop/mobile Edge interactions PASS.
See verification/TASK-021-FRONTEND.md. No API integration or cloud deployment
was performed. This explicitly requested UI work does not waive any consolidated
cloud acceptance criterion; overall status remains BLOCKED.

## First approved cloud session result (2026-09-29)

Bootstrap PASS; application apply FAIL on Lambda reserved concurrency (regional
total=10, required minimum unreserved=10, monitor reservation=1). Captured and
deleted all 187 created Terraform application resources; independent service
inventories confirm absence. Five journeys NOT RUN; no test notifications initiated.
Retained approved state bucket/SES identity and AWS-managed empty system backup.
Shared API Gateway service-role deletion rejected by automatic approval review;
user explicitly chose to retain the shared role. See verification/TASK-021-20260929-session.md.
Resolve quota/configuration before another reviewed session. TASK-022 remains TODO.

## Historical preparation progress (2026-09-29)

Local region correction under ADR-024/DEC-028 uses docflow-toolkit/ap-southeast-2.
MCP identity/plan/SES checks PASS. Account-specific billing/credit details withheld for privacy; SES
sandbox has one verified test identity. The old organization-admin SCP-edit suggestion is
superseded. User explicitly authorized one mailbox verification; SES CreateEmailIdentity
PASS; subsequent GetEmailIdentity reports SUCCESS and verified=true. Regional planning allowance is USD 10 for the bounded four-hour subset;
explicit four-hour deployment/test/cleanup approval received; first live execution failed; see current result above.
Local operator checks: 27 tests, lint and mypy PASS. Updated Terraform checks are
recorded in verification/TASK-021.md. All real runtime/cleanup criteria remain
NOT RUN; no completion publication or TASK-022 until they pass.

## Consolidated cloud acceptance

Prepare deployment/E2E/cleanup scripts and a concrete cost/resource/session plan locally.
Then obtain explicit user authorization for a short-lived cloud session. No automatic
deployment on main-branch push. Complete every row in docs/CLOUD_ACCEPTANCE.md, including
all deferred real-service checks from TASK-003 through TASK-020. Keep actual evidence.
Configure remote state before shared/automated deployment per ADR-005.
Perform approved cleanup, inventory remaining resources and record residual costs.
Until live checks and cleanup pass, TASK-021 cannot be DONE and TASK-022 cannot start.

## Acceptance criteria
- PR checks run tests/lint/type/Terraform validation
- dev deployment is reproducible and manually gated; never triggered merely by a push
- happy and critical failure paths E2E verified
- no fabricated verification results

---



# TASK-022 — Portfolio documentation hardening

2026-09-29 supplement: DONE. Added Chinese/English illustrated reference guides,
self-contained offline HTML editions and six actual synthetic-demo screenshots.
See verification/TASK-022-GUIDES.md. Subsequent authorized state-bucket deletion
and no-additional-cost SYSTEM backup expiry are documented in AWS-RETIREMENT.md;
the earlier retained-bucket statement below is historical.

**Status:** DONE
**Phase:** 10  
**Depends on:** TASK-021 gate waived by explicit owner decision, ADR-029.

Deliverables: docs/portfolio/README.md, architecture.md, trade-offs.md, security.md,
cost.md, runbook.md, demo.md and project-2-roadmap.md. Describe partial live
evidence and a synthetic frontend; do not claim skipped tests passed.
Verification: docs/verification/TASK-022.md. Documentation completion does not
change the paid plan. User subsequently chose to retain the listed AWS residual
items and complete TASK-022 only; no deletion or further cloud acceptance is pending.

## Deliverables
- architecture diagram
- design rationale
- security document
- cost document
- runbook
- trade-offs
- demo scenario
- Project 2 AI roadmap

## Acceptance criteria
A reviewer can understand the problem, architecture, reliability, security, cost trade-offs, and demo flow from repository docs alone.


### SES verification request - 2026-09-29

Explicit user authorization received for one email-address identity and its
verification message only. GetEmailIdentity confirmed absence; CreateEmailIdentity
PASS in ap-southeast-2, VerifiedForSendingStatus=false. Wait for user link click
and re-read before considering the identity verified. No application deployment
or test email authorized. This SES identity is a newly created retained prerequisite;
its later deletion is outside existing Terraform cleanup and needs explicit scope.


### SES verification confirmed - 2026-09-29

GetEmailIdentity PASS: VerificationStatus=SUCCESS, VerifiedForSendingStatus=true.
The ignored session config now uses the approved mailbox as sender and reviewer
with its exact regional identity ARN. Supersedes pending-verification notes above.
The user subsequently approved the four-hour deployment/test/cleanup subset
in docs/runbooks/cloud-acceptance.md. Session task021-20260929a started at
02:35:07 UTC; cleanup must finish by 06:35:07 UTC on 2026-09-29.
