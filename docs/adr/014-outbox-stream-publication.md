# ADR-014 - DynamoDB Streams outbox publication

Status: Accepted
Date: 2026-09-16
Task: TASK-011

## Decision

Keep existing Case creation and document validation transactions: each already
commits business state, audit and outbox together. Do not introduce a second
write or direct publishing in command handlers. Preserve physical keys and event
schemas. No unrelated producer refactor is needed.

The publisher accepts INSERT/MODIFY NewImage OUTBOX/PENDING records. It consistently
reads the current outbox item, skips DISPATCHED, and checks that committed identity,
source, type and detail agree with the stream image. Current supported types are
CaseCreated, DocumentValidated and DocumentValidationFailed. Extend this allowlist
with contracts as later tasks add event producers; never silently drop unknown facts.

Serialize detail exactly once, retaining business eventId/occurredAt/correlationId
and actor. Convert integral DynamoDB Decimal values to JSON integer; reject
nonintegral/nonfinite/unsupported values instead of rounding. Current schemas use
integers only. Reject oversized detail, invalid envelope identity and default bus.
EventBridge transport EventId is not the business eventId.

Before each single-entry PutEvents, DescribeEventBus must resolve the configured
custom ARN. This guards the documented nonexistent-bus success response. It cannot
eliminate deletion between the check and send; provisioning/operational control must
keep the bus present. Only a zero failed count and one successful EventId entry
permit conditional DISPATCHED/dispatchedAt update. Check status/entity/eventId and
original fact on update. A concurrent equivalent DISPATCHED row is successful;
other conflicts remain retryable. Dispatch bookkeeping is not a new business
transition and emits neither another audit nor another domain event.

## Delivery guarantee

This is at-least-once publication, not exactly once. Normal stale stream replay
after DISPATCHED does not send again. Concurrent senders or a crash after accepted
PutEvents but before status update can publish twice with the same detail.eventId.
Downstream consumers must deduplicate that ID. Never mark sent before sending.
HTTP success alone is insufficient: inspect per-entry success. Failed/malformed
records stay PENDING. No pending or dispatched outbox TTL is introduced.

The handler stops at the first failed stream SequenceNumber and returns
batchItemFailures with that sequence, not stream eventID. Configure
ReportBatchItemFailures, bisect on function error, batch 10, parallelization 1,
TRIM_HORIZON, no batching delay and retry/record-age -1. Lambda retries only while
DynamoDB retains the stream (24 hours). Durable PENDING rows remain after expiry,
but are not automatically rediscovered. TASK-020 must provide pending-age
monitoring and controlled replay; TASK-021 must verify outage/expiry recovery.
There is no new queue or automated replay/cleanup in TASK-011.

## Infrastructure boundary with TASK-012

TASK-011 implements the publisher Lambda, IAM, stream filter and full mapping.
Dev uses the planned docflow-dev-domain ARN with mapping disabled until TASK-012
creates the custom bus, replaces the ARN with its resource output and enables it.
Local tests create a Moto custom bus and execute real SDK calls. Do not deploy this
intermediate phase and leave business writes running without a functioning publisher.
No default-bus fallback. No live AWS writes or deployment were performed.

Publisher IAM grants data-read stream actions on the exact stream; ListStreams
alone requires Resource * because AWS does not support resource-level scope for it.
GetItem/UpdateItem are base-table/CASE-partition scoped; PutEvents/DescribeEventBus
target only the custom bus. No business PutItem/DeleteItem, S3 or command grants.
The role reuses its centralized log group. Success logs include only validated
eventId/caseId/correlationId; failures log a constant marker, never event payloads.
Runtime dependencies are unchanged; cases.zip includes outbox_publisher.

## References

- [PutEvents individual failures and missing-bus behavior](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html)
- [DynamoDB partial batch checkpoint](https://docs.aws.amazon.com/lambda/latest/dg/services-ddb-batchfailurereporting.html)
- [Stream mapping settings and retention](https://docs.aws.amazon.com/lambda/latest/dg/services-ddb-params.html)
- [DynamoDB IAM resource support](https://docs.aws.amazon.com/service-authorization/latest/reference/list_dynamodb.html)

## TASK-012 completion

ADR-015 completes the intermediate boundary above: dev now creates domain_events,
uses its actual ARN and enables mapping in Terraform. Historical TASK-011 tests
retained disabled-state evidence; current tests assert enabled wiring. No live
deployment occurred, and delivery/retention semantics above are unchanged.
