# PROJECT_STATUS.md — DocFlow Current State

## PRIVACY-PUBLISH-01 — 2026-10-14

State: IN_PROGRESS. Static source, all-history and remote-surface review complete;
redacted public candidate prepared. No application code or cloud state changed.
Publication is pending the owner's selection of private-history backup and clean
public repository strategy. TASK-021 BLOCKED and TASK-022 DONE remain; do not
infer cloud acceptance or production readiness. See docs/PRIVACY_REVIEW.md.

> Privacy note (2026-10-14): private account/resource identifiers and personal home paths have been redacted for the public-release candidate. Historical outcomes are unchanged; placeholders are not live targets.

## TASK-022 illustrated bilingual reference supplement - 2026-09-29

DONE: Chinese and English reference guides plus self-contained HTML editions and
six actual local-demo screenshots. Purpose, roles, feature matrix, walkthrough,
architecture, local commands and evidence limits match portfolio/source records.
No frontend/backend integration or cloud deployment added. Browser capture of claim,
checklist, approval and information-request transitions PASS; both HTML editions
load all six embedded images, have eight sections and no desktop/mobile overflow;
Markdown reference/image links and whitespace checks PASS. Full runtime suites
NOT RUN (documentation/images only). TASK-021 remains BLOCKED by owner skip;
TASK-022 remains DONE. No next Project 1 implementation task is defined.
Prior cleanup documentation is included to keep current cloud claims accurate;
all unrelated unfinished implementation files remain outside this publication.

## Authorized state cleanup completed; SYSTEM deletion blocked - 2026-09-29

Owner explicitly revoked retention of the state bucket/all versions and two
SYSTEM backups. DeleteObjects PASS for 47 versions plus 12 delete markers;
DeleteBucket PASS for <REDACTED_STATE_BUCKET>. Follow-up
ListBuckets returns zero buckets; ListTables returns zero tables.
DeleteBackup attempted separately for both exact authorized backup ARNs: BLOCKED
by DynamoDB ValidationException, which disallows manual SYSTEM backup deletion.
Both remain AVAILABLE and automatically expire on 2026-11-03 at 03:00:10.067 UTC
and 06:17:19.113 UTC. Official DynamoDB pricing confirms these SYSTEM backups are
retained at no additional cost. Do not retry deletion or restore them as a workaround.
SES identity and shared service role remain unchanged. No project closure or plan
change. Support/Marketplace, Savings Plans and FSx visibility gaps remain; no
zero-bill claim. TASK-022 DONE and TASK-021 BLOCKED remain unchanged. See current
retirement evidence; all prior retention/pending-approval notes below are historical.

## Renewed paid-resource cleanup request - 2026-09-29 07:27 UTC

Owner requested clearing all paid AWS content again. Read-only re-inventory of
project <REDACTED_AWS_ACCOUNT> in ap-southeast-2 confirms the state bucket still contains
47 versions and 12 delete markers; ListBackups with BackupType=ALL returns the
two SYSTEM backups (the default ListBackups call does not show them).
Because the owner previously explicitly retained these items, a precise question
to supersede retention is pending. No deletion, closure or subscription change
has occurred in this renewed attempt. Account-specific billing/credit details are withheld for privacy; no account-plan change occurred.
Checked application/compute/network/global resources remain absent; FSx and
Savings Plans reads are denied by SCP <REDACTED_SCP_ID>. Browser control failed to start,
so Support/Marketplace subscriptions and organization-wide billing remain
unverified. See docs/verification/AWS-RETIREMENT.md. TASK-022 remains DONE;
TASK-021 remains BLOCKED. Cleanup is incomplete pending retention clarification
and subscription visibility; do not claim zero future charges.

## Current owner-directed retirement and TASK-022 - 2026-09-29

Phase 10. TASK-022 DONE (documentation); TASK-021 BLOCKED (owner elected to skip remaining
acceptance), not DONE. ADR-029 waives TASK-022's dependency gate only. No new cloud
deployment or email. Local code/evidence preserved; older resume plans are inactive.
Portfolio docs cover architecture, design trade-offs, security, costs, local demo,
operations and Project 2 roadmap, with explicit partial-evidence boundaries.
AWS paid plan cannot downgrade to free. After automatic approval review rejected
retained-item deletion, the user explicitly chose to retain state/history, backups,
SES and shared role and complete TASK-022 only. No deletion occurred; do not retry.
Support status unconfirmed (user has not checked). See docs/verification/AWS-RETIREMENT.md.
Last completed task: TASK-022. No next implementation task is defined for Project 1;
Project 2 is a proposal only. No cleanup is pending authorization: retention is
the final choice. Support subscription visibility remains unresolved. Link/format checks PASS; no code
changed this turn. Publication result is recorded in the final handoff.
The dated sections below are historical where they conflict with this direction.

## Latest duration-scope amendment and fast supplement - 2026-09-29

User decision: retain local work; do not deploy the proposed follow-up session.
Session task021-20260929c is prepared only, not authorized or started. Do not
automatically retry deployment or re-request approval without renewed user intent.
No AWS writes or emails performed in response; previous application cleanup stands.

Phase 10; TASK-021 BLOCKED pending new short-session approval and remaining
non-omitted live evidence. Last completed TASK-020; next TASK-021 then TASK-022.
User authorized omission of long waits (ADR-028/DEC-033): actual >24-hour Streams
expiry, 14-day callback timeout/closure and literal 85-day aging stay NOT RUN but
no longer block DONE. Production behavior/local boundary tests remain unchanged.
Prepared cloud_fast_e2e.py and real-browser helper for signed-header tampering,
both configured CORS origins, denied origin, immutable/concurrent template seed,
role denials and no-op/denied-write side effects. Previous five-journey session
and clean teardown remain valid. No new AWS writes/deployment/email this turn.
See docs/runbooks/fast-cloud-acceptance.md and docs/verification/TASK-021-FAST.md
for exact scope/check results. New private config names task021-20260929c;
proposed scope is 45-60 minutes, maximum 120 with cleanup from minute 60.
Handoff: retain local results until the user resumes cloud acceptance; then review
fresh identity/state/plan and scoped approval before executing the supplement;
record remaining clause evidence individually; do not claim IAM/fault checks passed
from static inspection. No completion commit/push until all non-omitted criteria pass.
Latest verification PASS: full scripts/dev.py check (574 backend tests, frontend
checks/build, Python package build, Ruff and strict mypy); 64 targeted operator
tests; real Edge/local fake-service CORS positive/negative probes; Node syntax;
read-only AWS identity/quota/SES checks and Git diff/private-file exclusions.
Earlier duration-related blockers below are superseded by ADR-028.

## Latest completed low-quota session - 2026-09-29

TASK-021 BLOCKED by remaining full acceptance; Phase 10; last completed TASK-020,
next TASK-021 then TASK-022. Authorized session task021-20260929b began 05:42:44 UTC;
deployment, five live journeys/seven harness checks and cleanup PASS by 06:20 UTC
(about 37 minutes). All 189 application resources and 19 fixture objects removed;
remote state empty and independent service inventories PASS. Twelve notification
COMPLETED receipts; inbox delivery unconfirmed. Low-quota mode used 13 unreserved
Lambdas; quota 10 no longer blocks this mode. No application resources left running.
Retained original state bucket, SES identity, shared API Gateway role and AWS
SYSTEM backups expiring November 3. Costs not measured; retained state may incur
storage charges. Latest local preparation: 54 operator tests, 42 dev Terraform
mocks, lint/format/type/validate PASS. See docs/verification/TASK-021-20260929b-session.md.
Handoff: prepare only remaining browser CORS/IAM/fault/retention/alarm and long-duration
criteria from CLOUD_ACCEPTANCE.md, excluding ADR-028 omissions; new live approval required.
No completion commit/push; TASK-022 TODO. All older conflicting notes below are historical.

## Latest concurrency-10 continuation - 2026-09-29

Phase 10; TASK-021 BLOCKED pending new-session approval/live acceptance; last
completed TASK-020, next TASK-021 then TASK-022. User requests testing without
quota increase. ADR-027 adds opt-in low-quota mode: monitor shares unreserved
capacity; default reservation 1 unchanged. Low mode requires available quota 10,
not 101. Local verification: 54 operator tests, lint/type/format and Terraform
validation/mock checks. See verification/TASK-021-LOW-QUOTA.md for final results.
No live deployment/email/cleanup this turn. Concrete short-session scope in
runbooks/short-cloud-acceptance.md under docs. Pending quota request is retained
but need not block this mode. Earlier quota-wait handoffs describe normal mode.

## Latest quota submission and full local verification - 2026-09-29

Phase 10; TASK-021 BLOCKED; last completed TASK-020; next TASK-021 then TASK-022.
User explicitly approved Lambda quota request only. Submitted regional concurrency
10 -> 1000 for project <REDACTED_AWS_ACCOUNT>/ap-southeast-2 after confirming no existing
requests. Request 67f8f7f522db429088c4d6029ac575cc5kM3zDV3 is CASE_OPENED;
AWS case <REDACTED_SUPPORT_CASE>. Actual total/unreserved remains 10/10. No repeat request,
paid capacity, deployment or email authorized/performed. Earlier notes saying
quota authorization is missing are superseded by this entry.
Full local checks PASS: 560 backend tests, 6 frontend tests, lint/format/type/build,
acceptance helper syntax, Terraform fmt/validate and dev 41/bootstrap 1 mocked tests.
Published commit e405067 GitHub CI PASS; this does not verify unpublished tooling.
Handoff: read back this existing request and actual Lambda quota on continuation;
do not submit a duplicate. After effective capacity is sufficient, prepare the
reviewable next-session plan and obtain deployment/test/cleanup approval.
Real cloud journeys and long-duration criteria remain NOT RUN. No completion push.

## Latest state-reuse continuation - 2026-09-29

Phase 10; TASK-021 BLOCKED; last completed TASK-020; next TASK-021 then TASK-022.
Implemented retained-state-bucket reuse (ADR-026) with original-session provenance,
expected owner, selected region, versioning/public-block/encryption checks.
Preserved state key/locking and fresh-plan prior-resource rejection; no migration
or bootstrap of reused storage. 50 operator tests, Ruff lint/format and strict
mypy PASS. Real reuse and E2E NOT RUN. No AWS writes or completion publication.
Remaining blockers: quota request authorization/resolution, explicit next-session
deployment approval and real acceptance (including unresolved long-duration rows).
Handoff: use state_bootstrap_session as described in the short-session runbook;
the previous note saying reuse is unimplemented is superseded.

## Latest cost/time continuation - 2026-09-29

Phase 10; TASK-021 BLOCKED; last completed TASK-020; next TASK-021 then TASK-022.
Prepared target 90-minute / maximum 120-minute session; cleanup starts by minute
60. No deployment, quota mutation, email or paid feature enabled this turn.
AWS read checks PASS: account-specific billing/credit details withheld for privacy; Lambda total/unreserved 10/10,
zero functions; Service Quotas marks L-B99A9384 adjustable. New capacity guard
blocks fresh plan/apply before creation; cleanup is unaffected. 41 operator tests,
project Ruff lint/format and strict mypy PASS. See runbooks/short-cloud-acceptance.md
under docs. Quota resolution, reviewed state reuse and new-session approval remain
required. Long-duration evidence NOT RUN; no completion commit/push.

## Frontend publication update - 2026-09-29

User-authorized frontend implementation and owner-private online preview are
complete. Current phase remains Phase 10; TASK-021 remains BLOCKED by Lambda
concurrency prerequisites and unfinished live acceptance. Last completed task is
TASK-020; next is TASK-021, then TASK-022. No AWS resources were deployed here.
Frontend format, lint, six tests, type/build and desktop/mobile checks PASS.
Preview: <PRIVATE_PREVIEW_URL_OMITTED>
See frontend/PUBLISHING.md and docs/verification/TASK-021-FRONTEND.md.
Handoff: publish frontend changes separately from earlier unfinished cloud work;
reuse the existing Site project ID for future preview updates.

**Last Updated:** 2026-09-29
**Project:** DocFlow
**Current Phase:** Phase 10 — CI/CD hardening + full E2E preparation
**Current Task:** TASK-022 - Portfolio documentation (DONE); AWS residual items retained by user
**Last Completed Task:** TASK-022 - Portfolio documentation under ADR-029
**Next Task:** None scheduled; TASK-021 skipped by owner, no AWS cleanup authorized
**Blockers:** Short-session five-journey subset PASS; remaining browser CORS,
IAM/fault-injection and alarm evidence NOT RUN. ADR-028 omits long-duration evidence.
Latest session cleaned all 189 application resources; independent inventories PASS.
Profile docflow-toolkit, selected region ap-southeast-2; SES identity verified.
State bucket and SES identity retained as approved. AWS-generated empty SYSTEM backup
expires 2026-11-03. Shared AWSServiceRoleForAPIGateway deletion was rejected by automatic
approval review as outside session application-cleanup scope; user explicitly chose to retain this shared role.
See docs/verification/TASK-021-20260929b-session.md for authoritative current evidence.
Earlier dated notes below are historical and superseded where they conflict.

**Local frontend (2026-09-29):** User-requested Traditional Chinese review workspace
implemented and locally verified: search/filter, case/detail/checklist/activity,
guarded demo review decisions, create draft, template/help and JSON export.
Six frontend tests, lint/format/type/build and desktop/mobile Edge interactions PASS.
Loopback preview: http://127.0.0.1:5173/. All state is synthetic/in-memory; no AWS
API integration or live acceptance claim. See docs/verification/TASK-021-FRONTEND.md.


## Completed

- TASK-001 repository, Python 3.13 / React TypeScript tooling, baseline CI.
- TASK-002 dev database/observability, locked AWS provider, mock Terraform tests.
- TASK-002 published as c21aec415acf484eb5e646993bd9a537de3da91b.
- TASK-003 local implementation: Cognito pool/client/groups, HTTP JWT route,
  log-only Lambda, health handler, OpenAPI, tests and deterministic packaging.
  Local acceptance is DONE under ADR-007. Live acceptance is NOT RUN, owned by TASK-021.

- TASK-003 published as 06308bf21191289b6692393eade954f5aa4e5251.
- TASK-004 locally DONE: immutable template repository, atomic audited seed, numeric
  active lookup, historical reads and loopback-only CLI; see ADR-008.

- TASK-004 published as dc84c8372528dec97994103b7cef4a17dd7cbcf1.
- TASK-005 locally DONE: four Case API handlers, atomic Case/audit/outbox, scoped
  queries, public projections, Terraform wiring and bundled SDK; see ADR-009.

- TASK-005 published as ddcd66f2c1c9da3a81c62302113f63a04c014ade.
- TASK-006 locally DONE: 49 added authorization regression cases; production
  behavior unchanged. Requester/reviewer/admin matrix and adversarial inputs PASS.

- TASK-006 published as 826516ffafb1869bd16e926a223689d65170b156.
- TASK-007 locally DONE: private S3, upload route, audited initial metadata and
  conditional 600-second SigV4 PUT; no deployment. See ADR-010.

- TASK-007 published as ba677121b9073d7ef6819d2fe9b467b04337d388.
- TASK-008 locally DONE: audited soft deletion, guarded retries, tombstone filtering,
  preserved metadata/source history and new-ID replacement. See ADR-011.

- TASK-008 published as 80df2f2a16f373d9f054c9c9689f24260d3a118f.
- TASK-009 locally DONE: default-bus exact-bucket/prefix routing, raw SQS envelope,
  encrypted standard queue/DLQ and scoped redrive/publishing. See ADR-012.

- TASK-009 published as fb23b1a566e7af2635cfca66b5aa086738b2fe46.
- TASK-010 locally DONE: leased validation, audited stages, atomic pending document
  event/completion and local retry/DLQ coverage. See ADR-013.

- TASK-010 published as 1abf10a2e32becb8056600ddba3828a0e2c622e6.
- TASK-011 locally DONE: filtered Streams publisher, stable-ID at-least-once delivery,
  conditional dispatch and missing-bus guard. See ADR-014.

- TASK-011 published as ac19d940053924ecf77186d16a9ccee297167029.
- TASK-012 locally DONE: custom bus/actual ARN, enabled stream configuration,
  routed envelope and producer-to-bus isolation. See ADR-015.

- TASK-012 published as 04a9970eba30e82bb586c308a751254b2c54063d.
- TASK-013 locally DONE: submit/resubmit validation, durable UUID receipts, atomic
  Case/audit/outbox and documentRevision fencing. See ADR-016. Standard start/recovery
  remains TASK-014; live cloud evidence remains TASK-021.

- TASK-013 published as 5b0fb997356d24bc84cc495a6f71f0ea23a63159.
- TASK-014 locally DONE: Standard start/conditional ARN, fixed-input retries,
  Stream/HTTP/operator recovery, defensive PROCESSING validation and transactional
  WORKFLOW_FAILED audit/event. Foundation boundary extended by TASK-015.

- TASK-014 published as b99f307124276f709955094dd29d8500880f9dc3.
- TASK-015 locally DONE: retry-safe review/checklist creation, atomic public
  Task/REVIEW_PENDING/audit/outbox, trusted callback token refresh and reviewer/admin
  available/mine/detail queries. ADR-018; live callback acceptance remains TASK-021.

- TASK-015 published as aac44a16d4c4e5a3e84fdfa714b8561a31d7c9c2.
- TASK-016 locally DONE: atomic claim/start/check APIs, assigned-only authorization,
  GSI transitions, audit/ReviewStarted outbox, check versions/task checkRevision,
  guarded no-op retries and scoped command IAM. ADR-019; no AWS deployment.

- TASK-016 published as a0aa638bdec82ad1ded80e12111489e5c76a56b9.
- TASK-017 locally DONE: first-winner immutable decisions, persisted callback replay,
  three guarded finalizers, outcome audit/outbox and technical task closure.
  ADR-020; no AWS deployment.

- TASK-017 published as c165c83b079c9000ed2c309b06ca84f0c95cb29e.
- TASK-018 locally DONE: replacement/addition journeys reach second-review APPROVED
  through production handlers, preserving previous history and rejecting stale work.
  Test/documentation only; no production code, infrastructure or contract changes.

- TASK-019 locally DONE and published as 7e2d897468a7cc3f3bb675665c8efbe7e7b71fba.
- TASK-020 locally DONE: safe JSON/correlation/EMF, native X-Ray, bounded read-only
  status monitor, alarms/dashboard and controlled recovery runbook. ADR-022/DEC-026.

## Environment and verification

- AWS CLI 2.36.44: <USER_HOME>/AppData/Local/Programs/Amazon/AWSCLIV2/aws.exe.
- Profile docflow-dev, us-east-1, JSON; STS caller identity PASS on 2026-09-15.
- Account plan query PASS: account-specific billing/credit details withheld for privacy. No account-plan changes made.
- First real session 2026-09-29: state bootstrap PASS; application apply FAIL;
  exact 187-resource application cleanup PASS. Live journeys NOT RUN.
- Terraform 1.14.9, AWS provider 6.64.0; local state remains ignored.
- Python 3.13.15; ignored Node 22.23.2; backend virtual environment available.
- Application check PASS: lint/format/mypy, frontend test/type/build and backend build.
- TASK-020 full check PASS: 510 backend tests, Ruff lint/format, mypy (76 files),
  frontend formatting/lint/test (1)/TypeScript/Vite, Python sdist/wheel.
- Boto3 1.43.94 runtime; Moto 5.2.3 and stubs are development-only; no dependencies added.
- Terraform readonly init/fmt/validate PASS; 40 provider-mocked plan tests PASS.
- TASK-020 deterministic ZIP/isolated worker imports/size limits PASS.
- Live AWS notification delivery, SES, IAM and authenticated HTTP checks NOT RUN;
  deferred to TASK-021. No deployment or email was sent.
- Hosted CI NOT RUN; local checks do not establish its result.
- TASK-021 preparation PASS: 531 backend tests, Ruff lint/format, mypy (73 + 8
  files), frontend formatting/lint/test (1)/TypeScript/Vite, Python sdist/wheel.
- TASK-021 Terraform fmt/readonly init/validate PASS; dev 40 and bootstrap 1
  provider-mocked tests PASS. SRP helper npm ci and syntax check PASS.
- Prepared guarded operator deploy/E2E/evidence/cleanup tools and remote state
  bootstrap. All actual cloud checks and hosted CI NOT RUN.
- Current evidence and exact changed files: docs/verification/TASK-021.md.

## Architecture and decisions

Project 1 remains serverless-first and AI-free. Step Functions orchestrates Cases;
EventBridge broadcasts domain facts via transactional outbox. Keep DynamoDB key
formats, idempotency, audit requirements, backend authorization and private tokens.
No containers/RAG/Bedrock additions before their phase. See DECISIONS and ADRs 001–006.

Dev composes database, observability, auth, api, lambda, storage, document_pipeline, domain_events, workflow, notifications and operations. Central log ownership
remains unchanged (15 groups). Health and Case GET routes reuse case-query-handler with read-only table/index IAM.
The Case command handler has transaction-only Case and own submission-receipt writes (ADRs 009/016).
Document command adds transaction-only PutItem/ConditionCheckItem/UpdateItem and prefix-scoped
S3 PutObject (ADRs 010/011); it has no read/delete/list object permission.

## Handoff / next steps

1. TASK-021 local preparation is verified. Read docs/runbooks/cloud-acceptance.md
   and cloud-scenarios.md. Resolve the SES organization policy deny, then verify
   existing SES sender/recipients; obtain explicit session approval before writes.
   Proposed initial four-hour session is only a subset. Real >24h Streams expiry
   and production 14-day timeout need separately approved evidence windows.
   No AWS writes yet; no completion commit/push while IN_PROGRESS.
2. Track real-service acceptance as NOT RUN in docs/CLOUD_ACCEPTANCE.md under TASK-021.
   Do not claim local doubles establish IAM, delivery, concurrency or JWT verification.
3. TASK-021 prepares scripts and a concrete resource/cost/session/cleanup plan first.
   Obtain explicit cloud authorization before deployment; generic task prompts and
   GitHub publication do not grant it. Approved sessions should be short-lived.
4. Complete live E2E and approved cleanup before TASK-021 DONE and TASK-022.
5. Build ZIP first: py -3.13 scripts/package_health.py; use infra/README.md commands.
   Application checks: py -3.13 scripts/dev.py check.
6. Automatically commit/push locally DONE tasks under AGENTS 7.1; no AWS deployment
   on push. Keep deferred cloud checks explicit in each verification record.

TASK-021 prepares protected S3 remote application state and private local bootstrap
state under ADR-023. No state bucket has been created. Existing managed local state
requires separately reviewed migration; the fresh-session tool refuses it.
PRD/design resubmission discrepancy is resolved explicitly by TASK-013/ADR-016:
both operations persist SUBMITTED; the workflow subsequently enters PROCESSING. Existing Case ownership checks passed TASK-006; extend them for each new API.

Managed shell initialization has failed previously; approved escalated commands are
used. Git uses a per-command safe.directory setting without global configuration changes.

TASK-005 binds resolve_active(case_type) ID/version on create; preserve that behavior.
Use get_version for historical behavior; never reseed by overwriting old definitions.
Design section 25 now agrees with ADR-007/023: all ordinary workflows perform
checks only; operator deployment requires explicit session authorization.

Build Case ZIP with backend/.venv/Scripts/python.exe scripts/package_cases.py before
Terraform checks. Runtime dependencies are pinned in backend/requirements-runtime.txt.
CaseCreated and document events are published by the TASK-011 implementation; dev
TASK-012 connects the actual custom bus ARN and enables stream configuration. No AWS publication occurred.

TASK-007 reserves UPLOADING metadata and audit before URL issuance. TASK-008 adds
terminal DELETED metadata and audit; repeat deletion is an authorized mutable-state no-op.
Keep filename metadata-only, immutable-template validation and Case condition checks.
Signing failure leaves an auditable reservation; no retry deduplication is promised.
TASK-009 routing, TASK-010 validation and TASK-011 outbox publication are implemented locally.
Issued URLs remain usable for an initial upload within expiry after a state change;
content guards are implemented in TASK-010; submission coordination was completed in TASK-013. See ADR-010 for concurrency.
Browser origins default to local port 5173; configure approved origins in TASK-021.
Live claims/IAM/CORS/expiry/signature checks remain TASK-021.


TASK-010 ignores DELETED documents and conditionally prevents late/duplicate
processing from resurrecting them; local deletion-race regression passes.
Soft deletion retains S3 source bytes and history. No physical cleanup/TTL/revocation
was added or authorized. Replacement always uses a new documentId/key (ADR-011).

TASK-010 consumes the full AWS EventBridge envelope. Main visibility is 360 seconds
for the implemented 60-second consumer with partial batch failures. Main retention
is 4 days, DLQ 14 days, maxReceiveCount 5. No EventBridge target DLQ exists; target
delivery exhaustion is separate from SQS processing failures. See ADR-012.

TASK-011 publishes both CaseCreated and document validation contracts locally,
serializes integral DynamoDB numbers and preserves event IDs. Completed
worker claims expire after 30 days; unfinished claims and pending outbox have no TTL.
Processor hashes bounded streams and checks signatures; no malware scan is claimed.

TASK-012 uses the actual domain bus ARN in dev/outbox.tf and enables the mapping
in configuration; domain/S3 default separation is verified locally. No default-bus fallback. Publisher ListStreams needs Resource
*; stream data reads and EventBridge actions remain exact-resource scoped.
A crash after accepted PutEvents can resend the same business eventId. Downstream
consumers deduplicate it. Stream retention is 24 hours; durable PENDING recovery and
alarms belong to TASK-020/021. No automatic replay or outbox TTL was introduced.

TASK-013 synchronizes SUBMITTED semantics and extends publisher SOURCES plus detail/
routed schemas for CaseSubmitted/CaseResubmitted. Domain notification subscribers remain
TASK-019; no acceptance claim implies an active consumer or AWS deployment.

TASK-014 local verification PASS. StartExecution uses the stored deterministic name
and canonical input, reconciles closed execution identity, and conditionally records
the actual ARN without overwriting worker business updates. CASE/PENDING stream
retries and authorized HTTP replays recover starts; after stream expiry use targeted
IAM-only recoverWorkflowStart invocation. See docs/runbooks/workflow-recovery.md.
Pending starts older than 85 days fail closed for operator investigation. No TTL.
HTTP receipt replays retain status/attempt and may enrich a confirmed same-attempt
ARN; historical attempts never receive a newer execution ARN.

Workflow validation rechecks state/input/template/documents and fences revision/
version before PROCESSING audit. Technical failure writes WORKFLOW_FAILED plus
audit/CaseWorkflowFailed, never REJECTED. Failure persistence outage requires retry.
TASK-015 replaces FoundationComplete with CreateReviewTaskAndWait and persists
REVIEW_PENDING. TASK-017 replaces the intermediate callback terminal with decisions.
Human-review callback/finalization is implemented locally; live AWS acceptance is NOT RUN.

TASK-017 local verification PASS on 2026-09-20: 471 backend tests, full app
lint/format/types/frontend/build; previously verified 34 mocked Terraform plans,
readonly init/fmt/validate and deterministic isolated ZIP checks PASS.
Cloud/hosted CI NOT RUN. Automatic GitHub publication follows local completion.

TASK-018 local E2E PASS: replacement and additive upload preserve old review
Task/CHECK/audit history and S3 source bytes. Missing/pending documents block resubmit;
processing duplicates do not change documentRevision. Old submit/decision replays
and delayed first-attempt finalizer/failure/create workers cannot alter attempt 2.
Distinct execution/task/token and fresh NOT_REVIEWED checks lead to APPROVED.

TASK-019 locally DONE: four committed domain facts route to notification SQS;
leased permanent event receipts suppress completed/concurrent duplicates. SES
failure cannot change Case/audit/outbox business records. Review-ready uses the
configured reviewer mailbox; decisions resolve an enabled Cognito subject's verified
email. ADR-021/DEC-025 cover these boundaries and the SES acceptance/retry gap.
The existing notification log group is reused. Email configuration defaults to null:
rules disabled, no sender Lambda/mapping until approved configuration is supplied.
TASK-020 local verification PASS on 2026-09-23: 510 backend tests, full application
format/lint/types/frontend test/build and Python build; 40 mocked Terraform tests,
readonly init/fmt/validate and deterministic isolated ZIP imports.
Common logging emits only allowlisted safe fields and service-dimension EMF.
Domain counters are approximate dispatch observations; monitor gauges are bounded
read-only snapshots. Missing monitor heartbeat alarms rather than publishing zeros
on scan failure. Default SNS actions are empty: console/dashboard-only alarms.
Native Lambda/Standard tracing is enabled in configuration; no payload SDK tracing.

TASK-021 handoff: preserve all cloud checks in docs/CLOUD_ACCEPTANCE.md. Prepare
concrete scripts and costs for the new monitoring scan/log/metric/trace resources
alongside all application resources. Validate exact projected IAM, EMF extraction,
safe traces, pending work and heartbeat, both DLQs, per-rule target-delivery failures,
workflow/Lambda alarms, dashboard, chosen alarm actions and controlled recovery.
RecoverOutbox is IAM-only, one exact committed fact; it cannot repair downstream
target loss once DISPATCHED. Never bulk reset receipts or fabricate event IDs.
See docs/runbooks/operations.md. TASK-021 cannot become DONE on local checks alone;
explicitly authorized live acceptance and cleanup must pass before TASK-022.


## TASK-021 SCP remediation diagnosis - 2026-09-29

DescribeOrganization PASS: organization management account identified (ending 1268).
DescribePolicy BLOCKED: current member role cannot read <REDACTED_SCP_ID>. Only
docflow-dev is configured locally. Need authorized organization administrator
access/policy content before a scoped patch can be prepared. No policy changed.
See docs/runbooks/ses-scp-access.md (repository-relative) for diagnostic commands,
minimal-change constraints and an unsent administrator request. Task remains BLOCKED.


## Agent Toolkit setup - 2026-09-29

2026-09-29 Toolkit setup: AWS CLI 2.37.5 and uv 0.12.20 installed.
docflow-toolkit login/STS PASS, selected region ap-southeast-2; existing docflow-dev
region left unchanged. Official configure agent-toolkit PASS, 24 default skills
installed, catalog lists 110 skills, aws-mcp profile bound and original Codex config
preserved. New-experience rules appended to AGENTS.md without replacing the contract.
SES GetAccount/ListEmailIdentities PASS in ap-southeast-2: sending enabled,
production access false (sandbox), zero identities. No SCP changes, email or
deployment performed. MCP availability in a restarted Codex session is NOT RUN.

TASK-021 next: reconcile us-east-1-only deployment tooling/design with the selected
region, then obtain approved SES test identities and cloud session authorization.
Prior administrator-SCP-edit advice is superseded; no such edit is needed for
the two now-successful SES reads. TASK-022 remains TODO.


## Historical handoff - region correction

ADR-024 supersedes historical us-east-1 deployment instructions and SCP-edit
advice above. Tools now guard docflow-toolkit/ap-southeast-2. User prefers MEDIUM
guidance and supplied a test mailbox in ignored config. Do not send without
consent. No cloud deployment or cleanup has run. See verification/TASK-021.md.


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
Next action awaits explicit approval of the four-hour deployment/test/cleanup
subset in docs/runbooks/cloud-acceptance.md; no such approval yet.


## Current handoff - first cloud session closed (2026-09-29)

Application teardown finished and service inventory was checked by 03:03:39 UTC,
well before 06:35:07 UTC deadline. No fixtures/users/Case workflows created.
29 operator unit tests, Ruff lint/format and focused mypy PASS. Fixed failure-log
retention and partial-apply protection-unlock targets; production code unchanged.
Retain private plans/state/ownership inventory under ignored build/task-021.
Do not retry the old deploy plan or silently change monitor concurrency semantics.
Resolve quota/configuration with a concrete reviewed plan before a new deployment.
User explicitly chose to retain AWSServiceRoleForAPIGateway; no further role deletion is pending.
TASK-021 BLOCKED; TASK-022 TODO. No completion commit or push.


## Latest continuation - frontend design

User explicitly requested a frontend page while continuing TASK-021. The former
placeholder is now a responsive local review workspace using the existing React/
TypeScript/Vite stack, without new dependencies. Desktop 1440px and mobile 390px
screenshots inspected; 320px overflow check, mobile detail focus and rejection
validation PASS. Full cloud task remains BLOCKED; TASK-022 stays TODO.
Local preview server uses 127.0.0.1:5173. Reload resets demo data; no real PDFs,
login, API requests or notifications. No completion commit/push because TASK-021
acceptance remains incomplete. Existing earlier task changes were preserved.
