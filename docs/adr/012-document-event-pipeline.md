# ADR-012 - S3 document event routing and processing queue

Status: Accepted
Date: 2026-09-16
Task: TASK-009

## Context

Technical Design sections 10/11 require S3 Object Created facts on the default
EventBridge bus, followed by a standard document-processing queue and processing
DLQ. TASK-009 provides routing; TASK-010 provides the consumer. ADR-007 defers
real AWS acceptance to TASK-021. This implements the approved service topology.

## Decision

- Enable EventBridge on the actual storage module bucket. Dev composition owns
  its single aws_s3_bucket_notification resource and enables it after the pipeline
  module is ready. Future notification changes must extend that same resource.
- Match source aws.s3, detail-type Object Created, exact generated bucket name,
  and object key prefix cases/. Keep the entire AWS EventBridge envelope as the
  SQS message body; no input transformation or custom domain event is introduced.
- Use standard queues named docflow-{env}-document-processing and its -dlq.
  Main retention is 345600 seconds (4 days); DLQ retention 1209600 (14 days);
  long polling is 20 seconds. Both use SSE-SQS and deny insecure transport.
- Main visibility is 360 seconds, six times the planned 60-second processor
  timeout. TASK-010 must preserve that timeout relationship and configure partial
  batch failure reporting. Standard delivery can duplicate and reorder events.
- Main redrive maxReceiveCount is 5. The DLQ redrive allow policy permits only
  this main queue. EventBridge receives only sqs:SendMessage on the main queue,
  conditioned on this exact rule ARN; no broad publishing role is introduced.
- EventBridge target delivery retry is explicitly bounded to 86400 seconds and
  185 attempts. Processing failures use the SQS DLQ, not a target DLQ, as required
  by the existing design. Exhausted/non-retryable target delivery failures can
  lose events before they reach SQS; the processing DLQ does not cover that gap.
- No processor, custom domain bus, alarms, live deployment or redrive action is
  added. TASK-020 owns monitoring; TASK-021 owns real delivery/IAM/retry evidence.
- Moto events/sqs extras and jsonpath-ng are test-only dependencies. Runtime SDK,
  public API, DynamoDB keys and domain event schemas remain unchanged.

## Consequences and handoff

The prefix filter is routing, not document validation. TASK-010 must validate the
raw envelope, key/metadata relationship and source object; preserve DELETED
tombstones conditionally; handle duplicate/version events idempotently; and
return partial batch failures. No business state changes occur in this task.

Deploying only this pipeline without TASK-010 would accumulate messages until
the main retention expires. Consolidated deployment should include the consumer.
Provider mock assertions and Moto routing tests cannot establish AWS delivery,
IAM, encryption enforcement, retry timing, redrive or S3 notification propagation.

## References

- [EventBridge target retry policy](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html)
- [EventBridge resource policies](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html)
