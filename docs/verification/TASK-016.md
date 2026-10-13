# TASK-016 verification

Date: 2026-09-17. Status: DONE. Local acceptance under ADR-007.
Cloud acceptance: NOT RUN, owner TASK-021.

## Scope and acceptance

Started from clean aac44a16d4c4e5a3e84fdfa714b8561a31d7c9c2; TASK-015 DONE.
Read AGENTS/status/tasks/changelog/DECISIONS, ADR-007/018, design 6.6/8.8/9/13.11-13.13/
14, PRD review/auth/audit requirements and current persistence/query/IAM/event code.

ADR-019 explicitly resolves two task-owned documentation differences: TASK-016's
assigned-only start/update acceptance overrides the broader Admin=Yes matrix cells;
existing NULL reviewerId and absent reviewerId both mean unassigned. No key changes.

- Claim transaction checks current Case state/version/attempt, conditionally assigns
  PENDING task/owner/GSI1 and writes audit. Deterministic overlapping reads/writes
  produce one winner and one 409; another principal cannot take over.
- Start atomically records Task IN_PROGRESS/startedAt/GSI1, Case IN_REVIEW/version/
  GSI2, audit and ReviewStarted outbox. Duplicate active start returns original
  startedAt without a second fact. Admin must own the task like any reviewer.
- Checklist PUT only changes an existing skeleton on assigned current active review.
  Validated enum/comment/IDs/body. Atomic check version, task checkRevision, finding
  update and audit prevent concurrent stale writes; identical replay is a guarded no-op.
  Comments never enter audit/events/activity; callback token/generation are preserved.
- Timeout/new-attempt/terminal-state races reject writes without partial task, Case,
  finding, audit or outbox effects. Storage errors are sanitized 503.
- API 0.8.0 response contracts, ReviewStarted schema/envelope, publisher allowlist
  and actual local producer-to-bus tests agree. Public responses exclude tokens.
- Three JWT routes and PUT CORS use the planned command Lambda and central log.
  IAM permits table GetItem and CASE-only transactional Put/Update/ConditionCheck,
  with no Query/index/Scan/S3/EventBridge/callback permission.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | 429 backend tests in 363.61s; Ruff lint/format; mypy 60 source/test files + 4 scripts; frontend Prettier/ESLint/Vitest 1/TypeScript/Vite; Python sdist/wheel |
| Targeted command/domain checks | PASS | 54 command cases and prior domain cases passed initially; missing docflow.review test tap was fixed and failing event case re-run PASS (4.87s), then all passed in full suite |
| terraform init -backend=false -input=false -lockfile=readonly -no-color | PASS | New local module/test instances initialized; AWS 6.64.0 lock unchanged |
| terraform fmt -check -recursive infra | PASS | Final format |
| terraform validate -no-color | PASS | Final dev composition |
| terraform test -no-color | PASS | 34 provider-mocked plans including final GetItem-only command read IAM, transactional writes, JWT routes, PUT CORS and dev wiring |
| scripts/package_cases.py twice | PASS | Identical SHA256; compressed 16,382,561 / expanded 22,509,605 bytes, below Lambda limits |
| Python -I -S isolated ZIP imports | PASS | New command/common module and query/creator/publisher import from archive only |
| OpenAPI local reference resolution | PASS | All local references resolve |
| git diff --check / task-file credential-pattern review | PASS | Final whitespace and inventory contain no credentials, state or private key files |
| Live AWS / hosted CI | NOT RUN | No cloud deployment authorized; IAM/JWT/concurrency/delivery evidence deferred to TASK-021 |

Terraform .tools/terraform-1.14.9/terraform.exe uses -chdir=infra/environments/dev
for init/validate/test. No actual AWS plan/apply, deployment or cloud writes.
ZIP SHA256: eabb255af38ee14df15738a61e1b3e3b9504fb342c5752a5236be6c52789a836.
No dependencies or provider lock changes. Initial import formatting and test tap
coverage were corrected before the final passing run.

## Limits and TASK-017 handoff

Moto persistence and deterministic overlapping transaction interleavings exercise
production code and rollback guards; they do not prove actual AWS concurrency,
JWT validation, IAM or GSI propagation. Those checks remain NOT RUN / TASK-021.

Claim replay is a no-op only for the same owner while CLAIMED. Start replay is a
no-op only while assigned IN_PROGRESS/current Case IN_REVIEW. A concurrent loser
can receive 409 and must refresh. There is no reassignment or closed-task reopening.

Per-check version and task checkRevision are internal counters (absent means zero).
TASK-017 must read task revision before checklist validation and condition decision
writes on the same revision, ownership/status and current Case attempt. This task
does not send callbacks or implement decision idempotency/finalizers.
Callback refresh preserves all findings; commands never overwrite callback fields.
The existing ReviewCallbackReceived intermediate terminal remains pending TASK-017.

## Exact files changed

- PROJECT_STATUS.md
- README.md
- backend/README.md
- backend/src/common/reviews/commands.py
- backend/src/outbox_publisher/handler.py
- backend/src/review_api/command.py
- backend/tests/integration/test_domain_events.py
- backend/tests/integration/test_review_commands.py
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/PRD.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/019-review-commands.md
- docs/api/openapi.yaml
- docs/events/README.md
- docs/events/domain-event.schema.json
- docs/events/review-started.schema.json
- docs/runbooks/workflow-recovery.md
- docs/tasks.md
- docs/verification/TASK-016.md
- infra/README.md
- infra/environments/dev/health.tf
- infra/environments/dev/tests/reviews.tftest.hcl
- infra/environments/dev/workflow.tf
- infra/modules/api/main.tf
- infra/modules/api/review_commands.tf
- infra/modules/api/variables.tf
- infra/modules/lambda/database.tf
- infra/modules/lambda/variables.tf

## Documentation updated

- PROJECT_STATUS.md
- README.md
- backend/README.md
- docs/CHANGELOG.md
- docs/CLOUD_ACCEPTANCE.md
- docs/DECISIONS.md
- docs/PRD.md
- docs/TECHNICAL_DESIGN.md
- docs/adr/019-review-commands.md
- docs/api/openapi.yaml
- docs/events/README.md
- docs/events/domain-event.schema.json
- docs/events/review-started.schema.json
- docs/runbooks/workflow-recovery.md
- docs/tasks.md
- docs/verification/TASK-016.md
- infra/README.md

## GitHub publication

Automatic publication follows verified local completion under AGENTS 7.1.
The completion response reports the commit and verified remote result.
GitHub publication does not authorize or trigger AWS deployment.
