# DocFlow backend

Python 3.13. Use the repository bootstrap/check commands for pinned dependencies,
lint, types, local unit/integration tests and package builds.

## Checklist templates (TASK-004)

common.templates.models contains immutable validated Template/Check definitions.
common.templates.repository.TemplateRepository accepts a boto3 DynamoDB client and
table name. resolve_active(case_type) selects the highest numeric published version;
get_version(template_id, version) retrieves an exact immutable version and its checks.
publish(template, actor_id=...) conditionally inserts metadata/checks/audit atomically,
returns True on creation or False on identical replay, and raises TemplateConflict for
content disagreement. These are internal operator/repository functions, not public APIs.
Unsupported case types or missing versions raise TemplateNotFound.

The first seed is supplier-onboarding v1 for SUPPLIER_ONBOARDING. It requires
COMPANY_REGISTRATION, DIRECTOR_ID, BANK_INFORMATION and ADDRESS_PROOF, with four
required review checks and one optional observations check. Instructions are sample
portfolio workflow guidance, not a jurisdiction-specific compliance policy.

Preview without network calls (Windows, repository root):

    backend/.venv/Scripts/python.exe scripts/seed_templates.py

Write only to an already running local DynamoDB-compatible service/table:

    backend/.venv/Scripts/python.exe scripts/seed_templates.py --endpoint-url http://127.0.0.1:8000 --table docflow-dev

The local table needs string PK/SK. The script does not create tables, start services
or support AWS endpoints. Default preview needs no credentials. Tests use Moto in-process
and require neither Docker nor an AWS account; no persistent local server is started.
Run twice against the same local table to verify the second run reports an exact match.

The repository never overwrites existing versions. Use a new version for changed
content. Cases must persist their chosen template ID/version in TASK-005. Upgrading the
active template does not change historical reads. See ADR-008 for query/transaction/audit
details, limits and future management scope.

Local integration tests run automatically with pytest and scripts/dev.py check.
Moto evidence covers request/serialization and modeled behavior; real AWS seed,
permissions/transactions/concurrency are NOT RUN until TASK-021.
The health ZIP remains dependency-free because it contains only case_api. Future
Lambda packages that import templates must bundle the pinned SDK/runtime dependencies.

## Case APIs (TASK-005)

case_api.command.handler implements POST /api/v1/cases; case_api.query.handler
implements the three Case GET routes plus health. common.cases.repository persists
Cases transactionally with audit/outbox and exposes scoped queries. TABLE_NAME is
the only application environment setting; production credentials use the Lambda role.
API tests inject the same repository with a Moto client and make no AWS calls.

The Case API ZIP now bundles pinned requirements-runtime.txt dependencies using
scripts/package_cases.py. The original health ZIP remains a small standalone artifact.
See docs/api/README.md and ADR-009 for roles, cursor semantics, error shapes and
the absence of HTTP POST deduplication guarantees. Outbox publication is not yet enabled.


TASK-007 adds document_api.command.handler to the shared cases.zip. It accepts
metadata only, conditionally reserves Document/audit then signs S3 PUT. No new
runtime dependencies. Run tests/integration/test_documents.py for local upload
contracts and races; shared DynamoDB fixtures live in integration/conftest.py.
The signing client uses SigV4 and exact content length/type with If-None-Match.
Neither test output nor application logs should expose a presigned URL.


TASK-008 extends document_api.command.handler with audited soft deletion implemented
in document_api/deletion.py. Deletion requires only DynamoDB, leaves S3 untouched,
returns empty 204 and persists terminal DELETED metadata; detail queries hide it.
Rerun the document integration suite for retries, Case/document races and history.
TASK-010 consumers must conditionally reject DELETED rows to prevent resurrection.

TASK-009 adds ten local Moto EventBridge-to-SQS routing scenarios using the Terraform
pattern template. Moto events/sqs extras (including jsonpath-ng) are development-only;
no runtime dependency changes. Run scripts/dev.py check from the repository root.
These tests do not establish real AWS policy enforcement or redrive timing.

## Document processor (TASK-010)

Entry point document_processor.handler.handler consumes raw EventBridge envelopes
in SQS bodies and returns batchItemFailures. Configure TABLE_NAME/DOCUMENT_BUCKET.
Leased processing, source-pinned S3 reads, bounded SHA-256 and audited transactions
are implemented; terminal tombstones are preserved. See ADR-013 for validation limits.
Run tests/integration/test_document_processor.py for duplicate/crash/transaction,
partial-batch and Moto forced-DLQ coverage. Real retries remain TASK-021. The package
script now includes this worker in cases.zip; runtime dependencies are unchanged.

## Outbox publisher (TASK-011)

Entry point outbox_publisher.handler.handler consumes DynamoDB Streams and needs
TABLE_NAME and an explicit custom DOMAIN_BUS_ARN. It checks the current outbox,
sends one event entry, then conditionally marks DISPATCHED. Partial batch failures
use the first failed SequenceNumber. Runtime dependencies are unchanged; cases.zip
contains the publisher. Run tests/integration/test_outbox_publisher.py for local
Streams/EventBridge, failure-window, duplicate and contract tests. See ADR-014.

TASK-012 adds test_domain_events.py: actual Case/document producers and publisher
route to a custom Moto bus with default-bus isolation, full envelope validation and
publication-boundary regressions. JSON Schema references resolve offline. Production
handlers/runtime dependencies are unchanged; see docs/events/domain-event.schema.json.


TASK-013 adds submit/resubmit to case_api.command: historical-template validation,
atomic Case/audit/outbox/durable receipt and documentRevision concurrency fencing.
Document reservation/deletion/processor mutations increment that revision in their
existing transactions. Public Case/detail projections omit internal workflow input.
New cases.submission and cases.documents are included by existing package discovery.
No dependency changes. TASK-014 implements real SDK start/recovery; see ADR-017.

Workflow workers are workflow_validate_case.handler and workflow_failure_handler.handler.
The command starts Standard after submit and recovers CASE/PENDING stream records.
Local tests run the checked-in ASL subset with real workers/Moto persistence and a
Standard-service double; SDK Stubber verifies wire shapes, not AWS orchestration.


TASK-015 adds workflow_create_review_task.handler and review_api.query.handler.
Create one deterministic review per Case attempt, prepare up to 98 checklist rows
before atomic public creation, and refresh newer callback tokens without resetting
findings. The Standard ASL now waits for callback; TASK-017 provides decision delivery.
GET /api/v1/reviews supports available/mine, status, limit and cursor; detail includes
public task/Case/documents/checks. Reviewer/admin authorization and current GSI
candidate re-reads prevent cross-reviewer leaks. Tokens never enter DTOs or events.
Run py -3.13 scripts/dev.py check from repository root; test_reviews.py covers
persistence, interruption, concurrency, token generations and authorization.


TASK-016 adds review_api.command.handler and common.reviews.commands. claim/start/
check updates use current Case/Task transaction guards; check writes increment
per-check version and task checkRevision without replacing callback fields.
Admins may claim but cannot start/edit another assignee's task. Same-state retries
are guarded no-ops. Only ReviewStarted adds a fact; claim/check changes add audit.
Comments are stored on checks, never copied into events/audit/logs. TASK-017
guards decisions with checkRevision. Packaging already includes review_api recursively.


TASK-017 adds common.reviews.decisions/finalization and workflow_finalize_case.handler.
Decision requests require UUID Idempotency-Key and assignment. 503 CALLBACK_PENDING
means retry the same body/key; 202 confirms callback delivery, with asynchronous
Case finalization. First decision is immutable; checkRevision prevents stale
checklist acceptance. Failure closes the task while preserving findings/decisions.
See test_review_decisions.py for callback/transaction/finalizer fault injection,
and test_domain_events.py for all eleven producer envelopes. No runtime dependency
was added; scripts/package_cases.py includes the finalizer.


TASK-018: test_resubmission_e2e.py covers requester create/upload, local object
validation, initial submit/start/review/info request, replace/add, resubmit and
second-review approval. Production HTTP boundaries and transaction code run over
Moto; Standard start/callback is an explicit double and ASL routing is read from
the checked-in definition. No Case state or check rows are fabricated with direct
test writes. Previous Task/CHECK/audit history and original bytes are preserved.

Run .venv/Scripts/python.exe -m pytest tests/integration/test_resubmission_e2e.py -q
from backend. Type checking must include src/tests (or use configured mypy);
checking one test alone resolves some editable application packages as untyped.
Full baseline is TASK-017; TASK-018 changes tests/documentation only.


TASK-019 adds notification_worker.handler: read/validate the committed event,
claim IDEMPOTENCY#notification-worker by eventId, resolve a verified recipient,
send SES, then conditionally complete. Partial failures retry independently and
never write Case state. Completed receipts have no TTL; uncertain SES acceptance
can resend email on retry. Run tests/integration/test_notifications.py for local
fakes/Moto coverage. Runtime packaging includes the worker; no new dependencies.


TASK-020: common.logging emits safe JSON/EMF and wraps Lambda entry points.
operations_monitor performs a bounded projected read-only status scan; it never
repairs business state. outbox_publisher also accepts IAM-only recoverOutbox with
one caseId/eventId. No public route or SDK dependencies are added. Operational
counters are approximate; see ADR-022 and docs/runbooks/operations.md. Targeted
checks: .venv/Scripts/python.exe -m pytest tests/integration/test_observability.py.
