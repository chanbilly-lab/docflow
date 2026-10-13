# ADR-008: Immutable checklist template persistence

**Status:** Accepted
**Date:** 2026-09-16

## Context

TASK-004 must resolve a case type to its active template, load historical versions and
seed supplier onboarding repeatedly without changing prior Case behavior. Section 6.10
defines metadata/check keys but does not specify active lookup or publication atomicity.

## Decision

- Preserve PK TEMPLATE#{templateId}, metadata SK VERSION#{version}, and check SK
  VERSION#{version}#CHECK#{order}#{checkId}. No GSI, table or existing key changes.
- For the initial supported type, a backend mapping binds SUPPLIER_ONBOARDING to
  supplier-onboarding. Resolve the highest numeric version whose metadata is ACTIVE
  using a strongly consistent, paginated partition Query; never Scan in the repository.
  ACTIVE means published/eligible; several immutable versions may remain ACTIVE,
  with only the highest selected for new Cases. Load bound historical versions directly.
- Publication is activation for this first operator seed path. There is no mutable
  draft/retire/rollback management API in TASK-004. A future administrative lifecycle
  must be explicitly designed; do not mutate prior published definitions.
- Metadata, all checks and one append-only template audit are conditionally inserted
  in one TransactWriteItems call. Every key must be absent. Template audit uses the
  same template partition and SK AUDIT#{timestamp}#{auditId}; existing CASE audit
  keys remain untouched. Audit records actor/action/version/content hash/time.
- No business domain event is defined for initial configuration seeding, so no
  outbox event is invented. Case creation audit/outbox remains TASK-005.
- Store checkCount and a canonical SHA256 contentHash to detect incomplete/changed
  content. An identical replay returns without writes/a new audit; a conflicting
  immutable version fails. Recover only an identical completed racing publication.
  Backend/IAM errors propagate. Sorting uses numeric version/order, not string order.
- Enforce 1-98 checks, at most 50 document types, bounded identifiers/instructions,
  unique check IDs/orders and document references. The two other transaction actions
  are metadata and audit, within the 100-action DynamoDB limit.
- Use pinned boto3 as runtime SDK and boto3 DynamoDB stubs for development. Moto is a
  development-only in-process emulator testing the actual boto3 repository. It is not
  evidence of real AWS service guarantees or a production architecture replacement.
- scripts/seed_templates.py previews without writes by default. Its write mode accepts
  HTTP loopback endpoints only, with dummy local credentials and an existing local table.
  Actual AWS seed execution/authorization is deferred to TASK-021.

## Consequences

The initial partition lookup reads checks along with metadata and is acceptable for a
small template catalog; it is not a general large-scale template search implementation.
New versions never rewrite historical definitions. Real contention/permissions and
AWS transaction behavior remain in consolidated cloud acceptance under ADR-007.
No Case/API/IAM/Terraform deployment or frontend business feature is added here.

References:
- https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TransactWriteItems.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html
