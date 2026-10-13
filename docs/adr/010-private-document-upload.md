# ADR-010: Private direct document upload

**Status:** Accepted
**Date:** 2026-09-16

## Context

TASK-007 implements Technical Design sections 7, 8.3 and 13.5 under the local-first
plan. The upload URL cannot safely exist without the initial Document metadata,
bound-template validation and audit required by that design. These prerequisites
are implemented now; TASK-008 extends metadata/delete behavior, not initial issuance.

## Decision

- Add document_api.command.handler for POST /api/v1/cases/{caseId}/documents/upload-url.
  Trust only Gateway access-token claims, then require requester ownership or admin.
  Reviewers cannot upload even when assigned. Preserve inaccessible-Case 404 behavior.
- Accept metadata only: documentType/fileName/fileSize/mimeType. Reject unknown
  fields, including client keys/IDs/bytes. Limit encoded request body to 8192
  characters, filename to 255 non-control characters with nonblank content, and
  positive integer fileSize. Initial system config allows PDF up to 15,000,000
  bytes and JPEG/PNG up to 10,000,000 bytes (decimal MB).
- Resolve the Case's immutable historical template, not the newest active version.
  Initial requiredDocuments is the allowed type set. No optional type model is added.
- Generate d_/a_ UUIDs and preserve PK CASE#{caseId}, SK DOC#{documentId}, and
  cases/{caseId}/documents/{documentId}/v1/source. Filename is metadata only.
- Before signing, use one transaction: ConditionCheck Case status/version/owner
  still match the strongly consistent read; conditional Document and audit inserts.
  Only DRAFT/NEEDS_INFORMATION may reserve uploads. Conditional failure returns 409
  and leaves no partial Document/audit. No Case lifecycle transition is introduced.
- Initial Document is UPLOADING/PENDING/NOT_IMPLEMENTED, documentVersion 1.
  Audit action DOCUMENT_UPLOAD_REQUESTED records actor/resource/state/correlation.
  No upload-reservation business event is defined, so no new event/outbox is invented;
  processing/validation events remain TASK-010/011.
- Return a 600-second SigV4 PUT capability only after persistence. Sign exact
  Content-Type, Content-Length and If-None-Match: *. The response includes MIME and
  conditional headers; browser File/Blob upload supplies Content-Length automatically.
  No data is uploaded by the signing Lambda; client bytes go directly to S3.
- If signing fails after commit, return sanitized 503 and leave auditable UPLOADING
  metadata. No URL is stored/logged. Retries reserve new document IDs; no HTTP
  deduplication, URL refresh or automatic orphan deletion is promised.
- Implement storage module: generated unique suffix after docflow-dev-documents-
  (logical design bucket name retained as prefix), all four public-access blocks,
  BucketOwnerEnforced, explicit SSE-S3, TLS-only policy, create-only upload policy,
  and maximum signature age 600000 ms. force_destroy remains false.
  No blanket object-expiry lifecycle or automatic cleanup is added.
- CORS allows exact configured browser origins and PUT with the signed headers.
  Dev defaults to localhost/127.0.0.1:5173. HTTP API permits authenticated metadata
  requests from those same origins. CORS is not the authorization boundary.
- Separate document Lambda IAM: base-table GetItem/Query; Case-partition PutItem and
  ConditionCheckItem only within TransactWriteItems; S3 PutObject only under the
  generated v1/source prefix. No object read/delete/list, bucket admin or EventBridge.
  Reuse the pre-created document log group. The existing deterministic cases.zip
  now also contains document_api; all SDK dependencies remain unchanged.
- EventBridge bucket notifications/pipeline belong to TASK-009, content validation
  to TASK-010, and delete/replacement lifecycle to TASK-008. This task neither
  deploys AWS nor adds a frontend business UI.

## Limits and follow-up

Expiry is an upper bound; temporary signer credentials can expire earlier. The
presigned URL is a bearer capability: protecting it is mandatory. A later Case state
change does not instantly revoke an already issued URL. Conditional PUT prevents
overwriting an existing source; initial uploads can still arrive within the validity
window. TASK-010/013 must coordinate upload state and submission validation and
must not treat declared MIME or metadata reservation as content validation.
Case version is checked, not incremented by reservation; submission must account
for newly reserved UPLOADING documents, including concurrent reservations.

Content-Type is not proof of file content. Processing remains absent and documents
remain UPLOADING until that pipeline exists. TASK-008 owns soft-delete lifecycle;
abandoned reservations and failed-signing recovery need explicit retention decisions
before automated cleanup. No malware scanning is claimed.

Moto tests and provider-mocked plans cover local semantics only. TASK-021 must
verify actual expiry, header/length tampering rejection, conditional replay rejection,
privacy/encryption/TLS, exact-origin browser CORS, IAM, transactional races and direct
HTTP uploads with disposable bytes. No local test substitutes for these checks.

References:
- [AWS presigned URL limits](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)
- [AWS conditional write enforcement](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes-enforce.html)
- [DynamoDB transaction IAM](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis-iam.html)

ADR-011 extends the document handler with soft deletion and transactional UpdateItem;
upload issuance and storage constraints above remain in force.

TASK-013/ADR-016 completes submission coordination: document mutations atomically
increment Case.documentRevision with their existing audit; Case lifecycle version
remains unchanged. Submission conditions on that revision to fence stale reads.
