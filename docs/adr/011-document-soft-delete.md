# ADR-011: Document metadata lifecycle and soft deletion

**Status:** Accepted
**Date:** 2026-09-16

## Decision

TASK-008 implements Technical Design 8.3/13.6 using the existing document command
Lambda and stable Case/Document keys. Initial metadata creation, filename isolation
and bound-template validation from TASK-007 remain the upload path.

- DELETE /api/v1/cases/{caseId}/documents/{documentId} accepts no body or query.
  Require trusted requester ownership or admin; reviewer-only access is denied.
  Case must be DRAFT or NEEDS_INFORMATION, including for admins and retries.
- Get the document consistently using this Case partition and validated documentId.
  Missing/inaccessible Case returns 404; missing document in an accessible Case
  returns DOCUMENT_NOT_FOUND. Never perform a global document lookup.
- Soft deletion sets status DELETED, deletedAt/deletedBy and updatedAt. Keep
  documentVersion, fileName, MIME, size, original S3 key, creation timestamp and
  validation/scan fields unchanged. DELETED is a terminal metadata tombstone.
- One transaction checks Case status/version/owner, conditionally updates the
  document using its prior status/updatedAt/documentVersion, and inserts one
  DOCUMENT_DELETED audit with actor, resource, previous/new state and correlation.
  No partial deletion/audit is possible. Failed conditions return 409 DOCUMENT_CONFLICT.
- A sequential retry of an existing tombstone returns empty 204 without another
  mutation/audit. It still transactionally checks current Case state/ownership and
  tombstone existence. Racing deletes may produce one 204 and one 409; retrying the
  latter returns 204 if authorization and mutable Case state still hold.
- Initial permitted document states are REGISTERED, UPLOADING, UPLOADED, VALIDATING,
  VALID and INVALID; the Case gate is authoritative. Unknown future states fail
  closed. Processing transitions remain TASK-010, not fabricated by this endpoint.
- Case detail omits DELETED entries for every role. Raw tombstones and audits are
  retained. Replacement means requesting a new upload with a new ID/key; it never
  overwrites or reactivates an old document. Existing documentVersion semantics
  remain unchanged (each newly reserved source starts at v1).
- Add only transaction-bound DynamoDB UpdateItem to document-command IAM, with
  existing Case leading-key restriction. Add scoped JWT DELETE route/invoke
  permission and browser DELETE CORS. Do not add DeleteItem or S3 DeleteObject.
- No DocumentDeleted domain event/consumer is defined in the approved event
  catalog, so this local metadata operation produces audit only. Validation events
  remain TASK-010/011; no new event schema or direct EventBridge publication.
- Physical S3 source deletion is optional in the design and is not implemented.
  Retaining the source preserves history and avoids reusing a still-live create-only
  upload URL after deleting an object. No resource cleanup is authorized here.

## Boundaries and handoff

An issued URL is not revoked by soft deletion. A late first upload can still create
an orphan S3 source during its validity window; the metadata stays DELETED. TASK-010
must check and conditionally exclude tombstones on every processing transition,
including delayed/duplicate events and races. Local tests only demonstrate the
current persisted state without a running event processor.

Case versions are checked but not incremented by document mutations, consistent
with ADR-010. TASK-013 must coordinate concurrent document-set changes with submission
validation; reading the Case version alone does not prove an unchanged document set.
Retention/physical cleanup requires a later explicit policy; no TTL or destructive
cleanup is introduced. Real transactions, CORS/JWT/IAM and late-event behavior stay
in TASK-021 under ADR-007.

TASK-013/ADR-016 completes submission coordination: document mutations atomically
increment Case.documentRevision with their existing audit; Case lifecycle version
remains unchanged. Submission conditions on that revision to fence stale reads.
