# TASK-012 verification

Date: 2026-09-16. Status: DONE. Local acceptance under ADR-007.
Cloud acceptance: NOT RUN, owner TASK-021.

## Scope and acceptance

Started from clean ac19d940053924ecf77186d16a9ccee297167029; TASK-011 locally DONE.
Read AGENTS, PROJECT_STATUS, tasks, CHANGELOG, DECISIONS, ADR-002/007/014,
Technical Design 9.1-9.3, current schema, producer/publisher and infrastructure.

- Create custom bus Terraform module, export actual ARN/name and replace planned
  ARN with resource output. Stream configuration enabled after bus dependency.
- Default S3 pipeline untouched; no domain/default forwarding or cross-account policy.
- Three real local producer paths produce CaseCreated, DocumentValidated and
  DocumentValidationFailed; publisher delivers each through Moto EventBridge to
  its domain observation queue, with no event on the default observation queue.
- Synthetic local S3 event on default is observed there, not on domain. Identical
  tap patterns ensure tests establish bus isolation rather than filter differences.
- Delivered event validates against new routing envelope and existing detail schemas.
  Bad source/type/version/time/internal field/status are rejected in contract tests.
- AST publication ownership and Terraform no-publisher-policy assertions protect
  Case/document command boundaries. No runtime handler changes or new dependencies.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | 260 backend tests including 10 new domain tests; Ruff lint/format; mypy 39 source/test files and 4 scripts; frontend lint/format/1 test/type/build; Python sdist/wheel |
| terraform init -backend=false -input=false -lockfile=readonly | PASS | Domain module/test initialized; provider lock unchanged |
| terraform fmt -check -recursive infra | PASS | Final format |
| terraform validate | PASS | Dev config valid |
| terraform test | PASS | 24 mocked plans, including domain resource/output wiring and command publication isolation |
| git diff --check | PASS | Final whitespace |
| Lambda ZIP revalidation | NOT RUN | Runtime and packaging unchanged; TASK-011 evidence retained |
| Live AWS and hosted CI | NOT RUN | No deployment authorized; real checks owned by TASK-021 |

Terraform executable .tools/terraform-1.14.9/terraform.exe; init/validate/test use
-chdir=infra/environments/dev. Full checks use project-managed Python/Node.
Initial targeted 9-pass/1-fail run and type failure were corrected before the final
full passing run. Schema references resolve locally, without fetching their IDs.

## Corrections and limitations

Initial targeted run: nine passes and one failed date-time rejection because
jsonschema's optional format dependency was unavailable. Added an explicit stdlib
timestamp checker to the local validator; SDK kwargs fixture received a type
annotation before the final passing full check.

Schema contracts are local files, not server-side EventBridge validation. Moto does
not establish real IAM, AWS source delivery, encryption or Lambda poller behavior.
Observation SQS resources are test-only. Production domain subscribers remain
planned for TASK-019; accepted publication does not establish consumer receipt.
Mapping enabled refers to Terraform configuration, not live deployment.
Runtime/package code unchanged; TASK-011 isolated package evidence is retained.
Existing stream-expiry and duplicate-delivery limits remain ADR-014/TASK-020/021.

TASK-013 must resolve the recorded PRD PROCESSING vs design SUBMITTED resubmission
state discrepancy before implementation. That decision is not made in TASK-012.

## Exact changed files

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/tests/integration/test_domain_events.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/014-outbox-stream-publication.md
- docs/adr/015-custom-domain-bus.md
- docs/events/README.md
- docs/events/domain-event.schema.json
- docs/tasks.md
- docs/verification/TASK-012.md
- infra/README.md
- infra/environments/dev/domain_events.tf
- infra/environments/dev/outbox.tf
- infra/environments/dev/tests/cases.tftest.hcl
- infra/environments/dev/tests/documents.tftest.hcl
- infra/environments/dev/tests/domain_events.tftest.hcl
- infra/environments/dev/tests/outbox.tftest.hcl
- infra/modules/domain_events/main.tf
- infra/modules/domain_events/outputs.tf
- infra/modules/domain_events/variables.tf
- infra/modules/domain_events/versions.tf
- infra/modules/lambda/outputs.tf
