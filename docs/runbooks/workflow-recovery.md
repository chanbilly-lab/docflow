# Workflow start and failure recovery

Owner: TASK-014 implementation; TASK-020 provides local alarm configuration; TASK-021 owns live execution.
All cloud operations below are NOT RUN. Follow the explicit TASK-021 deployment
authorization before any AWS write. GitHub publication is not deployment approval.

## Pending start

1. Inspect the exact Case consistently using an authorized operator identity.
   Record caseId, submissionAttempt, workflowSubmittedAt, workflowStartStatus and
   expected workflowExecutionName. Do not export document contents or credentials.
2. Within 24h, the filtered CASE/PENDING Stream mapping retries failed batches.
   The command re-reads current state and acknowledges the first failed sequence.
   An authorized client's same UUID HTTP retry also tries the same pending start.
3. If Stream history expired, prepare a small JSON file with this shape:

   ```json
   {"operation":"recoverWorkflowStart","caseId":"c_example","attempt":1}
   ```

   Substitute the inspected Case/attempt. This is a direct Lambda invocation, not
   an HTTP API endpoint. The operator requires lambda:InvokeFunction on exactly
   docflow-dev-case-command-handler. After cloud-session authorization, invoke
   using AWS CLI --profile docflow-toolkit --region ap-southeast-2,
   --function-name with that exact function,
   --cli-binary-format raw-in-base64-out and --payload file://<request-file>.
   Store sanitized output locally, inspect FunctionError, and re-read the Case.
   Success is matching attempt/name, STARTED and actual workflowExecutionId.
   HTTP 200 from Lambda Invoke alone does not mean the function succeeded.
4. Never generate a fresh execution name/input to work around a retry. Closed
   executions are reconciled using DescribeExecution identity checks. A mismatch
   fails closed; investigate the configured machine and stored intent.
5. Pending intents older than 85 days intentionally refuse StartExecution. Inspect
   history and audit evidence. Do not edit timestamps or delete receipts to bypass
   the service's 90-day name-reuse window. A separately designed/operator-approved
   recovery is required; no automatic restart of an old attempt is promised.

Starts can succeed before ARN persistence, and validation may already move the Case
to PROCESSING, REVIEW_PENDING or WORKFLOW_FAILED. Recovery must preserve those business states.
Older-attempt replay is ignored and never launches the current attempt implicitly.
Receipt responses can enrich a confirmed same-attempt ARN; they never borrow a
newer attempt's execution ID. Pending receipts/intents have no TTL.

## Workflow technical failure

WORKFLOW_FAILED is a technical state, never REJECTED. Inspect sanitized
workflowFailure.code, audit and the Standard execution history using restricted
operator access. No public response includes callback tokens or raw exception data.
The failure Lambda transaction must commit Case/audit/CaseWorkflowFailed together.

If failure persistence itself exhausted retries, Case may remain SUBMITTED, PROCESSING,
REVIEW_PENDING or IN_REVIEW. After the underlying issue is fixed, a trusted operator can re-invoke
the failure Lambda with the exact original submission and executionArn from the
execution history, under the approved cloud session. It checks current
attempt/input and cannot overwrite newer attempts or terminal business decisions.
Never substitute the latest input for an old execution.

This is not a business retry API. Automatic restart of WORKFLOW_FAILED or a new
submission attempt is outside TASK-014; do not edit Case state as a shortcut.

## Review callback boundary

TASK-015 replaces FoundationComplete with CreateReviewTaskAndWait. The worker
creates REVIEW_PENDING and Standard waits. TASK-017 supplies callback delivery and
decision finalizers before the final Succeed state. See recovery instructions below.
Live Standard behavior, IAM, stream expiry and recovery checks remain TASK-021.


A preparation outage may leave hidden CHECK rows without a task. A trusted workflow
retry resumes identical rows, then atomically publishes task/Case/audit/outbox.
Do not expose, delete, or edit these rows as a recovery shortcut. Tokens stay inside
trusted components: never copy them into tickets, logs, HTTP requests or evidence.
ASL retry provides fresh callback context; generation checks prevent old retries
from overwriting newer tokens. Do not manually fabricate a callback token/generation.
Timeout after 14 days records technical failure without another 14-day retry.
TASK-017 atomically closes the matching task with technical failure metadata and
excludes it from queues while retaining authorized history. 48h dueAt is an operational deadline, not an automatic decision.


## Review commands (TASK-016)

Claim/start/check conflict is a 409: refresh current task/Case before retry.
Another owner cannot be overridden by admin; there is no reassignment shortcut.
Same-owner claim while CLAIMED and start while IN_PROGRESS safely replay their
active result. An identical finding replays without another audit. A concurrent
different finding can return 409; refresh rather than blindly overwrite it.

If a transaction response was lost, inspect the current task/finding using its
authorized query and retry only the intended operation. State/attempt/ownership
guards remain active on no-op retries. No command can reopen WORKFLOW_FAILED,
complete a decision or send a Step Functions callback in TASK-016.
Review comments stay on check rows. Never put comments/tokens in troubleshooting
evidence. checkRevision is internal concurrency metadata for TASK-017 decisions.


## Decision callback and finalization recovery (TASK-017)

Retain the UUID key and request body until 202. On 503 CALLBACK_PENDING, retry the
same authenticated POST decision; never submit a new key or changed decision.
The saved decision is immutable and task may already read COMPLETED while the
Case remains IN_REVIEW. 409 means refresh/investigate; no ownership bypass.

InvalidToken/TaskTimedOut/TaskDoesNotExist cannot distinguish expired from already
accepted callbacks. Do not mark DELIVERED manually. Original workflow finalization
proves delivery and reconciles a lost send response/failed acknowledgement. If the
workflow invokes review creation again, only a newer generation may replace a
pending token. There is no background callback recovery scheduler in this task.

Finalizers retry conditionally and emit one business outcome. On exhausted technical
failure, Case and matching review task close atomically with audit/outbox, keeping
existing decision/findings. Do not turn WORKFLOW_FAILED into REJECTED or reopen it
by editing rows. Failed attempts leave queues; authorized history remains readable.
Never copy tokens, callback output or private evidence into logs/tickets. Diagnose
using Case/task/correlation IDs and sanitized status. Real recovery acceptance
remains NOT RUN / TASK-021.


## Request-information resubmission (TASK-018 local evidence)

Read requestedInformation from authorized Case detail. To replace a file, soft
delete its metadata then request a fresh upload; preserve old bytes and never reuse
the old key. Additional evidence uses another upload reservation of a bound type.
Wait until every active document is VALID before resubmit. A missing/pending file
returns 422 and does not consume the resubmit key. Reuse that same UUID/body after
validation; accepted retries retain attempt 2 rather than start attempt 3.

The new attempt gets its own execution, task and NOT_REVIEWED checklist. Prior
findings remain history; do not copy completed findings into the new task.
Old callback/finalizer/failure events cannot reopen or modify the new attempt.
The two local journeys are in test_resubmission_e2e.py; actual AWS service behavior
and presigned HTTP uploads remain NOT RUN, TASK-021.


## TASK-020 monitoring

Pending-start maximum age >300 seconds, native execution failure/timeout/abort
and committed WorkflowFailures have alarms. Logs now use the original submission
correlation and safe request IDs. Check monitor heartbeat before interpreting an
absent pending-age gauge. See [operations](operations.md) for metrics semantics,
trace limitations, investigation and outbox/DLQ recovery. No automatic replay or
additional workflow write authority is introduced. Live alarms remain TASK-021.
