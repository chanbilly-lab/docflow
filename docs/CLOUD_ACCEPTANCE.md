# Consolidated cloud acceptance - TASK-021

## Current owner decision - ADR-029

On 2026-09-29 the owner elected to skip remaining TASK-021 acceptance and retire
AWS resources, then execute TASK-022 documentation. TASK-021 remains BLOCKED;
non-executed clauses stay NOT RUN, and no claim of production readiness follows.
TASK-022's dependency gate is explicitly waived. Earlier instructions to continue
cloud sessions are inactive. Historical PASS evidence below remains valid.

## Current duration-scope amendment - ADR-028

User approved long elapsed-time omissions on 2026-09-29. Actual >24-hour Streams
expiry/recovery, actual 14-day callback timeout/associated closure, and literal
85-day aging are NOT RUN (user-approved duration omission) and do not gate DONE.
Synthetic age/boundary and non-duration recovery checks remain required. Apply
this exception only to those clauses in the original broad rows below; other
NOT RUN clauses remain outstanding. No whole row becomes PASS from this change.
Earlier mandatory long-duration language is superseded. See
[fast follow-up plan](runbooks/fast-cloud-acceptance.md).

## Verified short-session subset - 2026-09-29

Session task021-20260929b, ADR-027 low-quota mode: deployment PASS (189 creates,
13 unreserved Lambdas); production-client SRP and valid/missing/invalid/ID-token
checks PASS; five real approve/reject/replacement/additive/invalid-document
journeys PASS. Twelve persisted notification COMPLETED receipts observed (SES
acceptance, not inbox confirmation). See verification/TASK-021-20260929b-session.md.
Cleanup PASS: 19 fixture objects and all 189 application resources removed;
empty Terraform inventory and independent service inventories verified by 06:20 UTC.
Retained state/SES/shared role and AWS-managed SYSTEM backups are documented there.
These are clause-level observations, not a PASS for every clause in the broad
matrix below. Full fault-injection/IAM/browser/long-duration checks remain NOT RUN.
The first failed-session statement below is historical, not this deployment result.

ADR-027 permits an explicit low-quota acceptance configuration with unreserved
monitor capacity. Evidence must identify the mode; it cannot prove default
reservation isolation or high-load capacity. No live row changes from this
local implementation. See verification/TASK-021-LOW-QUOTA.md.

Latest continuation: quota submission PASS after explicit approval; AWS request
CASE_OPENED and effective Lambda quota still 10. Full local suites PASS; these do
not change the live evidence rows. See verification/TASK-021-QUOTA.md.

2026-09-29 amendment: next short-session proposal targets 90 minutes (maximum
120 including cleanup), per runbooks/short-cloud-acceptance.md. Read-only quota
checks and local guard tests PASS; live matrix remains NOT RUN. No long-duration
criterion is replaced or waived and no new cloud writes are authorized.

This is the deferred live-evidence ledger under ADR-007. First real deployment
failed on 2026-09-29 due to Lambda reserved-concurrency quota; application cleanup PASS.
See verification/TASK-021-20260929-session.md. Broad acceptance rows remain NOT RUN
because none of their complete runtime scenarios passed. Local DONE does not imply cloud PASS.
TASK-021 cannot be DONE until every applicable row passes and approved cleanup is verified.

| Origin | Required real AWS evidence | Result |
| --- | --- | --- |
| TASK-002/003 | Fresh environment created from Terraform; Cognito pool/client/groups, JWT issuer/audience/scopes, valid access token 200, invalid/missing/expired/wrong-issuer/wrong-client tokens rejected; ID token rejected | NOT RUN |
| TASK-004/005/006 | Repeatable atomic seed with exactly one audit, conflicting/concurrent publication, immutable historical versions and highest numeric active selection (ADR-008); actual DynamoDB keys/queries/pagination; requester isolation, reviewer/admin matrix (including cross-Case assignment, assignment removal, combined groups, forged headers/cursor positions and denied-write side effects from TASK-006), Case/audit/outbox rollback, empty filtered-page continuation, least-privilege transaction-only command IAM, no internal data leaks | NOT RUN |
| TASK-007/008 | Private S3 and backend-generated keys; direct raw File/Blob upload with exact browser CORS; ten-minute expiry and early credential expiry; Content-Type/Content-Length/If-None-Match tampering and overwrite rejection; TLS/encryption; transactional owner/state/version races; metadata lifecycle, atomic delete/audit rollback, one-audit concurrent deletion/retry, immutable-state deletion denial (including admins/retries), retained S3 bytes and tombstone filtering | NOT RUN |
| TASK-009/010 | S3 EventBridge notification on actual bucket, default-bus source/type/exact-bucket/cases-prefix filtering (including nonmatches), full envelope delivery, exact-rule queue publishing restriction, SSE-SQS/TLS, retention/visibility and byQueue redrive policy; distinguish target-delivery retry exhaustion from processing DLQ; actual validation and version-pinned reads, bounded streaming/hash, late/deleted-document events cannot resurrect tombstones, leased-claim expiry/takeover and stale-owner rejection, atomic state/audit/outbox/completion rollback, duplicate safety including completed-claim TTL removal, mixed-batch acknowledgement, 60-second timeout/360-second visibility, retries and forced failure after five receives to DLQ | NOT RUN |
| TASK-011/012 | Atomic state/audit/outbox writes, DynamoDB Stream filtering, stable business event IDs across concurrent/accepted-send-failed-mark duplicates, per-entry PutEvents failure handling, missing-bus fail-closed preflight, conditional DISPATCHED marking, Stream SequenceNumber checkpoint/bisection, typed PENDING-only filtering, 24-hour expiry and controlled pending recovery, scoped IAM including ListStreams, and actual resource-ARN wiring/enabled mapping, custom/default bus isolation with no forwarding, all eleven current producer-to-bus envelopes, command-role publish denial, and correct event schemas | NOT RUN |
| TASK-013 | Submit/resubmit validation errors and SUBMITTED transitions; durable Case/principal/UUID replay (including lost responses, later state and cross-operation conflict); same/different-key concurrent submit/resubmit one-winner attempt updates; atomic Case/audit/outbox/receipt rollback; documentRevision fencing for reservations, deletions, processing transitions and paginated reads; exact transaction-only receipt/revision IAM, JWT and Idempotency-Key CORS; pending start recovery handed to TASK-014 | NOT RUN |
| TASK-014 | Standard start from actual command, fixed-name/input replay while running and closed; lost response and accepted-start/failed-ARN-save recovery; CASE/PENDING stream checkpoint/retry; operator recovery beyond 24h and 85-day guard; real defensive validation/version/revision races; WORKFLOW_FAILED/audit/event transaction and failure-handler outage; exact IAM/log payload exclusion | NOT RUN |
| TASK-015 | Actual Standard callback waiting and retry token replacement; 98-check preparation/interruption recovery and one-winner atomic public task/Case/audit/outbox; no token leaks in HTTP/events/logs; reviewer/admin JWT queues/detail, GSI propagation and stale-assignment rechecks, scoped cursor pagination; exact creator/query IAM; technical timeout/failure recovery | NOT RUN |
| TASK-016 | Real simultaneous one-winner claim; claimant JWT binding including admin assignment restriction; same-owner no-op retries; atomic Task/Case/audit/ReviewStarted, GSI1/GSI2 transitions; check version/task checkRevision races and timeout/finalization fencing; no comment/token leaks; PUT CORS and CASE-only transactional IAM | NOT RUN |
| TASK-017 | Assigned decision JWT, first-winner/checkRevision races, persisted same-key callback retry, lost send/ack recovery, ambiguous expired/closed token, pending generation refresh, exact callback IAM, three original-context finalizers and atomic Case/task/audit/outbox, timeout task closure and no token leaks | NOT RUN |
| TASK-018 | Replacement (soft delete + new key) and additive uploads through real presigned HTTP/S3/EventBridge/SQS; missing/pending rejection, duplicate delivery, same-key replay, distinct execution/task/token, fresh checklist, second approval, immutable previous task/check/audit/source history and late prior-attempt worker isolation | NOT RUN |
| TASK-019 | Configured enabled custom-bus rules and raw queue delivery; exact-rule/TLS policies, 5 receives to DLQ; verified SES sender/sandbox recipients, Cognito sub/verified enabled requester lookup, exact IAM with no business writes; concurrent leases/expiry, completed deduplication, uncertain SES acceptance replay and independent Case state; real email acceptance/delivery and approved cleanup | NOT RUN |
| TASK-020 | Real HTTP/upload/workflow/decision correlation, safe JSON and EMF extraction, native X-Ray without private payloads, projected Scan IAM/pagination/zero gauges and heartbeat loss, both DLQ alarms/redrive, workflow failure/timeout/abort, Lambda error rate, partial retries, pending ages, per-rule target failures, dashboard and configured SNS actions (or documented console-only operation), exact-fact outbox recovery after Streams expiry | NOT RUN |
| TASK-021 | Remotely managed state before automation, guarded deployment, full happy/failure E2E, recorded versions/results, approved cleanup and remaining-resource check | NOT RUN |

For each run record timestamp, commit, environment, command/scenario, result, sanitized
evidence path, defects/retests and cleanup outcome in docs/verification/TASK-021.md.
Never store secrets, user documents, tokens or raw state in Git.

## Preparation artifacts (2026-09-28)

Local operator tools and immutable-action CI are prepared under ADR-023. See
[session and cleanup plan](runbooks/cloud-acceptance.md),
[scenario worksheet](runbooks/cloud-scenarios.md) and
[verification record](verification/TASK-021.md). Login/STS and SES read-only preflight PASS in ap-southeast-2 on 2026-09-29.
ADR-024 corrects the old region. SES identity is verified and explicit short-session
approval was received. Bootstrap passed; application apply failed after creating
187 resources. Actual runtime scenarios remain NOT RUN. The initial short session cannot
prove literal 24-hour Streams expiry or the production 14-day callback timeout.
Separate approved windows/decisions are required; no criterion is waived.

## Session sequence

1. Finish TASK-003 through TASK-020 locally, plus TASK-021 test/deployment preparation.
2. Present the exact account/region, resource plan, estimated costs, short session
   duration, test fixtures and teardown/retention scope for explicit user approval.
3. Bootstrap state if needed, deploy and run the matrix with disposable test data.
4. Retain sanitized evidence, then perform only the approved cleanup. Explicitly
   handle DynamoDB/Cognito deletion protection and any S3 contents; do not silently
   remove protection or delete pre-existing data.
5. Inventory surviving resources and expected ongoing charges. Later billing checks
   must account for reporting delay; arrange follow-up only if requested.
6. Mark TASK-021 DONE only after acceptance/cleanup checks pass; then TASK-022 may
   describe the verified system. A permanent online demo needs separate authorization.

A user-authorized earlier short session may test a subset, but does not waive any row.
No deployment or teardown is authorized by this plan alone.
