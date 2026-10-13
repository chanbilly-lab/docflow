# ADR-020 - Persisted review decisions and guarded finalization

Status: Accepted
Date: 2026-09-17
Task: TASK-017

## Context and scope

The approved design requires an assigned reviewer decision, persisted pending
callback, then workflow finalization. Existing tasks use NULL decision, while an
older design race example assumes absence. The auth matrix allowed admin decisions
without ownership, conflicting with section 8.8's task-owned rule. This task resolves
both: absent or NULL means undecided; admins must also be the assigned reviewer.
No DynamoDB key, service choice or dependency changes.

## Decision

POST /api/v1/reviews/{taskId}/decision requires a UUID Idempotency-Key. Its scope
is the immutable task and assigned subject; store canonical payload hash/key on
the task. Same key/body replays, another key or changed body returns 409 once
accepted. All required checks must be PASS, FAIL or NOT_APPLICABLE; optional checks
may remain NOT_REVIEWED. Validate against the Case's immutable template version,
requiring its complete skeleton, and fence the transaction with the task
checkRevision read before checklist queries. Also fence owner, status, decision
and Case status/version/attempt. Concurrent valid decisions yield one winner.

REJECT and REQUEST_INFORMATION require nonblank reasons up to 2000 characters.
Request-information requires 1-50 unique bound-template document types, reasonCode
and nonblank message. Body limit remains 16 KiB. Extra fields are rejected.
APPROVE has no reason/items. Failed checks count as completed; this API does not
automatically replace human judgment with a business approval rule.

One transaction stores the immutable decision, actor, correlation, callbackOutput,
COMPLETED task/GSI1, callbackStatus=PENDING and REVIEW_DECIDED audit. Findings are
then immutable. Case remains IN_REVIEW until the trusted finalizer. Callback output
contains decision, decisionReason, requestedItems, taskId and internal decisionId.
Task tokens never enter public requests/responses, audit, domain events or logs.

SendTaskSuccess uses only the persisted backend token/output. Successful delivery
is acknowledged with a guarded DELIVERED update plus audit. 202 means callback
delivery confirmed, not finalization complete. Failure/uncertainty returns sanitized
503 CALLBACK_PENDING; repeat the same key/body to deliver the saved decision.
There is no background callback scheduler in this task. The caller must retain
the key and body until acknowledged; pending state has no TTL.

InvalidToken, TaskDoesNotExist and TaskTimedOut do not prove delivery: the token
may be expired or closed. A finalizer invoked by the workflow with the exact
original execution/input and stored callbackOutput proves delivery, allowing it to
atomically set DELIVERED too. This reconciles accepted-send/lost-response or failed
acknowledgement. Pending COMPLETED tasks may receive a newer callback generation
through workflow creation retry, without changing the saved decision. Completed
DELIVERED/finalized/failed tasks cannot have their token refreshed.

DecisionChoice selects three finalizer states. Each invokes the same worker with
original execution input/id and reviewDecision, with bounded retries and a technical
failure Catch. The worker matches execution, attempt, task and exact persisted
decision; one transaction updates Case APPROVED/REJECTED/NEEDS_INFORMATION, decision
metadata/requestedInformation/version/GSI2, task finalizedAt/DELIVERED, audit and
CaseApproved/CaseRejected/AdditionalInformationRequested outbox. Duplicate invocation
creates no additional business fact. Only the existing publisher sends events.

Workflow failure atomically closes the current task with workflowFailedAt and
COMPLETED, preserves existing decision/findings, marks undelivered callback FAILED,
and audits task closure with the Case WORKFLOW_FAILED/audit/outbox. Delivered stays
DELIVERED. Failed tasks leave queues but authorized history is retained. No business
rejection is fabricated. Races fail conditionally and retry from current state.

## IAM and deployment boundary

Only review-command-handler receives states:SendTaskSuccess. AWS does not support
resource-level ARNs for this action, so Resource "*" is required; no SendTaskFailure,
execution-history reads or workflow start permissions are added. Table Query reads
support bound checklist/template lookup; writes remain CASE-scoped transactions.
The state role invokes exactly four workers, including the finalizer. Finalizer
writes use existing workflow transaction-only permissions. Logs exclude payloads.

Sources: [AWS service authorization](https://docs.aws.amazon.com/service-authorization/latest/reference/list_stepfunctions.html)
and [SendTaskSuccess API](https://docs.aws.amazon.com/step-functions/latest/apireference/API_SendTaskSuccess.html).
Local Terraform source only; no IAM policy is deployed. TASK-021 must verify real
callback/JWT/IAM/races and cleanup after explicit deployment approval under ADR-007.

TASK-018 owns complete request-information, replacement/resubmission/new-review E2E.
