# docs/DECISIONS.md — DocFlow Decision Log

## DEC-035 — Separate private history from public source

Status: Accepted and implemented by the owner's explicit approval. Date: 2026-10-14.
Background: the owner requested privacy repairs before public source release;
original metadata contains a private email and source documents contain actual
operational identifiers. A HEAD-only edit would leave old information reachable.
Decision: preserve the original repository privately and archive it read-only;
publish a reviewed latest snapshot with clean history at the original name.
Implemented as public DocFlow ID 1418914087 and private archive ID 1366248864.
Original checkout/mirror remotes point to the archive; public work uses the clean
D:/Projects/docflow-public checkout and noreply commit identity.
Reason: no force-push/data loss or public legacy objects. Alternative: rewrite
all refs, which the contract forbids without specific approval and may leave
cached original objects. Impact: clean public source root, private backup and
explicit checkout/remotes handoff; no API, AWS, runtime or production behavior
change. See PRIVACY_REVIEW.md.

## DEC-034 - AWS retirement and portfolio documentation exception

Accepted 2026-09-29, ADR-029. User explicitly requested skipping TASK-021, clearing
AWS deployments/paid resources and proceeding to TASK-022. TASK-021 remains BLOCKED
with owner-skip reason; waive only TASK-022's dependency gate. Preserve partial
evidence and outstanding limitations. Paid-to-free downgrade is unavailable;
cleanup results/approval blockers are recorded separately. No new deployments.

## DEC-033 - Omit user-approved long elapsed-time acceptance

Accepted 2026-09-29, ADR-028. User permits omitting long tests such as 24-hour
Streams expiry and 14-day production callback timeout. These stay NOT RUN with
explicit duration-omission reason and no longer block completion. Production
semantics and local boundary tests remain; all non-omitted cloud criteria and
approved cleanup remain required. No new deployment authorized by this decision.

## DEC-032 - Explicit concurrency-10 acceptance mode

Accepted implementation at the user's request, 2026-09-29; ADR-027. Default
monitor reservation remains 1. Opt-in low-quota mode shares unreserved capacity,
preserves read-only bounds/alarms and requires 10 available executions. Sequential
synthetic journeys do not prove load capacity or default monitor isolation.
Separate new-session deployment/email/cleanup approval remains required.

## DEC-031 - Retained state reuse across acceptance sessions

Accepted local implementation, 2026-09-29; ADR-026. Optional original bootstrap
session selects only the exact retained bucket, with owner/provenance/protection
checks. Same state key and lock; fresh application plans still reject managed
prior state. Avoid additional retained buckets without adopting or migrating
existing resources. Actual reuse requires next-session approval and live evidence.

## DEC-030 - Shorter, cost-conscious acceptance preparation

Accepted planning scope, 2026-09-29, at the user's request. Target 90 minutes,
maximum proposed window 120 minutes, cleanup starts by minute 60; no optional
paid features or unattended retention. Keep architecture and all final criteria.
Conservative read-only Lambda headroom check before fresh plan/apply uses the
published 100 unreserved floor plus monitor reservation 1. Observed managed-project
floor was 10; the guard deliberately avoids assuming that floor after quota changes.
No implicit quota increase or deployment authority; no production concurrency
change. See runbooks/short-cloud-acceptance.md for exact scope and limitations.

## DEC-029 - Private frontend design preview

Status: Accepted. Date: 2026-09-29. See ADR-025.
Keep source in the existing private GitHub repository and host only the synthetic
frontend as an owner-private Site. GitHub Pages is unavailable on the current
private-repository plan. No visibility/plan change or AWS production architecture
change. Preview publication is separate from TASK-021 cloud acceptance.

Use this as the concise decision index. Use `docs/adr/*` for full architecture records.

---

## DEC-001 — Project 1 is serverless-first
**Status:** Accepted  
**Date:** 2026-09-09

Use CloudFront, S3, Cognito, API Gateway, Lambda, DynamoDB, EventBridge, SQS, Step Functions, SES, CloudWatch/X-Ray, and Terraform for the MVP.

Do not add EKS, ECS, Aurora, OpenSearch, or Bedrock to Project 1 without a new decision.

---

## DEC-002 — Step Functions orchestrates; EventBridge broadcasts
**Status:** Accepted  
**Date:** 2026-09-09

Step Functions owns deterministic Case workflow. EventBridge distributes facts to independent subscribers.

---

## DEC-003 — DynamoDB single-table design
**Status:** Accepted  
**Date:** 2026-09-09

Use the PK/SK/GSI access model defined in `TECHNICAL_DESIGN.md`.

---

## DEC-004 — Transactional Outbox for domain events
**Status:** Accepted  
**Date:** 2026-09-11

Write business state + audit + outbox in one DynamoDB transaction where an event is required. DynamoDB Streams drives the publisher to the custom EventBridge domain bus.

---

## DEC-005 — Human review uses Step Functions callback
**Status:** Accepted  
**Date:** 2026-09-09

Use Step Functions Standard with callback/task-token waiting. Task tokens remain backend-only.

---

## DEC-006 — AI/Codex uses persistent task-driven workflow
**Status:** Accepted  
**Date:** 2026-09-11

Every coding session follows `AGENTS.md`.

Normal user prompt:

```text
执行 TASK-XXX。
```

Every task updates task/status/changelog and any affected technical documents.

---

## DEC-007 — PROJECT_STATUS is a handoff cache
**Status:** Accepted  
**Date:** 2026-09-11

`PROJECT_STATUS.md` summarizes current implementation state for session recovery. It must not redefine durable architecture; durable truth remains in PRD, Technical Design, API/event contracts, Decisions, and ADRs.

---

## DEC-008 - TASK-001 local tooling baseline
**Status:** Accepted
**Date:** 2026-09-11

Use Python 3.13 with setuptools packaging, Ruff formatting/lint, strict mypy and pytest.
Use React/TypeScript with Vite, Vitest, ESLint and Prettier on Node 22.12+ (22.x).
Pin resolved development dependencies in backend/requirements-dev.txt and frontend/package-lock.json.
Use scripts/dev.py as the cross-platform root command entry point, with a backend-local
virtual environment. Baseline GitHub Actions runs these same commands without AWS credentials.

These are implementation tooling choices within TASK-001, not changes to AWS architecture,
domain behavior or deployment strategy. No additional architectural ADR is needed.

The user explicitly authorized deferring the PRD/Technical Design resubmission-state
discrepancy to TASK-013 while completing TASK-001. This records task scope only;
it does not approve either business-state interpretation.

---

## DEC-009 - TASK-002 Terraform dev foundation
**Status:** Accepted
**Date:** 2026-09-12

Use the existing database/observability modules for the dev foundation. Terraform 1.14.x
(verified/CI 1.14.9), AWS provider >=6.64.0, <7.0.0 with a committed 6.64.0 lockfile,
and an environment-local backend establish the initial single-operator baseline.
Remote bootstrap/migration must precede shared or automated deployment (TASK-021 at the
latest). See ADR-005 for state handling and consequences.

Retain all section 6 key formats; use GSI1/GSI2 ALL projections, on-demand billing,
expiresAtEpoch TTL, NEW_AND_OLD_IMAGES Streams, PITR and deletion protection by default.
Use default AWS-owned encryption and 14-day finite dev log retention. Pre-create the
12 section 8 Lambda plus API/workflow log groups in observability. No cloud deployment,
IAM boundary or business-state change occurs. Credential-free Terraform checks join PR CI.

---

## DEC-010 - TASK-003 authenticated health boundary
**Status:** Accepted
**Date:** 2026-09-15

Use the auth/api/lambda module boundaries for an invite-only Cognito Lite pool,
public SRP client, scoped HTTP JWT route and log-only case-query-handler.
See ADR-006 for token handling, IAM, throttling and deterministic packaging.
Only local implementation/testing is authorized; deployment is deferred by the user.
ADR-007 moves live acceptance to TASK-021 and permits local task completion.

---

## DEC-011 - Local development followed by consolidated cloud acceptance
**Status:** Accepted
**Date:** 2026-09-15

User-directed cost-control plan: implement and test TASK-003 through TASK-020 locally,
then conduct a short, explicitly authorized AWS acceptance session in TASK-021.
Preserve all cloud criteria in docs/CLOUD_ACCEPTANCE.md. Local DONE unblocks local
dependencies and automatic GitHub publication, without claiming cloud success.
TASK-003 is locally DONE, TASK-004 READY. TASK-021 requires real acceptance and approved
cleanup; TASK-022 remains downstream. No production architecture change. See ADR-007.

---

## DEC-012 - Immutable checklist templates and operator seed
**Status:** Accepted
**Date:** 2026-09-16

Preserve section 6.10 keys; resolve the initial case-type mapping by highest numeric
published ACTIVE version using paginated strongly consistent partition queries.
Publish immutable metadata/checks plus a template-scoped audit atomically, with
conditional writes and exact replay comparison. See ADR-008 for limits, fields,
active-version semantics and the no-overwrite rule. Use pinned boto3 runtime and
development-only DynamoDB stubs/Moto for local integration tests. The seed CLI is
preview-first and loopback-only; no cloud writes or new public API are authorized.

---

## DEC-013 - Case API transactions, projections and pagination
**Status:** Accepted
**Date:** 2026-09-16

Implement the four Case routes with atomic Case/audit/outbox creation, stable template
binding, scoped requester/admin index queries and explicit response whitelists.
Preserve all physical keys. ADR-009 defines cursor semantics, consistency/HTTP retry
limits, backend authorization, command/query IAM separation and pinned SDK packaging.
OpenAPI 3.1 and CaseCreated JSON Schema are synchronized. Pending outbox facts have
no TTL; publishing stays in TASK-011. No cloud deployment is authorized.

---

## DEC-014 - Private direct document upload
**Status:** Accepted
**Date:** 2026-09-16

TASK-007 implements metadata-only upload authorization, initial Document/audit
reservation, immutable-template type checks, private S3 and ten-minute SigV4 PUT.
ADR-010 specifies exact size/MIME binding, create-only writes, storage/CORS/IAM,
concurrency and failure boundaries. Existing keys and service choices are preserved.
TASK-008 retains delete/lifecycle work; events/processing remain TASK-009/010.
No AWS deployment is authorized; live expiry/browser/IAM checks remain TASK-021.

---

## DEC-015 - Audited document soft deletion
**Status:** Accepted
**Date:** 2026-09-16

TASK-008 implements terminal DELETED metadata, atomic Case/document guards plus
one audit, authorized retry no-op, public-detail filtering and new-ID replacement.
ADR-011 defines these semantics without changing physical keys or adding S3 deletion.
IAM adds transaction-only UpdateItem; JWT DELETE route and CORS are synchronized.
No new domain event is defined. TASK-010 must preserve tombstones under late events;
TASK-021 owns live concurrency/JWT/CORS/IAM validation. No cloud deployment.

---

## DEC-016 - Document event pipeline and retry boundary
**Status:** Accepted
**Date:** 2026-09-16

TASK-009 implements the approved S3 default-bus rule, raw-envelope standard SQS
queue and processing DLQ. ADR-012 records exact-bucket/prefix filtering, SSE-SQS,
TLS, least-privilege publishing, retention, redrive and single notification ownership.
Target delivery retries and consumer retries remain distinct; no target DLQ is added.
TASK-010 owns idempotent processing; real AWS evidence stays NOT RUN under TASK-021.

---

## DEC-017 - Recoverable document processing and atomic completion
**Status:** Accepted
**Date:** 2026-09-16

ADR-013 implements validation with source-pinned reads, streamed SHA-256, leased
conditional ownership, audited stages and atomic terminal state/audit/outbox/claim.
Only COMPLETED claims acknowledge duplicates; IN_PROGRESS requires retry or expired
lease recovery. Tombstones remain terminal. Processor IAM and partial SQS mapping
are scoped; real retry/DLQ/IAM evidence remains NOT RUN under TASK-021.

---

## DEC-018 - At-least-once outbox stream publication
**Status:** Accepted
**Date:** 2026-09-16

ADR-014 implements conditional dispatch after confirmed EventBridge entry success,
consistent duplicate checks, stable event IDs, numeric serialization and partial
Stream batch checkpoints. Preserve producer transactions and no outbox TTL.
Dev mapping remains disabled until TASK-012 provisions the custom bus and enables
it. Stream expiry recovery is TASK-020/021; no exactly-once or cloud claim is made.

---

## DEC-019 - Dedicated domain bus and routed envelope contract
**Status:** Accepted
**Date:** 2026-09-16

ADR-015 creates the planned custom domain bus, connects its actual ARN to publisher
IAM/environment and enables stream configuration. S3 remains on default. A new
routing-envelope schema binds the three implemented event types to existing detail
schemas; no runtime payload change. Command roles remain publication-free. Local
isolation/contracts are verified; real delivery/IAM remain NOT RUN under TASK-021.

---
## DEC-020 - Atomic submission and explicit resubmit state
**Status:** Accepted
**Date:** 2026-09-16

ADR-016 resolves the task-owned PRD discrepancy to SUBMITTED for both operations.
Bound-template validation, documentRevision fencing and durable scoped UUID
receipts accompany the atomic Case/audit/outbox transaction. Persist pending
workflow intent; TASK-014 owns actual Standard start/recovery. A null execution
ID truthfully indicates no execution yet. Live acceptance remains TASK-021.


---
## DEC-021 - Standard workflow foundation and recoverable initiation
**Status:** Accepted
**Date:** 2026-09-17

ADR-017 implements direct Standard StartExecution with fixed name/input, actual
ARN bookkeeping, closed-execution identity checks, stream/HTTP/operator recovery
and an 85-day fail-closed recovery age. Defensive validation records PROCESSING;
technical failure atomically records WORKFLOW_FAILED/audit/CaseWorkflowFailed,
never REJECTED. FoundationComplete is a task boundary, not business completion.
TASK-015 adds callback review; real AWS acceptance remains TASK-021.


---
## DEC-022 - Callback review publication and authorized queues
**Status:** Accepted
**Date:** 2026-09-17

ADR-018 defines deterministic attempt task IDs, hidden guarded checklist preparation
(up to 98 checks), then atomic Task/Case/audit/CaseReadyForReview publication.
Token generations support audited refresh without resetting findings. The ASL
waits for a trusted callback; timeout records technical failure. Initial dueAt is
submission time +48h, separate from the 14-day callback ceiling.
Available and mine queues use GSI1 with current authorization; reviewer/admin
detail supports pre-claim inspection without widening Case APIs. Public DTOs omit
callback internals. TASK-016/017 implement mutations/decisions; AWS remains TASK-021.


---
## DEC-023 - Assigned review commands and finding concurrency
**Status:** Accepted
**Date:** 2026-09-17

ADR-019 implements atomic claim/start/check transactions. TASK-016's assigned-only
acceptance takes precedence over the broader design Admin=Yes entries for start
and checklist update: admins must first claim their own task. Unassigned accepts
existing explicit NULL or absent reviewerId. This resolves both task-owned
documentation discrepancies without changing keys or bypassing ownership.

Start atomically records IN_PROGRESS/IN_REVIEW/audit/ReviewStarted. Finding updates
use an internal per-check version and task checkRevision with immutable audit.
Same-state retries are guarded no-ops; inactive/stale attempts fail closed.
Public contracts exclude tokens, internal revisions and comment text in events.
TASK-017 must fence decision validation with checkRevision. Cloud remains TASK-021.


---
## DEC-024 - Immutable decisions, persisted callbacks and finalization
**Status:** Accepted
**Date:** 2026-09-17

ADR-020 defines assigned-only decisions (including admin), absent/NULL compatibility,
UUID request replay and checkRevision fencing. Decision/audit/PENDING commit before
SendTaskSuccess. Only stored output is retried; expired/closed tokens are ambiguous.
Trusted matching finalization proves delivery and atomically commits Case outcome,
task metadata, audit and one outbox fact. Technical failure closes the task without
erasing a decision or fabricating rejection. Single-action callback IAM requires
Resource * by AWS design; no deployment is authorized. TASK-018 owns resubmission
E2E; real-service acceptance remains TASK-021.


---
## DEC-025 - Isolated domain notification delivery
**Status:** Accepted
**Date:** 2026-09-21

ADR-021 defines two custom-bus rules for four notification types, encrypted
notification queue/DLQ and a worker with writes limited to its own idempotency
partition. Validate received events against committed outbox facts; ready messages
use a configured reviewer mailbox, decisions resolve an enabled verified Cognito
requester by sub. No event-supplied recipients or business state writes.

EventId/hash, a 120-second lease and permanent COMPLETED receipts suppress normal
duplicates; SES acceptance and receipt persistence are not atomic, so uncertainty
can resend email. SQS retries/partial failure/DLQ do not roll back Case state.
Email configuration defaults null, disabling rules and omitting the sender worker
until an approved existing SES identity and addresses are supplied. No live sends
or cloud writes; TASK-021 owns actual verification and deployment approval.


---
## DEC-026 - Operational telemetry and controlled recovery
**Status:** Accepted
**Date:** 2026-09-23

ADR-022 implements common allowlisted JSON/EMF logs, service-only dimensions,
correlation propagation, native X-Ray, the required operational metrics, alarms
and dashboard. Domain counts are approximate committed-fact observations, not
transactional accounting. A bounded five-minute read-only monitor reports open
review count and durable pending ages; failures emit no false healthy snapshot.
Projected Scan permissions exclude private content/tokens. The operations module
consumes resource identities without creating a cycle through central log ownership.

IAM-only single-fact recoverOutbox reuses the publisher; no automatic replay,
business writes or public endpoint. Existing recovery and SQS redrive remain
operator-controlled. Empty alarm_action_arns means console-only alerts, not a
configured notification channel. Cloud acceptance remains NOT RUN / TASK-021.


---
## DEC-027 - Guarded operator cloud acceptance
**Status:** Accepted (implementation; no cloud execution authorization)
**Date:** 2026-09-28

ADR-023 implements ADR-005/007: protected versioned S3 state with native locking,
account/session and saved-plan hash guards, fresh-only deployment, exact-inventory
cleanup with separate protection updates. CI uses immutable Action revisions and
checks only. Test-only Cognito SRP authentication keeps credentials/tokens in memory.
No production API/event/database semantics change. Live acceptance remains NOT RUN;
short sessions do not waive retention or callback-timeout evidence.


---
## DEC-028 - Managed project's selected region
**Status:** Accepted
**Date:** 2026-09-29

ADR-024 applies the user-confirmed ap-southeast-2 region and docflow-toolkit profile
to TASK-021, including state bootstrap/backend and API/S3/SDK endpoint guards.
Read-only SES works in this region; the prior organization-admin SCP-edit advice
is superseded. No deployment, email, account upgrade or policy change authorized.
