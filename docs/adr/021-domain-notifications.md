# ADR-021 - Isolated notification delivery and recipient resolution

Status: Accepted
Date: 2026-09-21
Task: TASK-019

## Decision

Implement the four approved notification types on the custom domain bus:
CaseReadyForReview to a configured reviewer mailbox; AdditionalInformationRequested,
CaseApproved and CaseRejected to the Case requester's currently verified email.
Two rules preserve the raw EventBridge envelope into a standard notification queue.
Queue visibility is 360 seconds for a 60-second Lambda, batch size 1 with partial
batch failures, retention 4 days, maxReceiveCount 5; DLQ retention 14 days.
Queues use SSE-SQS, TLS-only policies and byQueue redrive permission. Only exact
notification rule ARNs can enqueue through EventBridge. Target retry is 24 hours /
185 attempts. There is no separate EventBridge target DLQ; SQS DLQ handles consumer
exhaustion. TASK-020/021 must diagnose target-delivery failures separately.

Existing Case/outbox facts are authoritative. The worker reads the committed
OUTBOX row, validates its serialized identity and requires exact received detail
and type. It never trusts a recipient supplied in an event. Ready events use the
approved reviewer mailbox (one destination, not a Cognito group fan-out). Decision
events read the immutable Case requesterId and query the configured Cognito pool
by sub, with pagination. Require exactly one enabled matching user, verified email
and valid address; missing/eventually inconsistent/unverified recipients retry.
No user profile store, API or event changes are introduced.

Messages contain only Case ID, attempt, event title and recorded time, instructing
the recipient to sign in. No document text, reviewer comments/reasons, token,
execution ARN or signed links. Delayed messages describe recorded events rather
than assert the current Case status. Structured success logs contain safe event/
Case/correlation IDs; failure logs contain only a constant RETRY status.

## Idempotency and failure semantics

Use stable keys from design 6.9:
PK IDEMPOTENCY#notification-worker, SK EVENT#{business eventId}.
Transport EventBridge IDs and SQS IDs do not affect identity. Persist a canonical
payload hash and IN_PROGRESS owner/120-second lease with a conditional PutItem.
Only COMPLETED is acknowledged as duplicate. Active leases fail/retry; expired
leases can be taken over conditionally with the same hash. Missing/conflicting
facts fail closed and ultimately enter DLQ.

Resolve recipient, send SES, then conditionally store COMPLETED/processedAt/MessageId
under the current owner and unexpired lease. Remove lease; completed receipts have
no TTL, so arbitrarily late replay stays deduplicated. On failure release only the
current owner's unfinished lease when possible; process crash recovers after expiry.
No Case, ReviewTask, Check, audit or outbox item is written by this worker.

SES SendEmail has no client idempotency token or transaction with DynamoDB.
Therefore completed duplicates and ordinary concurrent consumers are suppressed,
but accepted-send/lost-response or failed completion storage may resend an email.
Delivery is at least once, not exactly once. Do not mark COMPLETED before SES
acceptance or silently acknowledge an unfinished lease to hide this limitation.
SDK SES retries are disabled; SQS owns retry. Tests explicitly expose the acceptance
gap. Case state never depends on SES success. SES acceptance is not inbox delivery.

## IAM and activation

A dedicated role can read the table's CASE and notification receipt partitions,
write only its own receipt partition, consume only the notification queue, write
only the existing centralized log group, ListUsers on the exact Cognito pool and
SendEmail on an exact existing SES identity with an exact FromAddress condition.
No business writes, EventBridge publish, Step Functions, S3 or Cognito mutation.

Dev notification_email_config defaults null. Queues/rules/targets are represented,
rules are DISABLED and worker/mapping/IAM absent until a non-null approved
sender/reviewer/existing SES identity configuration is supplied. Configured mock
tests prove the complete enabled topology. No identity is automatically created
or verified; no verification messages, real emails, AWS writes or deployment occur.
TASK-021 must prepare verified sender/recipients (including SES sandbox restrictions)
and the concrete deployment/test/cleanup plan for explicit user authorization.

Sources:
- [SES SendEmail](https://docs.aws.amazon.com/ses/latest/APIReference/API_SendEmail.html)
- [Cognito ListUsers](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ListUsers.html)

No runtime dependencies added. Live service semantics, IAM, real delivery,
concurrency and cleanup remain NOT RUN / TASK-021 under ADR-007.
