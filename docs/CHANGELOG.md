# docs/CHANGELOG.md

## 2026-10-14 — PRIVACY-PUBLISH-01 (completed source publication)

- Purpose: remove private information before the owner-requested public release.
- Files: 13 redacted historical documents; README/AGENTS/PROJECT_STATUS/tasks,
  CHANGELOG/DECISIONS, .gitignore and docs/PRIVACY_REVIEW.md.
- Added: dated redaction notes, reviewed-scope report and private-data ignores.
- Changed: exact account/resource/Site identifiers and home prefixes in candidate
  documents. Original documents/history retained privately; current application,
  infrastructure, schema, test and dependency bytes unchanged.
- Removed: personal commit email/legacy history from new public candidate;
  no original commit or remote ref deleted.
- Bug fixes: none in application behavior.
- Verification: all refs/source metadata read; Gitleaks original-history exit 1
  with one individually verified non-secret test UUID. Post-redaction source
  review found zero remaining reviewed real-PII candidates. Remote surfaces and
  synthetic images read. The final clean-root scan returned exit 1 with the same
  verified UUID false positive; fsck returned exit 0 without unreachable objects.
- Semantic follow-up: 26 account-specific financial readings, three support-case
  references and one individual registration statement were removed/conditioned;
  seven further dated notes added. Only documentation changed; general technical
  prices, estimates and historical results are preserved. Final clean repository
  is rebuilt without provisional earlier commit objects.
- Tests: application tests/lint/type/build/CI and live credential checks NOT RUN;
  authorized privacy checks are recorded separately.
- Publication: owner approved the plan; original ID 1366248864 was renamed to
  docflow-private-archive and kept PRIVATE/read-only. New same-name ID 1418914087
  is PUBLIC; only the reviewed clean root was pushed normally. Original work and
  all refs are retained, old checkout/mirror origins point to the archive and
  clean work uses D:/Projects/docflow-public. Anonymous public access 200,
  private archive/old Git object 404, no application CI run.
- Known issues: this bounded audit cannot prove absence of every unknown encoding
  or external copy. Cloud acceptance remains unfinished; public source is not
  application deployment. The homepage's older email metadata is separate work.

> Privacy note (2026-10-14): private account/resource identifiers and personal home paths have been redacted for the public-release candidate. Historical outcomes are unchanged; placeholders are not live targets.

## 2026-09-29 - TASK-022 bilingual illustrated reference guides

Added Chinese and English purpose/feature/walkthrough guides, self-contained HTML
editions and six real screenshots of the existing synthetic React demo. Linked from
both repository and portfolio entry points. Explicitly separate backend capabilities,
local demo behavior, historical AWS evidence and unfinished production integration.
Checked image rendering, Markdown links and desktop/mobile HTML overflow. No runtime
code changes or AWS calls in this documentation supplement. Full tests not rerun.

## 2026-09-29 - Authorized residual state cleanup

Owner explicitly revoked state bucket and SYSTEM backup retention. Permanently
deleted 47 S3 versions, 12 delete markers and the state bucket; final ListBuckets
returns zero. Both authorized DeleteBackup calls were rejected by DynamoDB because
SYSTEM backups cannot be manually deleted. They expire on 2026-11-03 and official
pricing confirms no additional retention cost. Updated retirement evidence, current
status, ADR-029 amendment and portfolio costs. No code, deployments, restore,
subscriptions, project closure, SES identity or shared role changes. Whole-project
zero billing remains unverified due subscription visibility and SCP restrictions.

## 2026-09-29 - TASK-022 portfolio documentation and retirement inventory

Completed eight portfolio documents: entry guide, architecture diagram, rationale/
trade-offs, security, costs, runbook, demo scenario and Project 2 AI roadmap. Updated
README, requirements/design/status/task records and recovery profile/region examples.
ADR-029 records the user's TASK-021 skip and TASK-022 dependency exception. Evidence
remains partial; synthetic frontend and unpublished acceptance tooling are identified.
Local links/format reviewed; no production code or new AWS deployment/email.
AWS inventory confirms no application workloads in checked services. Automatic
approval review rejected retained-item deletion; user then explicitly chose to
keep those items and complete TASK-022 only. No deletion performed or retried.
Paid-to-free downgrade unsupported; Savings Plans/FSx inventory denied by SCP and
Support UI unavailable/user has not checked. These remain separate from TASK-022 completion.

## 2026-09-29 - TASK-021 follow-up deployment deferred by user

User chose to retain local fast-acceptance work and not deploy. Proposed session
task021-20260929c remains unstarted; no AWS writes or email. Preserved verified
local artifacts and ADR-028 duration omissions. TASK-021 BLOCKED, TASK-022 TODO;
no completion publication or automatic cloud retry.

## 2026-09-29 - TASK-021 duration omissions and fast acceptance supplement

Recorded user-approved long elapsed-time omissions in ADR-028/DEC-033 and aligned
AGENTS, task/status/design/acceptance/runbooks. Production timeouts remain unchanged;
omitted tests stay NOT RUN, other criteria remain required. Added fast live harness
for concurrent/immutable seed, role denials/no-op side effects, signed-header tamper,
real browser Blob upload and allowed/denied CORS origins. Added local negative tests
to reject false browser PASS and browser CORS misconfiguration. No new cloud writes
or completion publication. Verification details: verification/TASK-021-FAST.md.
Full local check PASS: 574 backend tests, frontend checks/build, Python package,
lint/format/type; browser fake-service positive/negative check PASS; AWS read-only
preflight PASS with quota 10 and zero functions. New live probes remain NOT RUN.

## 2026-09-29 - TASK-021 approved concurrency-10 live session

Session task021-20260929b deployed 189 resources using 13 unreserved Lambdas.
Five real journeys and seven harness checks PASS, including SRP/JWT, approve,
reject, replacement/additive resubmission, invalid documents and claim race.
Twelve COMPLETED notification receipts observed; inbox confirmation NOT RUN.
Removed 19 fixture objects, unlocked two protections and destroyed all 189
application resources. Empty remote state and independent inventories PASS by
06:20 UTC, about 37 minutes after start. Retained original state bucket, SES,
shared role and AWS-managed SYSTEM backups. See verification/TASK-021-20260929b-session.md.
TASK-021 remains BLOCKED by remaining browser/IAM/fault/long-duration criteria;
TASK-022 TODO. No completion publication; no quota increase needed for this mode.

## 2026-09-29 - TASK-021 opt-in concurrency-10 acceptance

Added low-quota dev/module/session flag. Monitor uses shared capacity only in
this mode; default reservation remains 1. Matching capacity guard requires 10,
and deploy/cleanup retain the same mode. Added Python and Terraform regression
tests and ADR-027. No AWS application resources or emails created this turn.

## 2026-09-29 - TASK-021 quota application and full local verification

After explicit approval and duplicate check, requested regional Lambda concurrency
1000. AWS returned PENDING, then CASE_OPENED (case <REDACTED_SUPPORT_CASE>); effective quota
remains 10. Full application checks PASS (560 backend/6 frontend tests), acceptance
helper syntax PASS, Terraform fmt/validate and 41+1 mocked tests PASS. Existing
published commit CI PASS. No application deployment, email, paid capacity purchase
or completion publication. TASK-021 remains BLOCKED awaiting AWS processing.

## 2026-09-29 - TASK-021 guarded retained-state reuse

Added optional original bootstrap-session identity, exact-name/owner/region/tag
checks and required versioning/public-access-block/AES256 checks. Reuse retains
the original backend key and locking, rejects re-bootstrap and managed prior
application state. 50 operator tests, project Ruff and strict mypy PASS. No live
reuse, deployment, email, quota request or completion push. See ADR-026.

## 2026-09-29 - TASK-021 shortened acceptance preparation

Added read-only capacity guard to preflight and fresh plan/apply, leaving cleanup
independent of quota. 41 operator tests, project Ruff lint/format and strict mypy
PASS. AWS reads confirm account-plan query execution (details withheld for privacy), concurrency 10/10 and adjustable quota.
Prepared 90-minute target / two-hour maximum plan with cleanup from minute 60.
No deployment, quota request, email or paid additions. TASK-021 remains BLOCKED.

## 2026-09-29 - Frontend design and online preview

Added the Traditional Chinese review workspace with responsive layout, synthetic
cases, filtering, guarded decisions, history, draft creation and JSON export.
Published a private static Site after GitHub rejected Pages for this repository's
plan. Kept the GitHub repository private. No new dependencies or AWS deployment.
Frontend format/lint/six tests/type/build and browser checks PASS. See
frontend/PUBLISHING.md for the live link and update procedure. TASK-021 remains
BLOCKED; this frontend publication is not a task-completion commit.

## 2026-09-29 - TASK-021 - Local document-review frontend

User-requested frontend design implemented in the existing React/TypeScript stack:
forest-green/sage Traditional Chinese workspace, responsive case/detail layout,
search/filter/empty states, create-draft form, document information, template view,
four-check approval guard, reason-required decisions, immutable demo history,
filtered JSON export and reset. No new dependencies or external page requests.
Explicit in-memory demo boundary; no login/upload/API/email integration claimed.
PASS: six frontend tests, format/lint/type/build, headless Edge desktop/mobile
interactions and screenshot review. TASK-021 cloud blocker unchanged; no AWS
mutation, completion commit or push. See verification/TASK-021-FRONTEND.md.

## 2026-09-29 - TASK-021 - First deployment failed; application cleanup PASS

CloudTrail confirmed monitor reserved-concurrency rejection: total regional quota
10, minimum unreserved 10, requested reservation 1. The apply created 187/189
Terraform resources and stopped before live journeys. All 187 session application
resources were destroyed after the reviewed protection-only update; empty state
and independent service inventories PASS. Retained state/SES as approved and an
AWS-managed empty system backup. Shared API Gateway service-role deletion was
blocked by automatic approval review; user explicitly chose to retain the shared role.
Fixed private failure-log preservation and protection-only partial-apply cleanup;
29 operator tests, Ruff lint/format and focused mypy PASS. No runtime test emails
initiated; no completion commit/push. TASK-021 BLOCKED, TASK-022 TODO.
See verification/TASK-021-20260929-session.md for exact evidence and retained items.

## 2026-09-29 - TASK-021 - Approved first live session

User approved the bounded four-hour deployment, five synthetic cases, fewer than
100 notification attempts to the verified mailbox and cleanup on success/failure.
Session task021-20260929a: 02:35:07-06:35:07 UTC; USD 10 planning allowance, not
a hard cap. Protected state bucket bootstrap PASS (five Terraform resources).
Create-only application plan reviewed: 189 resources, including 13 Lambda,
29 alarms and 15 log groups. Application apply is in progress. No pre-existing
DocFlow application resources found in the pre-deployment service inventories.
State bucket and SES identity will be retained; longer tests remain NOT RUN.

All meaningful changes are recorded by task.

---

## 2026-09-29 - TASK-021 selected-region preparation

- ADR-024/DEC-028 correct acceptance tools, state bootstrap/backend, SDK and HTTP/S3
  guards to docflow-toolkit/ap-southeast-2. Add wrong-region/profile rejection tests.
- MCP STS/plan/SES PASS; account-specific billing/credit details withheld for privacy; sandbox and zero identities.
- User provided test mailbox privately and selected MEDIUM guidance. No email,
  deployment, SCP or billing mutation. Updated checks in verification/TASK-021.md.


## 2026-09-29 - Agent Toolkit setup and region diagnosis correction

2026-09-29 Toolkit setup: AWS CLI 2.37.5 and uv 0.12.20 installed.
docflow-toolkit login/STS PASS, selected region ap-southeast-2; existing docflow-dev
region left unchanged. Official configure agent-toolkit PASS, 24 default skills
installed, catalog lists 110 skills, aws-mcp profile bound and original Codex config
preserved. New-experience rules appended to AGENTS.md without replacing the contract.
SES GetAccount/ListEmailIdentities PASS in ap-southeast-2: sending enabled,
production access false (sandbox), zero identities. No SCP changes, email or
deployment performed. MCP availability in a restarted Codex session is NOT RUN.


## 2026-09-29 - TASK-021 - Authenticated preflight

2026-09-29: Login and STS identity PASS for docflow-dev/us-east-1 (account ending 8998). SES GetAccount and ListEmailIdentities BLOCKED by explicit AWS Organizations SCP deny (<REDACTED_SCP_ID>). Verified identities, sandbox status and test mailbox remain unknown. Organization administrator action is required. No AWS policy changes, deployment or email performed.

### Earlier login attempt

- Started explicitly requested docflow-dev login; browser authorization pending.
- SES/account read-only checks NOT RUN pending callback. No credentials, tokens
  or authorization URLs printed; local login diagnostics stay ignored. No AWS
  deployment or email. Task remains IN_PROGRESS.

## 2026-09-28 - TASK-021 - Cloud acceptance preparation (IN_PROGRESS)

- Hardened check-only CI with pinned Actions, timeouts and concurrency.
- Prepared protected S3 state bootstrap, account/session/plan-hash guarded operator
  deployment, production-client SRP journeys, sanitized evidence and scoped cleanup.
- Added 21 local guard tests, bootstrap mock coverage and a bounded cost/resource/
  cleanup plan plus a complete manual scenario worksheet. ADR-023/DEC-027.
- Live AWS checks and hosted CI NOT RUN; authentication BLOCKED by expired login.
  No AWS writes, email or deployment. No completed-task commit/push.
- Verification results are recorded in verification/TASK-021.md; TASK-021 stays
  IN_PROGRESS pending explicit authorization, real acceptance and approved cleanup.

## 2026-09-23 - TASK-020 - Observability, alarms and operations

- Added safe common JSON/EMF logging with invocation-context isolation, HTTP/
  workflow correlation and upload correlation preserved through document processing.
- Implemented required domain/retry/duration metrics and a bounded read-only
  pending-work monitor with projected Scan IAM, zero gauges and missing heartbeat.
- Added native Lambda/Standard X-Ray, both DLQ/workflow/error-rate/retry/pending/
  heartbeat/per-rule EventBridge alarms and operations dashboard. No payload
  tracing or new runtime dependency; central ownership now covers 15 log groups.
- Added IAM-only exact-fact outbox recovery and diagnosis/redrive procedures.
  ADR-022/DEC-026 document approximate metric semantics, scan bounds and console-only
  alarm defaults. Public API/event schema shapes and business transaction rules stay.
- PASS: 510 backend tests (19 new observability cases), complete app lint/format/
  types/frontend test/build and Python build; 40 mocked Terraform tests, readonly
  init/fmt/validate, deterministic ZIP and isolated imports.
- NOT RUN: live AWS/EMF/X-Ray/IAM/alarm actions/recovery and hosted CI. Cloud evidence
  remains TASK-021; no AWS writes/deployment/messages. TASK-020 locally DONE;
  TASK-021 READY for preparation, with explicit approval required before deployment.

## 2026-09-21 - TASK-019 - Domain notifications

- Added four-type custom-bus routing, encrypted notification SQS/DLQ, partial-batch
  Lambda and least-privilege table/Cognito/SES permissions.
- Worker verifies committed outbox facts and uses leased permanent event receipts.
  SES failures retry independently of Case transactions; ambiguous acceptance can
  resend email. Verified requester lookup and configured reviewer mailbox are
  documented in ADR-021/DEC-025. No public API/event schema changes.
- Added 18 notification integration cases including duplicate/lease/recipient
  rejection, failure isolation, accepted-send gap and mocked routing/redrive.
- PASS: full application check (491 backend tests, frontend test/build, Python
  build, lint/format/types), 38 mocked Terraform tests, init/fmt/validate and
  deterministic isolated Lambda ZIP.
- Added notification operations runbook and updated cloud acceptance requirements.
  Default null email configuration disables activation. No AWS writes/email sent.
- NOT RUN: real AWS/SES/IAM/delivery and hosted CI; cloud owner TASK-021.
  TASK-019 locally DONE; TASK-020 READY.

## 2026-09-21 - TASK-018 - Request-information and resubmission E2E

- Added local replacement and additive-upload journeys through production
  Case/document/review HTTP boundaries, document SQS handler, workflow starter,
  validation/creation/finalizer and outbox publisher over Moto.
- Proved IN_REVIEW -> NEEDS_INFORMATION -> upload -> SUBMITTED -> new review ->
  APPROVED. Missing/pending documents reject resubmit without consuming its key.
- Verified distinct execution/task/token, fresh checklist, immutable prior review
  and audits, retained original S3 bytes, late worker isolation and safe API retries.
- PASS: 2 E2E scenarios, Ruff lint/format and repository-scoped mypy (70 files).
  Production code, dependencies, infrastructure and API/event contracts unchanged.
- NOT RUN: unchanged frontend/build/Terraform/full regression and live AWS E2E.
  Last full baseline remains TASK-017; live checks belong to TASK-021 under ADR-007.
  TASK-018 locally DONE; TASK-019 READY.

## 2026-09-20 - TASK-017 - Decision callback and finalization

- Added assigned-only decision API with UUID idempotency, bound required-check
  validation and checkRevision/Case/Task transaction guards. First decision wins;
  retry cannot create another decision or overwrite completed findings.
- Persisted COMPLETED/PENDING decision/audit before trusted SendTaskSuccess.
  Same request retries saved output. Closed/expired tokens remain ambiguous;
  matching finalization reconciles lost responses and failed acknowledgements.
- Added three guarded finalization branches, atomic Case/task/audit/outbox and
  CaseApproved/CaseRejected/AdditionalInformationRequested event contracts.
  Technical failure closes the task while preserving accepted decision/history.
- Wired decision JWT route, finalizer Lambda, exact worker invocation and scoped
  callback action. Added table Query for checklist/template reads. No dependencies.
- ADR-020/DEC-024 resolve admin assignment and NULL/absent decision semantics.
  OpenAPI 0.9.0, design/PRD, recovery and cloud acceptance synchronized.
- PASS: 471 backend tests (42 added), complete application lint/format/type checks,
  frontend test/build and Python package builds; 34 mocked Terraform tests,
  readonly init/fmt/validate and deterministic ZIP/isolated imports.
- NOT RUN: AWS deployment/live IAM/JWT/callback/delivery/concurrency and hosted CI.
  Cloud evidence remains TASK-021. TASK-017 locally DONE; TASK-018 READY.
  Work resumed on September 20 after interrupted full-check output was unavailable.

## 2026-09-17 - TASK-016 - Claim, start and checklist commands

- Added conditional reviewer/admin claim with one-winner ownership/GSI1/audit,
  and assigned-only start/check updates; admins cannot bypass assignment.
- Start atomically updates Task IN_PROGRESS, Case IN_REVIEW/version/GSI2, audit
  and ReviewStarted outbox. Active same-owner retries create no duplicate facts.
- Check updates require existing skeletons and current Case/Task gates; internal
  check versions/task checkRevision reject stale writes and support TASK-017
  decision fencing. Identical retries are no-ops; comments stay out of audit/events.
- Added three scoped JWT routes, PUT CORS, planned command Lambda with GetItem-only
  reads and CASE-only transactional writes. API 0.8.0/event schemas synchronized.
- ADR-019 explicitly resolves Admin=Yes and absent-only reviewerId design wording
  using higher-priority task acceptance and existing NULL task representation.
- PASS: 429 backend tests (55 added), full application checks/builds, 34 mocked
  Terraform plans, readonly init/fmt/validate, deterministic ZIP/isolated imports.
  Initial event test tap omission fixed and re-verified in the full suite.
- NOT RUN: live AWS concurrency/JWT/IAM/delivery and hosted CI; cloud evidence remains
  TASK-021. TASK-016 locally DONE; TASK-017 READY. No deployment or cloud writes.

---

## 2026-09-17 - TASK-015 - Review creation and queue queries

- Replaced FoundationComplete with real callback task creation/waiting. Original
  submission is retained on Catch; 14-day timeout records technical failure.
- Deterministic attempt task ID; hidden guarded preparation supports 98 checks,
  then atomic Task/Case REVIEW_PENDING/audit/CaseReadyForReview outbox publication.
  Retry and newer token generation handling preserve findings and prevent duplicates.
- Added reviewer/admin available/mine GSI1 queues and detail, scoped pagination,
  consistent stale-assignment filtering and explicit public projections.
- Added two scoped JWT routes, creator/query IAM, packaging and event/API contracts.
  ADR-018 documents dueAt +48h, retry semantics and TASK-016/017 boundaries.
- PASS: 374 backend tests (28 added), full application checks/builds, 31 mocked
  Terraform plans, readonly init/fmt/validate, deterministic ZIP and isolated imports.
- NOT RUN: live AWS callbacks/IAM/GSI behavior and hosted CI; TASK-021 owns cloud
  evidence. No deployment or AWS writes. TASK-015 locally DONE; TASK-016 READY.

---

## 2026-09-17 - TASK-014 - Standard workflow foundation

- Added actual SDK Standard initiation after submit and receipt replay, fixed
  name/input reconciliation, conditional ARN acknowledgement and stale-attempt guards.
- Added filtered CASE/PENDING Stream recovery and IAM-only operator recovery after
  retention expiry; 85-day age guard prevents accidental name reuse. No domain
  EventBridge orchestration or new runtime dependency.
- Added defensive validation with transactional PROCESSING audit, and technical
  WORKFLOW_FAILED/audit/CaseWorkflowFailed transaction; retries never business-reject.
- Added Standard ASL/Terraform, two planned workers, exact workflow/worker IAM,
  centralized logs with payload data disabled and four infrastructure contract runs.
- FoundationComplete is explicitly the TASK-014 boundary; TASK-015 adds review/callback.
  API replays may enrich confirmed same-attempt ARN. Contracts and ADR-017 synchronized.
- PASS: 346 backend tests, full application checks/builds, 28 mocked Terraform plans,
  backend-disabled readonly init, fmt/validate and deterministic ZIP/isolated imports.
- NOT RUN: AWS deployment, real orchestration/IAM/recovery and hosted CI; TASK-021.
  No AWS writes. TASK-014 locally DONE, TASK-015 READY.

---

## 2026-09-16 - TASK-013 - Submit/resubmit validation

- Explicitly resolved PRD/design discrepancy to SUBMITTED for both operations
  (ADR-016/DEC-020), then PROCESSING under the subsequent workflow.
- Added owner/admin commands, bound-template 422 gates, atomic version/attempt
  updates with audit/outbox and durable scoped UUID receipts; no direct publishing.
- Fenced paginated document validation using transactionally incremented Case
  documentRevision across reservation, deletion and processor transitions.
- Added JWT routes, idempotency CORS, receipt/revision IAM, API and event schemas;
  publisher supports CaseSubmitted/CaseResubmitted. No dependency changes.
- Persisted stable workflow start intent; actual Standard start, ARN persistence
  and crash recovery remain TASK-014. Public execution ID is null until actual start.
- PASS: 313 backend tests, full lint/format/types, frontend test/build, Python build,
  24 mocked Terraform plans, fmt/validate and deterministic ZIP/isolated imports.
- Initial type annotation and Terraform computed-ARN fixture issues corrected
  before final passing checks. AWS/hosted CI NOT RUN; live evidence in TASK-021.
- TASK-013 locally DONE; TASK-014 READY. No AWS deployment or writes.

---

## 2026-09-16 - TASK-012 - Custom domain event bus

- Added domain_events module and dev bus outputs; replaced planned ARN with actual
  bus dependency and enabled publisher stream configuration. No cloud deployment.
- Kept S3 on default, command roles without publisher grants, and no forwarding
  or production domain subscribers. Runtime code/dependencies unchanged.
- Added routed envelope schema referencing existing Case/document detail schemas.
  Added 10 local producer-to-bus isolation, contract-negative and boundary tests.
- PASS: 260 backend tests, application lint/format/types, frontend test/build and
  Python build; 24 Terraform mocked plans plus readonly init/fmt/validate.
- NOT RUN: unchanged Lambda ZIP revalidation, hosted CI and real AWS bus delivery/
  IAM, with cloud checks retained under TASK-021. No AWS writes.
- ADR-015/DEC-019 and status/design/events/infra docs synchronized. TASK-012 locally
  DONE; TASK-013 READY with its required resubmit-state discrepancy resolution.

---

## 2026-09-16 - TASK-011 - Transactional outbox stream publisher

- Retained existing state/audit/outbox transactions; added consistent outbox reads,
  exact envelope serialization, custom-bus preflight and per-entry send checks.
- Added conditional DISPATCHED bookkeeping, stable business-ID retry semantics,
  first-failed-sequence responses and safe correlation logging.
- Added stream filter/IAM/Lambda composition; dev mapping intentionally disabled
  until TASK-012 creates and connects the custom domain bus. No default fallback.
- Added 36 local publisher tests, including actual Moto DynamoDB Stream records,
  Case/document contracts, accepted-send/failed-mark duplicates and concurrent updates.
- PASS: 250 backend tests, full application lint/types/frontend/build, 22 mocked
  Terraform plans, init/fmt/validate and deterministic ZIP/isolated publisher import.
- Recorded ADR-014/DEC-018, outbox no-TTL clarification, stream-expiry recovery and
  TASK-012 handoff. Runtime dependencies and public API unchanged.
- NOT RUN: real AWS stream checkpoint/delivery/IAM and hosted CI, owned by TASK-021.
  TASK-011 locally DONE; TASK-012 READY. No cloud deployment.

---

## 2026-09-16 - TASK-010 - Document processor and recoverable idempotency

- Added raw-event/source validation, conditional version-pinned S3 reads, bounded
  SHA-256 and size/MIME/extension/metadata/signature checks.
- Added leased claims, audited UPLOADED/VALIDATING stages, atomic terminal
  state/audit/outbox/COMPLETED claim and durable duplicate/tombstone guards.
- Added partial SQS batch responses, scoped Lambda IAM and 60-second/batch-5 mapping.
- Added document validation schema and deployable processor ZIP contents.
- PASS: full application check with 211 backend tests, frontend check/build and
  Python build; final 29 processor tests including 3 added image/version cases
  (214 total cases); final targeted lint/types; 20 mocked Terraform plans,
  init/fmt/validate; deterministic ZIP/isolated import and package limits.
- Local forced failure reaches Moto DLQ after five receives. Real AWS
  retry/DLQ/IAM and hosted CI NOT RUN, owned by TASK-021. No cloud deployment.
- TASK-010 locally DONE; TASK-011 READY. ADR-013/DEC-017 record recovery semantics.

---

## 2026-09-16 - TASK-009 - S3 EventBridge and SQS pipeline

- Added exact-bucket/cases-prefix Object Created routing on the default bus,
  preserving the raw envelope and enabling bucket notifications after target setup.
- Added SSE-SQS standard main/DLQ queues, TLS-only policies, exact-rule publishing,
  source-restricted redrive, 360-second visibility, 4/14-day retention and maxReceiveCount 5.
- Added ten Moto routing cases and two Terraform plan runs; test-only Moto extras
  and jsonpath-ng support the SDK integration. Runtime dependencies unchanged.
- PASS: full application check, 185 backend tests, frontend test/build, lint/types,
  dependency check, Terraform init/fmt/validate and 18 mocked plan runs.
- Updated ADR-012/DEC-016, design, event/infra docs, cloud ledger and task handoff.
- NOT RUN: cloud delivery/IAM/encryption/retry/redrive and hosted CI; deferred
  TASK-021. No deployment. TASK-009 locally DONE; TASK-010 READY.

---

## 2026-09-16 - TASK-008 - Document metadata and soft deletion

- Added owner/admin-only DELETE with mutable Case gate, transactionally guarded
  document update/audit, conflict responses and current-state-checked no-op retry.
- Retained source metadata/S3 bytes, filtered tombstones from Case detail and
  verified replacement uses a new ID/key. Existing template/type constraints remain.
- Added scoped DELETE JWT route/CORS and transaction-only DynamoDB UpdateItem;
  no S3 delete permission, cleanup or event publication.
- Synchronized OpenAPI 0.4.0, PRD, design, ADR-011/DEC-015 and cloud handoff.
- PASS: 175 backend tests including 67 document tests, full lint/types/frontend
  checks/builds, 16 Terraform mock runs, fmt/validate and deterministic isolated ZIP.
- NOT RUN: real JWT/CORS/IAM/concurrency/late-event processing; deferred TASK-021.
  TASK-008 locally DONE; TASK-009 READY. No deployment.

---

## 2026-09-16 - TASK-007 - Private S3 and direct upload authorization

- Added metadata-only document-command-handler: owner/admin checks, mutable Case
  gate, historical template validation and atomic initial Document/audit reservation.
- Generated stable backend S3 keys; issued 600-second SigV4 PUT binding MIME/length
  and If-None-Match. No file bytes enter Lambda; no URLs enter storage/logs.
- Added private SSE-S3/TLS/ACL-disabled storage, conditional writes, signature-age
  policy, exact-origin CORS, scoped IAM and authenticated upload route.
- Extended deterministic Lambda package; reused DynamoDB fixture for upload tests.
- Updated OpenAPI 0.3.0, ADR-010/DEC-014, design, API/infra instructions and handoff.
- PASS: 147 backend tests (39 document), full application lint/types/builds,
  16 mocked Terraform tests, validate/fmt and deterministic isolated packaging.
  Final 9 state-gate tests rerun PASS after clearer signing-call assertions.
- NOT RUN: deployed expiry/signature/CORS/IAM/direct HTTP upload, hosted CI and
  arm64 runtime; cloud evidence remains TASK-021. No AWS deployment.
- TASK-007 locally DONE; TASK-008 READY. Initial metadata/type checks were necessary
  upload prerequisites; remaining delete/lifecycle work stays TASK-008.

---

## 2026-09-16 - TASK-006 - Authorization and ownership regression tests

- Added 49 cases to the real HTTP-boundary/Moto repository tests, covering the
  requester/reviewer/admin matrix, assignment changes, cross-Case isolation,
  identity/query/cursor forgery, private-field filtering and denied-write effects.
- Existing production behavior passed; no runtime, API contract, IAM or dependency change.
- PASS: 74 Case tests; full application check with 108 backend tests, frontend
  test/type/build, Ruff/mypy and backend sdist/wheel.
- NOT RUN: Terraform/package revalidation (unchanged), hosted CI and live AWS
  JWT/IAM/HTTP acceptance (deferred to TASK-021).
- Updated API authorization coverage, cloud acceptance ledger, status and evidence.
  TASK-006 locally DONE; TASK-007 READY. No deployment.

---

## 2026-09-16 - TASK-005 - Case create/query APIs

- Added four Lambda API routes with trusted claims, role/ownership enforcement and
  explicit scalar/nested response projections; preserved the health route.
- Bound immutable active templates; transactionally inserted Case/audit/CaseCreated outbox.
- Implemented GSI1/GSI2 pagination, empty-filter continuation and scoped activity cursors.
- Wired separate command/query IAM and routes; bundled pinned SDK in deterministic ZIP.
- Updated OpenAPI 3.1, event schema, ADR-009, design and verification/handoff records.
- PASS: application checks/builds, 59 backend tests, 12 Terraform mock tests, isolated
  ZIP loading and dependency checks. NOT RUN: real cloud/hosted CI/arm64 execution.
- TASK-005 locally DONE; TASK-006 READY. No deployment or domain event publication.

---

## 2026-09-16 - TASK-004 - Immutable checklist templates and seed

- Added validated immutable Template/Check models and supplier-onboarding v1.
- Implemented strongly consistent paginated active/historical reads and conditional
  atomic metadata/check/audit publication; identical replay is a no-op, conflicts fail.
- Added preview-first loopback-only seed CLI, pinned boto3 SDK and local Moto tests.
- Recorded ADR-008 / DEC-012 and synchronized design, backend instructions and cloud ledger.
- PASS: application checks/builds, final backend 34 tests (8 local integration), types,
  formatting/lint and dependency consistency. NOT RUN: cloud/Terraform (no infra changes).
- TASK-004 locally DONE; TASK-005 READY. No AWS resources created or changed.

---

## 2026-09-15 - Development plan - local development and consolidated acceptance

- User approved local development first, then short-lived cloud acceptance.
- Added ADR-007, DEC-011 and CLOUD_ACCEPTANCE ledger; synchronized AGENTS and plans.
- TASK-003 through TASK-020 use explicit local acceptance; preserve real AWS
  requirements under TASK-021. TASK-022 remains gated on real acceptance.
- TASK-003 is DONE against existing local evidence; TASK-004 is READY.
- GitHub publication continues for locally DONE tasks. No AWS deployment on push;
  session scope, cost and cleanup require explicit authorization.
- No cloud writes, new service checks or product implementation changes in this revision.

---

## 2026-09-15 - TASK-003 - Local implementation; deployment deferred

- STS identity PASS for docflow-dev/us-east-1; prior authentication blocker resolved.
- Account plan query executed; billing/credit details withheld for privacy; user explicitly declined deployment.
- Added Cognito Lite pool/public SRP client/groups, scoped HTTP API JWT health route,
  minimal log-only Lambda and deterministic package builder; wired existing log groups.
- Added health unit/contract tests, Terraform security tests, OpenAPI and ADR-006.
- Application checks/builds PASS; latest backend tests 14 PASS; Terraform tests 9 PASS.
- Package determinism and isolated ZIP invocation PASS. Live cloud checks NOT RUN.
- TASK-003 remains BLOCKED for cloud acceptance. No deployment or GitHub publication.

---

## 2026-09-15 - TASK-003 - Authentication prerequisite recheck

- STS caller identity for docflow-dev/us-east-1: FAIL, NoCredentials (exit 253).
- Account activation and CLI authorization remain unverified.
- TASK-003 remains BLOCKED under AGENTS.md section 12; deployment and implementation checks NOT RUN.
- Updated status, task blocker and verification evidence; no cloud deployment or GitHub publication.

---

## 2026-09-13 - TASK-003 - AWS CLI prerequisite resolved

- Installed official per-user AWS CLI 2.36.44 on explicit user request after verifying its Amazon Authenticode signature.
- Configured local profile docflow-dev with us-east-1 and JSON output.
- Started official browser login with authentication output suppressed; awaiting user completion.
- Installer/version/profile checks: `PASS`. Caller identity and deployment authentication: `BLOCKED` pending login.
- Follow-up STS: FAIL (NoCredentials, exit 253). User reached the console but CLI authorization remained incomplete; opened a fresh CLI authorization page.
- TASK-003 remains BLOCKED; no implementation, cloud deployment or completed-task publication.

---

## 2026-09-12 - TASK-003 - BLOCKED

### Changed
- Read the project contract, state, task criteria, current decisions/ADRs and authentication/infrastructure baseline.
- Checked AWS environment prerequisites without reading or outputting credential values.
- Marked TASK-003 BLOCKED and synchronized PROJECT_STATUS, tasks and docs/verification/TASK-003.md.
- Stopped under AGENTS.md section 12 before implementation. Completed-task automatic publication is not triggered.

### Verification
- Working tree at session start: `PASS`, clean.
- Local prerequisite inventory: `PASS`, no AWS CLI on PATH, no AWS environment variables, no default config/credentials files; Python 3.13 has no boto3.
- AWS caller identity/deployment access: `BLOCKED`, no local authentication configuration discovered and CLI absent.
- Unit/lint/type/build/Terraform and live authenticated/invalid/missing-token checks: `NOT RUN`, no implementation or deployment.
- TASK-002 remains DONE; TASK-004 remains TODO.

---

## 2026-09-12 - TASK-002 - DONE

### Added
- Terraform dev root with version/provider constraints, local backend, inputs/outputs and HashiCorp AWS 6.64.0 lockfile with signed Windows/Linux checksums.
- Database module: docflow-dev, String PK/SK, GSI1/GSI2 ALL projections using key_schema, on-demand billing, expiresAtEpoch TTL, NEW_AND_OLD_IMAGES Stream, PITR and default deletion protection.
- Observability module and 14 baseline log groups with configurable finite retention (14-day default).
- Six credential-free mock plan tests and a separate Terraform PR CI job.
- DEC-009, ADR-005 and docs/verification/TASK-002.md.

### Changed
- On explicit user request, added AGENTS.md section 7.1: automatically commit and push completed tasks using the task-ID message format; synchronized the standing authorization in PROJECT_STATUS.
- README, infra README and Technical Design now document the implemented foundation, module integration outputs and state boundary.
- TASK-002 is DONE; TASK-003 is READY. PROJECT_STATUS is synchronized.
- No AWS deployment, business behavior, API or event contract change.

### Verification
- Terraform fmt, readonly init and validate: `PASS`; final validation has no warnings.
- Terraform mock tests: `PASS`, 6 passed, 0 failed.
- Local backend init and official provider platform lock checks: `PASS`.
- Initial GSI deprecation warnings resolved by using provider key_schema.
- Initial schema introspection: `FAIL` because local backend was not initialized; `PASS` after local init.
- Initial diff check: `FAIL` on Markdown trailing spaces; corrected. Final diff/ignore/source-pattern/documentation checks: `PASS`.
- Application tests/builds: `NOT RUN`; application sources/dependencies unchanged.
- AWS plan/apply, integration/contract/E2E/smoke and GitHub-hosted CI: `NOT RUN`; no cloud deployment or business handlers in this task.
- Initial managed shell access: `BLOCKED` by setup refresh errors; approved escalated commands completed the work.

---

## 2026-09-11 - TASK-001 - DONE

### Added
- Repository directories matching Technical Design, with tracked placeholders for future handlers and Terraform modules/environments.
- Python 3.13 package, Ruff/mypy/pytest/build configuration, resolved dev pins, shared namespaces and 7 package-import baseline tests.
- React/TypeScript shell with Vite, ESLint, Prettier, Vitest, exact dependencies and npm lockfile; 1 rendering baseline test.
- Cross-platform scripts/dev.py bootstrap/check/format and individual developer commands.
- Git/editor/line-ending defaults, safe environment examples and baseline GitHub Actions workflow.
- docs/verification/TASK-001.md with actual checks and exact changed-file inventory.

### Changed
- README local bootstrap instructions, Technical Design scaffold clarification, DEC-008 tooling record and status/task handoff synchronization.
- TASK-001 is DONE and TASK-002 is READY. User explicitly deferred the resubmission-state discrepancy to TASK-013; no state semantics were changed.
- Downloaded project-local Node 22.23.2 from nodejs.org and verified its published SHA256. Runtimes, dependencies and build outputs are ignored.

### Verification
- `py -3.13 scripts/dev.py bootstrap`: `PASS`.
- `py -3.13 scripts/dev.py check`: `PASS` - lint, formatting, strict type checks, 7 backend tests, 1 frontend test, frontend production build and backend package build.
- Production preview HTTP smoke: `PASS` - HTML/JS/CSS; process stopped afterward.
- Directory/ignore/common secret-pattern review and diff formatting: `PASS`.
- Initial Ruff import sorting: `FAIL`; corrected and complete checks rerun with `PASS`.
- Terraform fmt/validate, integration/contract/cloud E2E: `NOT RUN` - no relevant implementation yet.
- GitHub-hosted CI and POSIX runtime execution: `NOT RUN` - verified locally on Windows only.

---

## 2026-09-11 - TASK-001 - Python runtime prerequisite resolved

### Changed
- Installed Python 3.13.15 and bundled pip 26.2.1 for the current Windows user on explicit request, using the hash-verified python.org installer through winget.
- Initial installation waited for elevation to install the system launcher; restarted with Include_launcher=0 to retain the existing launcher and complete a per-user installation.
- Updated `PROJECT_STATUS.md` and `docs/tasks.md` to clear the Python blocker. TASK-001 remains BLOCKED by the previously recorded documentation discrepancy.

### Verification
- `py -3.13 --version`: `PASS` - Python 3.13.15.
- `py -3.13 -m pip --version`: `PASS` - pip 26.2.1.
- ssl/sqlite3/venv imports: `PASS`.
- Temporary virtual environment creation with pip and cleanup: `PASS`.
- `py -0p`: `PASS` - Python 3.13 registered alongside existing installations; use the explicit version selector.
- Interim pip/import checks during installation: `FAIL` - standard library not yet installed; the same checks passed after installer completion.
- Application tests/builds: `NOT RUN` - application scaffolding has not started.

---

## 2026-09-11 - TASK-001 - BLOCKED

### Changed
- Read all 13 existing Markdown documents and checked local runtimes before implementation.
- Recorded TASK-001 as BLOCKED in `docs/tasks.md` and synchronized `PROJECT_STATUS.md`.
- Recorded missing Python 3.13 and the PRD section 7 / Technical Design sections 8.1 and 13.8 discrepancy over the persisted resubmission state.
- Stopped under AGENTS.md section 12; no application scaffold, dependencies, infrastructure, or business-state decision was introduced.

### Verification
- Documentation review: `PASS` - all existing documents read, including four ADRs.
- Runtime discovery: `PASS` - Python launcher lists 3.9/3.10; Node v16.13.0; npm 8.1.0.
- Python 3.13 availability: `BLOCKED` - not listed by the launcher.
- Initial Git status: `PASS` - clean using a command-scoped safe.directory exception.
- Backend tests/lint/format/type check and frontend tests/lint/type check/build: `NOT RUN` - scaffolding stopped before implementation.
- Integration/contract/smoke tests and Terraform fmt/validate: `NOT RUN` - no application, contracts, or infrastructure implementation exists.

---

## 2026-09-11 — TASK-000

### Added
- `AGENTS.md` permanent AI/Codex development contract.
- `PROJECT_STATUS.md` cross-session state handoff.
- `docs/tasks.md` ordered implementation plan with acceptance criteria.
- `docs/DECISIONS.md` decision log.
- `docs/CODEX_PROMPTS.md` short prompt reference.
- Initial ADRs for the current architecture baseline.

### Changed
- Updated `docs/TECHNICAL_DESIGN.md` to include project-state/document governance and the mandatory Codex workflow.

### Test
- Application tests: `NOT RUN` — no application code yet.
- Lint: `NOT RUN` — tooling not created yet.
- Type check: `NOT RUN` — tooling not created yet.
- Build: `NOT RUN` — application not created yet.
- Terraform validate: `NOT RUN` — Terraform implementation not created yet.


## TASK-021 SCP remediation diagnosis - 2026-09-29

DescribeOrganization PASS: organization management account identified (ending 1268).
DescribePolicy BLOCKED: current member role cannot read <REDACTED_SCP_ID>. Only
docflow-dev is configured locally. Need authorized organization administrator
access/policy content before a scoped patch can be prepared. No policy changed.
See docs/runbooks/ses-scp-access.md (repository-relative) for diagnostic commands,
minimal-change constraints and an unsent administrator request. Task remains BLOCKED.


## 2026-09-29 authorized SES verification

PASS: STS identity guard and SES GetEmailIdentity not-found check.
The MCP sandbox did not define documented ClientError; its catch failed after the
API reported NotFoundException. No write occurred in that failed read script.
PASS: one separately executed CreateEmailIdentity after explicit user consent.
VerifiedForSendingStatus=false; verification completion is NOT RUN pending user
link click. No application deployment or test send; mailbox stays outside Git.


## SES verified result - 2026-09-29

PASS: GetEmailIdentity reports SUCCESS and VerifiedForSendingStatus=true after
the approved verification request. Private session config contains sender, reviewer
and exact identity ARN. No test email or deployment. Session approval pending.
