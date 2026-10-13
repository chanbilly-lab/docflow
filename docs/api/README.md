# API contracts

openapi.yaml uses JSON syntax (valid YAML) and OpenAPI 3.1. The health and Case
handlers are implemented locally; no cloud endpoints have been deployed.

All routes require a Cognito access token for the configured issuer/client and
aws.cognito.signin.user.admin scope. This scope does not confer the DocFlow admin role.
API Gateway validates JWT signatures; handlers trust only its authorizer context,
then apply backend role/ownership checks. Never substitute request headers for claims.

| Route | Behavior |
| --- | --- |
| GET /api/v1/health | Authenticated liveness; no dependency readiness test |
| POST /api/v1/cases | Requester/admin creates own DRAFT with active template binding and atomic audit/outbox |
| GET /api/v1/cases | Own Cases by default; admin owner=all requires status |
| GET /api/v1/cases/{caseId} | Authorized Case/document/current-review summary |
| GET /api/v1/cases/{caseId}/activity | Authorized audit activity page |

Create accepts only caseType=SUPPLIER_ONBOARDING. The backend generates IDs and owner.
Repeated successful POSTs create separate Cases; HTTP idempotency is not guaranteed.
Unsupported input is 400, unauthenticated 401, forbidden role 403, missing/inaccessible
Case 404, unavailable template/storage 503. Gateway JWT errors retain its message
response; backend errors use error.code/message/correlationId.

List limit defaults to 20; activity to 50; accepted range is 1-100. GSI lists are
eventually consistent, newest first. An empty filtered page can still have nextCursor:
continue until null. Cursors bind the principal and query scope, but are not signed
authorization credentials or snapshots. The server reconstructs partition keys from
authorized context and never accepts client-supplied database keys.

Details omit workflow tokens, execution ARNs, callback state, S3 keys and storage keys.
Unknown nested attributes are not copied into responses. Document/review mutations
arrive in later tasks; empty collections are expected for newly created Cases.

Use backend tests/integration/test_cases.py for credential-free request examples
against the real SDK repository with Moto. Health/Case Lambda entry points are
case_api.query.handler and case_api.command.handler. Tests inject a local repository;
production uses TABLE_NAME and the Lambda execution role. No local public server is
started. Build packages with scripts/package_health.py and scripts/package_cases.py.

See ADR-009 and docs/events/case-created.schema.json. TASK-021 retains real
token, IAM, DynamoDB and HTTP acceptance in docs/CLOUD_ACCEPTANCE.md.

## Authorization regression coverage (TASK-006)

The existing Technical Design section 14 / ADR-009 rules are checked through the
actual backend HTTP boundary and repository with local Moto fixtures:

| Implemented operation | Requester | Reviewer | Admin |
| --- | --- | --- | --- |
| Create Case | Own identity | Denied | Own identity |
| List Cases | Own partition | Denied | Own partition; all requires status |
| Case detail/activity | Owner only | Assigned Case only | Any Case |

Combined roles may use any permission granted by their trusted groups. Ownership
alone does not grant a reviewer access without assignment; assignment alone does
not grant a requester reviewer privileges. Other users receive the same 404 as a
missing Case. Private reviewer comments remain excluded from these public DTOs.

TASK-006 covers assignment changes, cross-Case assignment, forged identity headers,
owner query injection, group representations, denied-write side effects and forged
cursor positions. No frontend check is required for enforcement. See
../verification/TASK-006.md for exact evidence and deferred live checks. Mutation
and review-queue authorization is tested when those APIs are implemented.


## Direct document upload (TASK-007)

POST /api/v1/cases/{caseId}/documents/upload-url accepts only documentType,
fileName, fileSize (exact bytes) and mimeType. Owner requester/admin may reserve
uploads for DRAFT or NEEDS_INFORMATION; reviewers cannot. The bound historical
template must permit the type. PDF <=15,000,000 bytes; JPEG/PNG <=10,000,000 bytes.
The endpoint creates UPLOADING metadata plus audit before returning 201 with
 documentId and upload.method/url/expiresAt/requiredHeaders. No file bytes enter it.

Client sequence: request metadata authorization, then PUT the raw File/Blob directly
to upload.url with every requiredHeaders value. Do not send FormData or a bearer
Authorization header to S3. The browser sets Content-Length from the exact file;
non-browser clients must supply that signed length. Preserve Content-Type and
If-None-Match: *. Reusing the URL after successful upload cannot overwrite the source.
No frontend business upload screen is implemented by this task.

URLs expire after at most ten minutes (credentials may expire sooner). Never log,
store or share them. State changes do not instantly revoke an issued URL. A failed
signing step leaves audited metadata and returns 503; POST retries create new IDs.
409 reports invalid Case state or a concurrent change; 413 excessive size, 415 MIME,
422 a type outside the bound template. See OpenAPI and ADR-010 for exact contracts.

Configured dev browser origins are http://localhost:5173 and http://127.0.0.1:5173.
Real browser CORS, expiry, signature tampering and upload replay checks are NOT RUN,
owned by TASK-021. Backend tests use local mocks and actual SDK signing only.


## Document deletion (TASK-008)

DELETE /api/v1/cases/{caseId}/documents/{documentId} has no body/query parameters.
Owner requester/admin only, in DRAFT or NEEDS_INFORMATION. Reviewer-only callers
cannot delete; admin does not bypass the Case state gate. Success is empty 204.
The backend atomically soft-deletes metadata and records audit; original S3 bytes
and historical fields remain. Case detail omits DELETED entries for every role.

Retrying the same tombstone returns 204 without a duplicate audit, provided current
permissions and Case state still allow it. 409 reports a state or concurrent-change
conflict; refresh before retrying. Missing or cross-Case document IDs return 404.
Use a new upload request for a replacement; old IDs/keys are never reused.
Soft deletion does not instantly revoke an issued upload URL. Physical cleanup and
late-event processing guards are separate work. See ADR-011 and TASK-008 evidence.


## Submission and resubmission (TASK-013)

POST /api/v1/cases/{caseId}/submit requires DRAFT; /resubmit requires
NEEDS_INFORMATION. Owner requester/admin only. Send an empty JSON object and a
UUID Idempotency-Key. Backend checks the Case's historical template and every
active document. Missing required types, invalid, and not-ready return 422.
Deleted documents do not count. Conditional changes return 409.

Successful 202 atomically records SUBMITTED, next attempt, audit, event and durable
receipt. Same Case/principal/key replays original status/attempt without another
attempt, even after later state changes. Use a new key for a new operation:
cross-operation reuse returns IDEMPOTENCY_KEY_REUSED. Failed validation consumes
no key. Retry uncertain 503 with the same key. Never send attempt/state in the body.

TASK-014 now attempts Standard start after commit and on same-key replay.
workflowExecutionId is the confirmed current-attempt ARN; old receipt replay after
a newer attempt returns null rather than that newer ARN. Start failure returns
sanitized 503 while preserving the accepted receipt: retry with the same key.
A pending intent older than 85 days requires operator recovery investigation.
No live endpoint is deployed. See ADR-017 and the workflow recovery runbook.
