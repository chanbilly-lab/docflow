# Operations diagnosis and controlled recovery

Owner: TASK-020 local implementation; real execution NOT RUN / TASK-021.
These are preparation instructions, not authorization to deploy, invoke workers,
send email, redrive queues or delete data. Use the approved short-lived session,
profile docflow-toolkit, verified project and ap-southeast-2. Never attach tokens, raw events,
execution payloads, presigned URLs or document contents to tickets/evidence.

## Start with evidence

1. Open docflow-dev-operations. Record alarm name, time range and safe Case/task/
   event/correlation IDs. An empty alarm_action_arns means no external notification.
2. Check monitor-missing before interpreting absent/zero age metrics. It detects a
   missed schedule, failed invocation, scan bound, IAM/EMF/log-delivery problems.
   Snapshot Limit=100 and maximum 100 pages cap evaluated items at 10,000; it is
   read-only, not a cross-page transaction. No partial snapshot is reported healthy.
3. Inspect the relevant log group with this Logs Insights query, substituting only
   a known safe correlation ID:

       fields @timestamp, service, message, correlationId, caseId, taskId, eventId, requestId
       | filter correlationId = "corr_example"
       | sort @timestamp asc
       | limit 100

   Use requestId for invocation errors and the original submission correlation for
   workflow logs. A decision has its own correlation; locate its event/Case link.
   S3 processing uses upload correlation (legacy rows use processing identity).
4. Inspect native Lambda Errors/Invocations, Step Functions execution state and
   X-Ray service metadata under restricted operator access. Do not export history
   inputs: callback tokens can exist in trusted execution history. Native tracing
   is sampled and not continuous across every async boundary.
5. Operational event counters may under/overcount at crash/race/log boundaries.
   Confirm business truth using authorized Case detail, audit and committed outbox.

## Alarm interpretation

- Document/notification DLQ visible count >0: consumer retries exhausted.
- OutboxPublishFailures/NotificationFailures/DocumentProcessingFailures: retry
  attempts, even if Lambda returned a successful partial batch response.
- WorkflowFailures: committed technical Case failure. Native ExecutionsFailed,
  TimedOut or Aborted can also reveal failed failure persistence.
- Lambda error rate: >5% over five minutes with at least 10 invocations. Below that
  floor inspect logs; the retry/workflow/heartbeat alarms remain independent.
- Outbox age >15 minutes or pending-start age >5 minutes: persistent work needs
  investigation before the 24-hour Streams history expires.
- Event-target-failures: per-rule EventBridge FailedInvocations. Custom-bus rules
  include both EventBusName and RuleName; inspect document/notification/schedule rules and
  target policies. Consumer DLQs do not capture target-delivery exhaustion.
- Monitor missing: three five-minute periods without a successful complete snapshot.
  Inspect monitor errors/throttles, schedule, IAM and EMF ingestion; never infer an
  empty queue from missing metrics. Alarm transitions/actions require live testing.

## Durable outbox recovery after stream expiry

1. Inspect the exact Case partition and OUTBOX row consistently. Verify eventId,
   event type, PENDING status, immutable fact and configured custom bus. Fix IAM,
   missing bus, target policy or service failures first. Check downstream duplicates.
2. Prepare an operator-reviewed JSON file with exactly the intended identity:

       {"operation":"recoverOutbox","caseId":"c_example","eventId":"evt_example"}

3. After explicit session/recovery authorization, invoke only
   docflow-dev-outbox-publisher using AWS CLI lambda invoke, --profile docflow-toolkit,
   --region ap-southeast-2, --cli-binary-format raw-in-base64-out and
   --payload file://<reviewed-file>. Operator IAM needs lambda:InvokeFunction on
   that exact ARN; it is not granted to application users. Use a local output file.
4. Check FunctionError as well as returned status, then consistently re-read the
   row and confirm DISPATCHED. HTTP 200 on Invoke alone is not success. Confirm the
   expected downstream effect separately. Already DISPATCHED is an intentional
   no-op; this operation cannot repair an exhausted EventBridge target delivery.
5. Stop on identity/schema errors. Never invent a new eventId, reset status or TTL,
   publish an edited event, edit Case state or bulk replay the table.

Pending workflow starts use the existing
[workflow recovery runbook](workflow-recovery.md) and its exact original attempt/
execution name. An outbox replay never starts a workflow.

## Consumer DLQ recovery

1. Identify the exact source/DLQ pair: docflow-dev-document-processing[-dlq] or
   docflow-dev-notification[-dlq]. Record counts/age and the safe identifiers only.
   Inspect an individual envelope in a restricted environment if necessary; never
   log or paste its content. Preserve malformed evidence securely for investigation.
2. Diagnose underlying IAM/configuration, storage metadata, verified recipient or
   SES availability problems. Notification guidance is in
   [notifications](notifications.md). Fix and verify one safe original message first.
3. Obtain bounded recovery authorization within the approved session. An operator
   performing SQS StartMessageMoveTask needs exact-DLQ start/receive/delete/
   attributes access and SendMessage on the original source queue; list/cancel
   permissions are scoped to that DLQ. No such grants are added to runtime roles.
4. Redrive to the original queue at a small rate (initially one message/second);
   inspect task handle/status using ListMessageMoveTasks, source processing logs
   and business/audit evidence. Cancel the move task if errors recur. Moving a
   message is not proof of successful processing.
5. Do not purge/delete original records, strip envelopes, reset receipts or modify
   document/Case state to force success. Preserve event IDs so existing idempotency
   guards remain effective. SES ambiguous acceptance can still produce a duplicate
   email. A poisoned message that cannot be replayed requires separate resolution.

## Cloud acceptance evidence checklist

TASK-021 must demonstrate projected Scan IAM, zero and nonzero gauges, heartbeat
loss/recovery, real partial-batch metrics, both DLQ alarms/redrive, workflow failure/
timeout alarms, low/high-rate Lambda error behavior, EventBridge target failures,
CloudWatch EMF extraction, safe X-Ray/log content, dashboard and any configured SNS
action. Record actual alarm transitions and downstream outcomes. Preserve evidence
before the explicitly approved resource cleanup. Monitoring itself incurs usage;
no deployment or cost ceiling is implied by local PASS.
