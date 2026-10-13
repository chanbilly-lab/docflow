# Domain event contracts

case-created.schema.json defines the CaseCreated detail envelope (version 1.0)
for source docflow.case. TASK-005 writes this detail into an OUTBOX/PENDING row
in the same transaction as the Case and audit. TASK-011 now implements local outbox publication.

The TASK-011 publisher sets EventBridge Source/DetailType from the outbox
and serializes its detail exactly once, retaining eventId/occurredAt/correlationId/actor.
DynamoDB numeric representations must become JSON numbers. Do not give PENDING rows
a TTL that could erase unprocessed facts. Dispatch/retention belongs to TASK-011.

Local tests validate the serialized detail against Draft 2020-12 JSON Schema.
Real EventBridge delivery is NOT RUN and remains in TASK-021 cloud acceptance.

## S3 transport events (TASK-009)

The document pipeline uses AWS-owned aws.s3 / Object Created on the default bus.
The canonical pattern is infra/modules/document_pipeline/s3-created.json.tftpl.
The exact document bucket and cases/ prefix are required; the full EventBridge
envelope is the SQS body. This is not a domain event or S3 Records notification.
No project JSON Schema changes are needed. TASK-010 validates raw event/object
identity and duplicate handling; TASK-021 verifies live delivery. See ADR-012.

## Document validation events (TASK-010)

DocumentValidated and DocumentValidationFailed share document-validation.schema.json
for their detail envelope (version 1.0, SYSTEM/document-processor actor, source
docflow.document). data includes documentId/documentVersion, validationStatus,
validationErrors and nullable sha256. Event ID and correlation derive from the
source identity hash, not the delivery ID. Terminal state/audit/outbox/completed
claim commit together; no direct publication. TASK-011 must serialize DynamoDB
Decimal numbers as JSON numbers. Pending events have no TTL.

The publisher accepts eight implemented types (CaseCreated, CaseReadyForReview, CaseSubmitted,
CaseResubmitted, CaseWorkflowFailed, DocumentValidated, DocumentValidationFailed, ReviewStarted), verifies envelope/outbox identity and preserves detail
eventId across transport retries. A DISPATCHED row is skipped. EventBridge's response
EventId is transport identity only. Send/mark is at-least-once: subscribers deduplicate
detail.eventId. Future event producers must extend the publisher allowlist and tests.
No outbox TTL; no default-bus fallback. See ADR-014.

## Routed envelope (TASK-012)

| Source | Detail type | Detail schema |
| --- | --- | --- |
| docflow.case | CaseCreated | case-created.schema.json |
| docflow.case | CaseWorkflowFailed | case-workflow-failed.schema.json |
| docflow.case | CaseReadyForReview | case-ready-for-review.schema.json |
| docflow.review | ReviewStarted | review-started.schema.json |
| docflow.case | CaseSubmitted / CaseResubmitted | case-submission.schema.json |
| docflow.document | DocumentValidated | document-validation.schema.json |
| docflow.document | DocumentValidationFailed | document-validation.schema.json |

domain-event.schema.json binds these source/type pairs to their detail schemas and
validation status/error consistency. It describes delivered lowercase EventBridge
source/detail-type/detail; publisher API uses Source/DetailType/string Detail.
AWS-added transport fields are allowed. Tests resolve references offline and check
formats explicitly. No AWS schema discovery/validation service is deployed.

The actual docflow-dev-domain ARN now feeds publisher IAM/environment and enables
Stream configuration. Raw S3 remains on default; no forwarding. Future event work
must update this routing schema, detail schema, publisher allowlist and tests.


TASK-013 submission facts commit atomically with Case/audit/receipt. Their data
contains attempt, caseType, requesterId, bound template ID/version and
documentRevision. Routed schema requires initial attempt 1 or resubmission >=2.
These are acceptance facts, not proof that Step Functions started. TASK-014 owns
workflow start/recovery. Idempotent API replay adds no new fact; publication remains
at least once with stable eventId. Local tests validate all eight producers.

TASK-014 adds docflow.case / CaseWorkflowFailed, with case-workflow-failed.schema.json.
Only sanitized failureCode and attempt enter data. This technical failure is not a
business rejection. The worker commits Case/audit/outbox together; only publisher
sends the fact. No raw exception data, execution input or task token is emitted.


TASK-015 adds CaseReadyForReview atomically with public Task, Case REVIEW_PENDING and
audit after all bound check skeletons exist. SYSTEM actor workflow-create-review-task;
data: taskId, attempt, priority NORMAL, dueAt. No token/execution internals.
Creation retries/refreshes do not emit another ready fact. Publication remains at
least once through the existing outbox publisher; schema validates routed envelopes.


TASK-016 adds docflow.review / ReviewStarted (review-started.schema.json).
USER actor is the assigned reviewer; data is taskId/attempt/reviewerId/startedAt.
Task IN_PROGRESS, Case IN_REVIEW, audit and outbox commit together. Guarded start
replay emits no second fact; transport is still at least once by stable eventId.
Claim/check edits have audit only. No reviewer comment or callback data is published.


TASK-017 adds CaseApproved, CaseRejected and AdditionalInformationRequested under
docflow.case. Each has its own detail schema, SYSTEM workflow-finalize-case actor
and taskId/attempt/decision/reviewerId/decisionReason/requestedItems. Reasons and
structured items are intentional business outcome content; checklist comments and
callback internals are excluded. State/task/audit/outbox commit atomically. Event
ID derives from immutable decisionId; transport remains at least once. Local tests
now cover all eleven producers through the existing custom-bus publisher.


TASK-019 subscribes to CaseReadyForReview and the three requester decision
events on the custom bus. The raw envelope reaches notification SQS; worker checks
it against the committed OUTBOX fact before using business eventId for deduplication.
No new event types or addresses are added to contracts. Rule activation requires
explicit email configuration; there is no default-bus forwarding.
