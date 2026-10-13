# TASK-018 verification

Date: 2026-09-21. Status: DONE. Local acceptance under ADR-007.
Cloud E2E: NOT RUN, owner TASK-021.

## Scope

Started from clean c165c83b079c9000ed2c309b06ca84f0c95cb29e, TASK-017 DONE.
Read AGENTS/status/tasks/changelog/decisions, ADR-007/011/016/018/020, PRD resubmit
flow, related design and API/workflow/persistence code. No production defect
blocked the journey. Test/documentation only: no architecture, API/event, security,
infrastructure, dependency or key changes. No new ADR is required.

## Acceptance

Two scenarios (replace/add) execute production Case/document/review HTTP handlers,
document SQS batch handling, WorkflowStarter, validation/creation/finalization and
outbox publishing. They never fabricate business states/check rows via direct writes.

- Create Case, reserve all required documents, put synthetic PDF bytes into Moto S3,
  process SQS object envelopes to VALID, submit and start the initial review.
- Claim/start/check, then REQUEST_INFORMATION callback finalizes NEEDS_INFORMATION.
  Authorized Case detail exposes exact requestedInformation.
- Replace: soft-delete old ADDRESS_PROOF and reserve a new ID/key. Delayed old
  object notification cannot restore it. Add: retain the original active document
  and upload supplemental ADDRESS_PROOF. Both preserve original S3 bytes.
- Missing/pending documents reject resubmit with 422 and leave attempt 1. Processing
  duplicates leave documentRevision unchanged. Retry with the previously unused key.
- Resubmit returns SUBMITTED/attempt 2 and a distinct execution ARN. Same-key retry
  returns identical receipt; exactly two executions exist.
- Second review uses a distinct task/token and fresh NOT_REVIEWED checklist.
  Claim/start/check/APPROVE completes APPROVED; requestedInformation clears and the
  public currentTask points to attempt 2.
- Entire prior Task/CHECK rows and every pre-existing audit remain identical.
  Old findings remain readable through authorized detail. Historical submit/decision
  replays and delayed creation/finalization/failure workers cannot mutate attempt 2;
  completed finding edits are denied.
- Validate all actual outbox facts against routed schemas, then publish/replay via
  the production publisher over Moto EventBridge. Exactly one information request,
  resubmit and approval, two ready/start facts; all outbox entries become DISPATCHED.

## Commands and results

From backend:
- PASS: .venv/Scripts/python.exe -m pytest tests/integration/test_resubmission_e2e.py -q --tb=short
  (2 passed in 11.01 seconds).
- PASS: .venv/Scripts/python.exe -m mypy src tests ../scripts
  (70 source files, no issues).
- PASS: .venv/Scripts/python.exe -m ruff check . ../scripts
- PASS: .venv/Scripts/python.exe -m ruff format --check . ../scripts
  (71 files already formatted).
- PASS: git diff --check; exact changed-file inspection and credential/state scan.
- NOT RUN: full backend baseline, frontend tests/build, Python build, Lambda ZIP
  and Terraform checks. Only tests/docs changed; production/build/infra inputs
  are unchanged. TASK-017's 471-test, app-build, 34 mocked Terraform tests and ZIP
  PASS records remain historical evidence, not TASK-018 rerun results.
- NOT RUN: real AWS E2E, JWT/IAM, browser presigned PUT/CORS/expiry, real
  S3/EventBridge/SQS delivery, Standard service behavior and GSI propagation.
  Explicitly deferred to TASK-021; no cloud writes/deployment.
- NOT RUN: hosted CI results at local completion.

The initial single-test-file mypy invocation reported untyped editable application
imports. Repository-scoped source/tests/scripts checking passed without ignoring
type errors or changing runtime code.

## Limits and handoff

Moto supplies DynamoDB/S3/EventBridge. Existing Standard start double and a callback
double represent workflow service boundaries; routing reads the actual ASL file,
but this is not a Step Functions emulator. S3 uploads use SDK PUT to Moto after
real reservation/presigning, not browser HTTP. Callbacks finalize synchronously in
this double; TASK-017 separately verifies pending/lost acknowledgement recovery.
TASK-019 owns notifications; TASK-021 owns real consolidated acceptance.

## Files changed

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/tests/integration/test_resubmission_e2e.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/runbooks/workflow-recovery.md
- docs/tasks.md
- docs/verification/TASK-018.md

## Documentation updated

- PROJECT_STATUS.md
- README.md
- backend/README.md
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/runbooks/workflow-recovery.md
- docs/tasks.md
- docs/verification/TASK-018.md

## Publication

Standing AGENTS 7.1 authorization applies after local completion.
Commit format: feat: complete TASK-018 request-information and resubmission E2E.
Completion response reports commit and verified remote result. Push does not deploy.
