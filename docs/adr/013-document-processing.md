# ADR-013 - Leased document validation and atomic completion

Status: Accepted
Date: 2026-09-16
Task: TASK-010

## Decision

Implement Technical Design 8.4 with the existing S3/EventBridge/SQS topology.
The Lambda consumes the full raw AWS envelope, validates source/type/exact bucket
and generated key shape, and binds the key/version to reserved Document metadata.
S3 HEAD and streamed GET use quoted If-Match; version-id is passed when present.
Event size/ETag must match HEAD. No client filename becomes an object key.

Validate declared size against HEAD and decimal MIME limits, MIME equality,
filename extension (case-insensitive .pdf/.jpg/.jpeg/.png), required metadata,
and PDF/JPEG/PNG leading signatures. Stream in 64 KiB chunks with a hard size bound
and SHA-256. This is basic content consistency, not full-format parsing or malware
scanning; scanStatus remains NOT_IMPLEMENTED. Metadata failures become INVALID;
transport, malformed event, missing reservation and identity failures retry.

### Durable ownership and crash recovery

Preserve PK IDEMPOTENCY#document-processor and SK EVENT#{identity}. Identity is
SHA-256 of JSON [bucket, key, version-id-or-etag]. Conditional transaction inserts
IN_PROGRESS with random owner and 120-second lease; an expired lease can be replaced.
A live IN_PROGRESS record means retry, never successful duplicate acknowledgement.
Only COMPLETED is acknowledged. This clarifies the shorthand in Design 6.9:
acknowledging an unfinished claim would lose work after a crash.

Persist UPLOADING -> UPLOADED -> VALIDATING with an audit for each transition.
Each transaction checks lease ownership/time and exact prior status/version/updatedAt.
A retry resumes from the persisted stage without repeated intermediate audits.
Final Document VALID/INVALID, system audit, deterministic event outbox and claim
COMPLETED are one transaction. Lost lease or concurrent deletion rolls everything
back. No direct EventBridge publication. Terminal DELETED is acknowledged without
S3 reads or resurrection. Conflicting source identities retry for diagnosis.

Completed claims have a 30-day expiresAtEpoch; unfinished leases have no TTL.
Document processingIdentity and terminal state remain durable duplicate guards
after completed TTL removal. Pending outbox records have no TTL. Event ID is
evt_{identity}; source docflow.document and detail conform to
docs/events/document-validation.schema.json. Valid/invalid produce
DocumentValidated/DocumentValidationFailed respectively.

### Invocation and security

Use existing packaged SDK and cases.zip, adding document_processor sources.
Separate execution role has exact-queue receive/delete/get-attributes, prefix-only
S3 GetObject/GetObjectVersion, scoped base-table GetItem and transaction-only
PutItem/ConditionCheckItem for CASE#* and IDEMPOTENCY#document-processor.
No S3 write/delete/list or EventBridge permission. Reuse centralized log ownership.
Lambda timeout 60 seconds, existing SQS visibility 360, lease 120; batch 5 with
ReportBatchItemFailures and no batching delay. Each failed record reports its
SQS messageId; successful records are not retried. Payloads/exceptions are not logged.

## Verification and limits

Local integration executes actual SDK transactions, S3 reads, partial-batch code
and Moto SQS redrive after five receives. Zero visibility is a local test shortcut,
not deployment configuration. No local result establishes AWS IAM, real timing,
Lambda poller acknowledgement or delivery. TASK-021 owns those live checks;
TASK-020 adds diagnostics/alarms. TASK-011 publishes pending outbox facts.
No public API/key changes, cloud deployment or cleanup authorized.

References:
- [AWS partial batch responses](https://docs.aws.amazon.com/lambda/latest/dg/example_serverless_SQS_Lambda_batch_item_failures_section.html)
- [S3 EventBridge envelope](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html)

TASK-013/ADR-016 completes submission coordination: document mutations atomically
increment Case.documentRevision with their existing audit; Case lifecycle version
remains unchanged. Submission conditions on that revision to fence stale reads.
