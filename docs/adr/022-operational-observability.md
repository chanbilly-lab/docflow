# ADR-022 - Safe operational telemetry and bounded pending-work monitoring

Status: Accepted
Date: 2026-09-23
Task: TASK-020

## Decision

Keep the approved CloudWatch/X-Ray stack and all transaction/event boundaries.
Use common.logging for allowlisted JSON stdout and CloudWatch Embedded Metric
Format (EMF). Every record has level, service, message, timestamp and requestId;
safe correlation/Case/task/event IDs appear when available. Invocation context is
reset after every call. Never serialize requests, responses, exception text, JWTs,
email addresses, task tokens, document names/content, S3 keys or signed URLs.
Only the finite service name is a metric dimension. No Case/user/task dimension,
PutMetricData IAM, new SDK or SDK payload instrumentation is added.

HTTP responses retain their correlation header. Submission input preserves its
original correlation through Step Functions; decision events retain the decision
request correlation. Add internal Document.correlationId at upload reservation
and reuse it in processing audits/domain facts. Existing documents without that
field retain the deterministic corr_<processing identity> fallback. Physical keys,
DTOs, API and event schema shapes stay unchanged. This is a causal chain of
request correlations, not one correlation for an entire Case lifetime.

## Metrics and delivery limits

Domain counters are observations of committed facts after publisher dispatch:
CasesCreated; CasesSubmitted (includes resubmission); CasesApproved; CasesRejected;
CasesNeedsInformation; DocumentsProcessed (valid and invalid terminal validation);
DocumentValidationFailures; ReviewTasksCreated; WorkflowFailures (technical Case
failure, distinct from native execution failure). Normal DISPATCHED replay emits
nothing. Concurrent publication, crash gaps and log transport can duplicate or
lose samples. These are operational trends, never exactly-once accounting.

ReviewDurationSeconds measures review task creation to saved decision, emitted
after successful finalization. Duplicate finalization emits nothing; crash before
logging can lose a sample. OutboxPublishFailures, NotificationFailures and
DocumentProcessingFailures count retry attempts, including partial batch failures
that do not increment native Lambda Errors.

A new operations-monitor runs every five minutes, reserved concurrency 1, timeout
60 seconds. It scans the exact table with only six allowed status/time attributes
(no token/document columns), at most 100 pages of 100 evaluated items each.
ReviewTasksPending counts PENDING/CLAIMED/IN_PROGRESS tasks. Pending outbox age is
the maximum createdAt age; pending workflow-start age uses workflowSubmittedAt
(or the legacy updatedAt fallback). Successful empty snapshots emit zero gauges.
Strongly consistent pages are not a transactionally consistent table snapshot.
Partial/error/page-limit results emit no gauges or heartbeat, never false zeros.
MonitorSuccess missing for three five-minute periods alarms. Review scale/scan
read cost before growing beyond the initial small dev workload; a bound violation
requires a separately reviewed indexed approach, not removing safety limits.

The operations module consumes resource identities separately from the central
observability log module to avoid a dependency cycle through workflow logging.
This adds a read-only scheduled worker, log group and narrowly projected Scan IAM.
It adds no business writes, automatic replay, cleanup, event producer, new index
or key format. Central observability now owns 15 log groups.

## Alarms, dashboard and traces

Represent both consumer DLQs (>0 visible), native workflow failed/timed-out/aborted,
per-function Lambda error rate (>5%, minimum 10 invocations per five minutes),
partial retry counters, durable pending ages (outbox >900s, start >300s), heartbeat,
and per-rule EventBridge FailedInvocations (target-delivery failure).
Sparse event/error metrics use notBreaching; age gaps use missing and are guarded
by the heartbeat alarm. Low-volume native Lambda failures below the rate floor
still appear in logs; workflow, retry and heartbeat alarms cover critical paths.

Dashboard shows domain observations, pending work, review duration, DLQs and alarm
states. Existing approved SNS topic ARNs may be supplied as alarm_action_arns;
empty default provides console/dashboard alarms only. No subscriptions, email,
SMS or arbitrary recipient are created. TASK-021 must verify the chosen action
path or explicitly record console-only operation; alarms are not a spend cap.

Enable native active Lambda and Step Functions X-Ray tracing with only required
telemetry/sampling permissions (these actions require wildcard resources).
Workflow execution payload logging stays disabled. No custom payload annotations
or boto3 monkeypatching. HTTP API, S3, Streams and human callback boundaries do not
promise a single continuous trace; safe correlation IDs remain the cross-service
diagnostic link. Actual trace content and delivery are live acceptance checks.

## Controlled recovery

Add IAM-only outbox-publisher operation recoverOutbox with one validated Case ID
and event ID. Read the exact committed row; use the same Publisher conditions,
bus checks and stable eventId; DISPATCHED is a no-op. No public route or broad
replay is added. Operator invocation is scoped to the publisher function and must
follow approved cloud-session authorization. Existing pending-start recovery
continues unchanged. Diagnose/fix before bounded SQS DLQ redrive. See runbook.

Local implementation only. All cloud metrics/alarms/trace extraction, IAM,
delivery, schedules and recovery remain NOT RUN / TASK-021 under ADR-007.

## References

- [CloudWatch EMF specification](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)
- [Native Lambda X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)
- [Step Functions X-Ray](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html)

- [EventBridge metric dimensions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-monitoring.html)
- [DynamoDB projected Scan](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_Scan.html)
