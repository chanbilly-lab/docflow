# TASK-014 verification

Date: 2026-09-17. Status: DONE. Local acceptance under ADR-007.
Cloud acceptance: NOT RUN, owner TASK-021.

## Scope and acceptance

Started from clean 5b0fb997356d24bc84cc495a6f71f0ea23a63159, TASK-013 DONE.
Read AGENTS/status/tasks/changelog/decisions, ADR-002/007/016, design 8.6/8.11/12,
submission/receipt code, packaging, event contracts and existing IAM/stream modules.

- Standard StartExecution uses persisted deterministic name and canonical input.
  Actual ARN acknowledgement guards attempt/name/input/PENDING and preserves state.
- Reconcile ExecutionAlreadyExists only after matching DescribeExecution identity;
  closed executions do not restart. Lost response/accepted-start-failed-save retries
  preserve one execution. Stale attempts cannot overwrite or start the latest one.
- HTTP receipt replay, filtered Stream partial checkpoints and direct IAM operator
  invocation recover committed pending work. Old pending intent fails closed at 85d.
- Defensive validation checks original input/context, state/attempt, bound template,
  required active VALID documents and revision; conditional PROCESSING/audit transaction.
- Technical failure commits WORKFLOW_FAILED/audit/CaseWorkflowFailed atomically;
  duplicate handling is harmless. No REJECTED transition or raw failure Cause persisted.
  Failure-handler persistence outage propagates and is recoverable by trusted retry.
- New failure producer traverses actual local publisher and custom bus isolation tests.
- Checked-in executable ASL ends at FoundationComplete with Case PROCESSING.
  This is a foundation, not review completion. TASK-015 must add real callback review.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | 346 backend tests in 268.17s; Ruff lint/format; mypy 49 source/test files and 4 scripts; frontend Prettier/ESLint/Vitest 1/TypeScript/Vite; Python sdist/wheel |
| Targeted workflow/domain pytest | PASS | Initial 40 tests; five additional race/failure/SDK tests included in final full suite |
| terraform init -backend=false -input=false -lockfile=readonly -no-color | PASS | Initialized new workflow module and mocked test modules; provider 6.64.0 lock unchanged |
| terraform fmt -check -recursive infra | PASS | Final formatting |
| terraform validate -no-color | PASS | Dev composition valid |
| terraform test -no-color | PASS | 28 provider-mocked plans; Standard/logging/worker identity, starter IAM/stream filter, worker transactional scope, dev composition |
| scripts/package_cases.py twice | PASS | Identical ZIP; compressed 16,370,993 / uncompressed 22,477,335 bytes, below Lambda limits |
| Python -I -S isolated ZIP imports | PASS | Command, common workflow and both new worker handlers import using ZIP dependencies |
| API refs / ASL graph / common secret-pattern review | PASS | Local refs resolve, targets exist, no REJECTED ASL state, no credentials/state artifacts among changed files |
| git diff --check | PASS | Final whitespace |
| Real AWS / hosted CI | NOT RUN | No cloud writes authorized; live Standard/IAM/stream/recovery evidence remains TASK-021 |

Terraform .tools/terraform-1.14.9/terraform.exe uses -chdir=infra/environments/dev
for init/validate/test. Application tooling is project-managed.
ZIP SHA256: f371cf9da9fc2d3f60d36f3772525f73059524c398a932d2fd6555f5df62237e.

Initial lint wrapping/import issues corrected before the final passing full run.
No new runtime/development dependency or provider lock change.

## Verification limits and handoff

Local persistence is Moto. Standard-service double implements same-name/input
running/closed behavior; botocore Stubber verifies real start/describe wire shapes.
The test ASL subset runner reads the actual checked-in definition, invokes actual
workers and exercises Retry/Catch/Choice/ResultPath and both terminals. It is not
the AWS Step Functions engine and cannot certify service behavior or IAM. TASK-021
must exercise actual StartExecution, closed retries, delivery and recovery.

Stream retains 24h; durable pending records survive but require explicit operator
recovery after expiry. No background scan or new scheduled service was added.
The 85-day guard intentionally requires investigation rather than bypassing service
name-reuse limits. Failure-persistence outages need trusted retry. See the runbook.
No automatic business resubmission from WORKFLOW_FAILED is introduced.

Only payload-free workflow logs are configured; no callback tokens exist in this
task. TASK-015 must replace FoundationComplete with real review/callback creation
and retain original execution input on Catch. TASK-017 supplies final decisions.
No human-review or production deployment acceptance is claimed.

## Exact changed files

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/case_api/api.py
- backend/src/case_api/command.py
- backend/src/common/cases/submission.py
- backend/src/common/cases/workflow.py
- backend/src/common/cases/workflow_state.py
- backend/src/outbox_publisher/handler.py
- backend/src/workflow_failure_handler/__init__.py
- backend/src/workflow_failure_handler/handler.py
- backend/src/workflow_validate_case/__init__.py
- backend/src/workflow_validate_case/handler.py
- backend/tests/integration/test_domain_events.py
- backend/tests/integration/test_workflow.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/016-case-submission.md
- docs/adr/017-workflow-foundation.md
- docs/api/README.md
- docs/api/openapi.yaml
- docs/events/README.md
- docs/events/case-workflow-failed.schema.json
- docs/events/domain-event.schema.json
- docs/runbooks/workflow-recovery.md
- docs/tasks.md
- docs/verification/TASK-014.md
- infra/README.md
- infra/environments/dev/cases.tf
- infra/environments/dev/tests/workflow.tftest.hcl
- infra/environments/dev/workflow.tf
- infra/modules/lambda/database.tf
- infra/modules/lambda/main.tf
- infra/modules/lambda/outputs.tf
- infra/modules/lambda/variables.tf
- infra/modules/lambda/workflow.tf
- infra/modules/workflow/definition.asl.json
- infra/modules/workflow/main.tf
- infra/modules/workflow/variables.tf
- infra/modules/workflow/versions.tf
- scripts/package_cases.py
