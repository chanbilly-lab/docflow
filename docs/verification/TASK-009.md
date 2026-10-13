# TASK-009 verification

Date: 2026-09-16. Status: DONE. Local acceptance under ADR-007.
Cloud acceptance: NOT RUN, owned by TASK-021.

## Scope

Read AGENTS, PROJECT_STATUS, tasks, CHANGELOG, DECISIONS, relevant ADRs,
Technical Design 10/11, PRD upload flow, existing storage/dev modules and tests.
TASK-008 was locally DONE; working tree clean at
80df2f2a16f373d9f054c9c9689f24260d3a118f.

Implemented the default-bus S3 rule, raw-envelope SQS target, standard processing
queue/DLQ, constrained resource/redrive policies and bucket notification wiring.
No consumer, domain event publication or cloud deployment. See ADR-012.

## Acceptance evidence

- Mocked root plan verifies EventBridge enabled on the actual generated bucket,
  without direct SQS/SNS/Lambda notification bypasses.
- Module plan verifies exact source/type/bucket/prefix, default bus, full envelope,
  queue names/encryption/TLS/retention/visibility/polling, maxReceiveCount 5,
  exact-rule publishing permission and exact-source redrive allow policy.
- Ten Moto EventBridge-to-SQS SDK tests use the actual pattern template: two
  accepted versioned keys; eight rejected wrong-source/type/bucket/prefix/case
  or missing bucket/key fixtures. Received messages preserve detail/envelope.
- No hand-written event matcher substitutes for the local routing integration.

## Checks

| Check | Result | Evidence / reason |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | 185 backend tests including 10 routing cases; Ruff lint/format; mypy 32 source/test files and 4 scripts; frontend format/lint/1 test/type/build; backend sdist/wheel |
| backend/.venv/Scripts/python.exe -m pip check | PASS | No broken requirements |
| terraform init -backend=false -input=false -lockfile=readonly | PASS | New local module initialized; provider lock unchanged |
| terraform fmt -check -recursive infra | PASS | Formatted configuration |
| terraform validate | PASS | Dev configuration valid |
| terraform test | PASS | 18 provider-mocked plan runs, including 2 new pipeline runs |
| git diff --check | PASS | No whitespace errors |
| Lambda ZIP repackaging | NOT RUN | Runtime/handlers/packaging unchanged; TASK-008 package evidence retained |
| Live AWS and hosted CI | NOT RUN | No deployment authorized; local results are not cloud/hosted evidence |

Terraform executable: .tools/terraform-1.14.9/terraform.exe; init/validate/test use
-chdir=infra/environments/dev. Full application check uses repository-managed tools.

Initial routing tests exposed a missing Moto events extra, then Moto's omission
of the AWS account envelope field. Added the test-only dependency and corrected
the local envelope assertion; final full run passes all ten cases. Synthetic
aws.s3 events are submitted only inside Moto, never to real AWS.

## Limits

Moto does not prove S3 notification delivery, IAM/TLS/SSE enforcement, redrive
timing or real retry behavior. TASK-010 owns processing/idempotency/partial batches;
TASK-021 owns real bucket upload filtering, queue policy rejection and forced
consumer failure to DLQ. EventBridge delivery retry exhaustion has no target DLQ
under the existing design; SQS DLQ covers only received processing failures.
Unconsumed messages expire after four days. No AWS resources were created.

Existing unrelated carryovers remain: resubmit-state discrepancy TASK-013 and
superseded push-deploy prose synchronization TASK-021.

## Exact changed files

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/pyproject.toml
- backend/requirements-dev.txt
- backend/tests/integration/test_document_pipeline.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/012-document-event-pipeline.md
- docs/events/README.md
- docs/tasks.md
- docs/verification/TASK-009.md
- infra/README.md
- infra/environments/dev/document_pipeline.tf
- infra/environments/dev/tests/document_pipeline.tftest.hcl
- infra/modules/document_pipeline/main.tf
- infra/modules/document_pipeline/outputs.tf
- infra/modules/document_pipeline/s3-created.json.tftpl
- infra/modules/document_pipeline/variables.tf
- infra/modules/document_pipeline/versions.tf
