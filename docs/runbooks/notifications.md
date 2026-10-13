# Notification operations

Local-only implementation: TASK-019 / ADR-021. Real AWS acceptance is TASK-021.

## Configuration for an approved session

notification_email_config is null by default: rules disabled and no sending worker.
After the concrete deployment/cost/cleanup plan is approved, provide sender,
reviewer and exact existing SES identity_arn in the dev environment configuration.
The sender must be permitted by that identity in the deployed region. SES sandbox
recipients must be eligible/verified; check this before enabling. No account upgrade,
identity verification request, email send or deployment is authorized by this file.
Keep real addresses/environment-specific values outside tracked examples.

Ready notifications go to the approved reviewer mailbox. Decision recipients are
looked up from Case requesterId by Cognito sub; exactly one enabled user with
email_verified=true is required. Do not put addresses into domain event payloads
or edit business state to repair email delivery.

## Failure and recovery

Inspect notification queue/DLQ and safe consumer/event/Case/correlation identifiers.
A failed record returns ReportBatchItemFailures; other records can complete.
After five receives it moves to the 14-day DLQ. Main retention is four days;
visibility 360 seconds, worker timeout 60 seconds, lease 120 seconds.
An active lease is not a completed notification. Let it expire before takeover.

Fix the cause (SES verification/sandbox/quota, recipient availability, IAM, storage
outage or malformed/uncommitted event) before authorized targeted redrive. Preserve
the business eventId. Do not delete COMPLETED receipts or change eventId merely
to resend; retain them without TTL. No automatic redrive is implemented.
SES failure does not roll back Case status. MessageId proves SES acceptance only.

An SES acceptance followed by a crash/lost response or failed receipt update can
cause another email on retry. This is an explicit at-least-once boundary, not a
second business decision. Check completion status and sanitized service evidence;
do not promise exact-once email. Tokens, message bodies and addresses stay out of logs.

EventBridge target-delivery failure is separate from SQS consumer DLQ. Rules retry
for 24 hours/185 attempts; no target DLQ is configured. TASK-020 provides operational
alarms/diagnostics; TASK-021 exercises both paths with approved disposable fixtures.

Local checks: backend pytest tests/integration/test_notifications.py, and Terraform
provider-mocked tests in infra/environments/dev/tests/notifications.tftest.hcl.
All real AWS checks remain NOT RUN until the approved cloud acceptance session.


## TASK-020 observability

Safe common JSON logs and NotificationFailures EMF count retry attempts, including
partial batches. Notification DLQ and retry alarms are represented; native tracing
is enabled on the configured sender. A missing sender configuration still omits
the worker. EventBridge target exhaustion is diagnosed separately with per-rule
FailedInvocations. See [operations](operations.md) for bounded redrive and alarm
actions (empty SNS configuration is console-only). Real delivery remains TASK-021.
