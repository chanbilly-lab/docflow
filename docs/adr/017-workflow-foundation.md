# ADR-017 - Standard workflow foundation and recoverable starts

Status: Accepted
Date: 2026-09-17
Task: TASK-014

Keep ADR-002/007/016. Case command starts Standard directly after submission and
on authorized receipt replay. Same deterministic name and canonical JSON input
are reused. Persist actual execution ARN with an attempt/name/input/PENDING
condition. Never overwrite business state while acknowledging a start.
ExecutionAlreadyExists requires DescribeExecution with matching input/machine/name;
a closed execution is acknowledged, never started under a new name. Fail closed
on mismatches and retry transient failures. Pending intents older than 85 days
require operator investigation, avoiding the service's 90-day name reuse boundary.
Persist workflowSubmittedAt; older TASK-013 intents use their submission updatedAt.

A second DynamoDB Stream consumer invokes case-command for CASE/PENDING intents.
It reads current state rather than trusting stream payload, reports first failed
sequence and skips stale attempts/acknowledged starts. HTTP attempts remain another
recovery path. Stream retention is 24h: an IAM-only recoverWorkflowStart invocation
with explicit caseId/attempt provides durable targeted recovery after stream expiry.
No domain EventBridge subscriber orchestrates the flow; no scheduled infrastructure.
TASK-020 adds pending-age alarms; TASK-021 tests long outages and operator recovery.

HTTP 202 retains original submission status/attempt; workflowExecutionId can be
enriched with the confirmed ARN on same-attempt calls. A later attempt's ARN is
never returned for an older receipt. Start failure returns sanitized 503; the
committed receipt and pending intent remain retryable. This refines ADR-016's
fixed-null phase response without changing idempotent business effects.

Workflow receives immutable submission input plus execution context supplied by
ASL. Validate against stored input, execution name, attempt, template and document
revision. Query all active documents consistently and recheck using an atomic Case
version/revision guard when moving SUBMITTED -> PROCESSING with an audit.
Duplicate validation is a no-op; stale executions never change a newer attempt.
Unexpected service failures propagate into bounded retries then Catch. Invalid
defensive validation also enters failure handling, not business rejection.

Failure handler conditionally changes only the matching SUBMITTED/PROCESSING
attempt to WORKFLOW_FAILED, with sanitized metadata, audit and CaseWorkflowFailed
outbox atomically. Duplicate handling produces no extra audit/event; newer or
terminal business state is protected. No raw exception Cause/document/token logs.
Failed failure-handler persistence leaves the execution failed and needs operator
retry; it is never reported as success.

TASK-014 ASL ends at FoundationComplete after successful validation and PROCESSING.
This explicitly represents only the foundation, not completed review/approval.
TASK-015 replaces this terminal with review creation/callback; TASK-017 adds decisions.
No fake callback task or premature business success. Final deployment waits for
the remaining workflow tasks and TASK-021 approval.

Use existing central workflow/Lambda log groups; payload logging disabled.
State-machine role invokes only validation/failure Lambdas. Workers have
transaction-only CASE writes and read-only template access; no callback permissions.
Case command has exact-machine StartExecution and matching execution DescribeExecution,
CASE-only start bookkeeping plus stream read grants. No new runtime dependencies.

Local tests use Moto persistence and a deterministic Standard-service double plus
botocore Stubber for real request/response shape. A local ASL subset runner executes
the checked-in definition and real workers. These do not prove AWS orchestration;
all live service/IAM/history/recovery verification stays NOT RUN, TASK-021.

References:
- https://docs.aws.amazon.com/step-functions/latest/apireference/API_StartExecution.html
- https://docs.aws.amazon.com/step-functions/latest/apireference/API_DescribeExecution.html
- https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html


## TASK-015 handoff completed
ADR-018 replaces FoundationComplete with CreateReviewTaskAndWait. The worker
publishes REVIEW_PENDING and Standard waits for a trusted callback. Failure
handling also accepts REVIEW_PENDING/IN_REVIEW. ReviewCallbackReceived is an
intermediate terminal pending TASK-017 decision finalizers, not business approval.
