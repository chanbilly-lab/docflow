# ADR-009: Case creation and query foundation

**Status:** Accepted
**Date:** 2026-09-16

## Decision

TASK-005 implements the four section 13 Case routes as Python Lambda handlers with
local acceptance under ADR-007. No HTTP API deployment or cloud write is authorized.

- Resolve the active template before creating a Case and permanently store its ID/version.
  A later template publication does not change existing Case behavior.
- Generate c_/a_/evt_ UUID-based identifiers server-side and UTC microsecond timestamps.
  Preserve section 6 Case PK/SK, requester GSI1 and status GSI2 keys.
- One conditional TransactWriteItems creates DRAFT Case, CASE_CREATED audit and PENDING
  CaseCreated outbox. No direct EventBridge calls. Outbox detail uses the section 9.2
  envelope and case-created.schema.json. Pending events have no TTL to prevent loss;
  publisher/dispatch retention belongs to TASK-011.
- HTTP POST creates a new Case per successful call. No HTTP idempotency guarantee is
  introduced; clients must not assume retries deduplicate after an uncertain response.
- Use only trusted HTTP API v2 authorizer access-token claims. Creation/listing require
  requester or admin; requester ownership comes from sub, never from request JSON.
  Detail/activity permit owner requester, assigned reviewer or admin. Other users see
  the same 404 as a nonexistent Case. TASK-006 expands adversarial authorization tests.
- Requester list uses GSI1; admin owner=all requires status and uses GSI2. Default is mine.
  Limit 1-100, descending order, optional requester status FilterExpression. A filtered
  page may be empty with a continuation cursor. GSI results are eventually consistent.
- Cursors contain only timestamp/ID position and a scope fingerprint, never raw PK/SK.
  They are bounded, structurally validated and bound to principal/query context. They
  are not signed credentials: the server always reconstructs the partition from the
  authorized principal/query. Forging a position cannot grant cross-partition access.
  Cursors are not snapshots; concurrent changes can affect GSI pagination.
- Exact Case and activity reads use the base table consistently. Detail loads document
  and review prefixes (paginated) and selects highest attempt as current review.
  No document/review mutation is implemented. Explicit scalar whitelists and nested
  projections omit keys, object storage paths, tokens, callback state and outbox data.
  Activity exposes only action/actorType/timestamp. Related reads are not one snapshot.
- Separate case-command-handler and case-query-handler. Query role has GetItem/Query
  on the table and its two indexes. Command role reads templates and has PutItem only
  for CASE# partitions within TransactWriteItems, enforced with IAM condition keys.
  No Scan, update/delete, Cognito admin, EventBridge or workflow permission is granted.
- Reuse all existing central log groups and existing query-function Terraform address.
  Health remains available through query.handler. All four routes require scoped JWTs.
- Package pinned pure-Python SDK dependencies in cases.zip for arm64 Python 3.13.
  No dependency on workstation site-packages or runtime-provided SDK versions.
  OpenAPI 3.1 describes nullable response shapes; JSON Schema validates CaseCreated.

## Consequences

Local tests use the actual boto3 repository under Moto plus JSON Schema assertions
and provider-mocked plans. They do not establish AWS IAM enforcement, JWT signature
validation or cloud concurrency. TASK-021 owns live acceptance. TASK-006 owns broader
authorization verification; TASK-007 onward populate related domain entities.

Sources:
- https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_Query.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis-iam.html
