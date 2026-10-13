# ADR-016 - Submission state, idempotency and document fencing

Status: Accepted
Date: 2026-09-16
Task: TASK-013

## Explicit state resolution
TASK-013 owns the deferred PRD/design discrepancy. Submit from DRAFT and resubmit
from NEEDS_INFORMATION persist SUBMITTED, matching Technical Design 8.1/13.8.
RESUBMITTED is an action/event; only the workflow enters PROCESSING afterward.

## Transaction and authorization
Require requester ownership or admin, trusted access-token claims, empty JSON
object and UUID Idempotency-Key. Validate the immutable bound template, ignore
DELETED documents, require every required type, reject any active INVALID
document and any active document not VALID with validationStatus VALID.
Missing, invalid and not-ready return 422 in that precedence. Scan status is not
a malware guarantee. Reviewer-only callers get 403; other owners get 404.

Read Case before paginated consistent document queries. Every reservation, actual
deletion and processor transition increments Case.documentRevision atomically
with its document/audit transaction. Missing field means zero; new Cases set zero.
Document changes preserve Case lifecycle version/timestamps. Tombstone retries
do not increment. Submission checks prior owner/state/version/attempt/revision,
preventing phantom insertions and stale validation. This completes ADR-010/011/013.

Atomically update Case to SUBMITTED (version and attempt +1, GSI2 status/time),
insert audit, PENDING outbox and durable receipt. Preserve physical key formats:
receipt PK IDEMPOTENCY#case-submission, SK EVENT#SHA256(JSON[caseId,actorId,UUID]).
Key scope is Case and principal; stored operation prevents cross-operation reuse
with 409 IDEMPOTENCY_KEY_REUSED. No receipt TTL: old retries cannot submit again
after NEEDS_INFORMATION. Authorization precedes replay. Replay returns original
response without writes even after subsequent state changes. Failed validation
does not consume the key. Conditional races re-read the receipt: same-key winner
replays, otherwise 409. Infrastructure failures remain sanitized 503.

## TASK-014 boundary
TASK-013 accepts submissions; TASK-014 owns the state machine. Persist
workflowStartStatus PENDING, deterministic <=80-character execution name from
Case ID/attempt, and immutable workflowInput with caseId, attempt, bound template,
documentRevision and correlationId. No fake execution ARN. 202 includes
workflowExecutionId null until actual execution exists, clarifying the previously
unspecified example string in Design 13.7/13.8. 202 means accepted, not started.
TASK-014 MUST implement Standard StartExecution, fixed retry input/name,
conditional ARN persistence and recovery of committed PENDING starts after crashes.
The domain outbox broadcasts facts; it does not orchestrate workflows.
No new AWS resources, workflow grants or deployment in this task. Do not deploy
the intermediate phase before TASK-014 completes start/recovery.

## Contracts and verification
CaseSubmitted/CaseResubmitted data includes attempt, caseType, requesterId,
template ID/version and documentRevision, without tokens or document contents.
Extend publisher, schemas, API/JWT/CORS. Command writes are transaction-only
and include its own receipt partition; processor adds CASE revision updates.
No dependency changes. Moto transactions/interleavings/contracts are local
evidence only. Live concurrency/IAM checks are NOT RUN under TASK-021/ADR-007.


## TASK-014 completion
ADR-017 implements the deferred start/recovery boundary. Receipt business status
and attempt still replay unchanged; confirmed same-attempt execution ARN may now
enrich the HTTP response. Historical receipts never receive a newer attempt's ARN.
The foundation enters PROCESSING and ends there until TASK-015 adds review.
