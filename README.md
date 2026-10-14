# DocFlow

2026-10-14: [privacy-reviewed source](docs/PRIVACY_REVIEW.md) is public at
https://github.com/chanbilly-lab/docflow, on codex/privacy-release. Original work
and history remain in a private read-only archive. New development uses
D:/Projects/docflow-public with GitHub noreply commits; the older checkout points
to the archive. Private identifiers in historical records are redacted; outcomes
and application limitations are preserved. Public source does not deploy a service.

Illustrated project guides: [中文](docs/portfolio/guide-zh.md) |
[English](docs/portfolio/guide-en.md). Both describe purpose, implemented features,
six actual demo screenshots, architecture, local demonstration and evidence limits.

DocFlow is a serverless document review portfolio: immutable requirements, private
uploads, human review, transactional audit/outbox and asynchronous notifications.

Start with the [portfolio guide](docs/portfolio/README.md) for architecture,
security, cost, trade-offs, a local demo and the proposed Project 2 AI roadmap.
Five backend journeys passed a short real-AWS session; the owner subsequently
elected to skip remaining TASK-021 acceptance and retire AWS resources. This is
not a production-readiness claim. See [current state](PROJECT_STATUS.md),
[acceptance limits](docs/CLOUD_ACCEPTANCE.md) and [retirement evidence](docs/verification/AWS-RETIREMENT.md).


## Local development

TASK-001 through TASK-020 supply the local implementation and Terraform baseline.
The React/TypeScript page is an in-memory synthetic demo, without real login,
uploads or backend calls. Backend code implements Case/document/review workflows;
see [backend/README.md](backend/README.md). Local checks need no AWS credentials.

Development now follows [ADR-007](docs/adr/007-local-first-cloud-acceptance.md): finish
TASK-003 through TASK-020 locally, then use TASK-021 for an explicitly authorized short
AWS acceptance session and cleanup. Local DONE does not mean cloud-verified. See the
[cloud acceptance ledger](docs/CLOUD_ACCEPTANCE.md). Under the user's
[ADR-029 exception](docs/adr/029-retire-cloud-and-document-portfolio.md), TASK-022
documents the actual evidence without marking TASK-021 complete.
Completed local tasks are backed up to GitHub automatically; pushes do not deploy AWS.

Prerequisites:

- Python 3.13 with pip and venv (Windows: `py -3.13`).
- Node 22.12+ in the 22.x line, including npm. `.node-version` records the major line.
- Internet access for the initial dependency installation.

From the repository root on Windows:

```powershell
py -3.13 scripts/dev.py bootstrap
py -3.13 scripts/dev.py check
py -3.13 scripts/dev.py dev
```

On macOS/Linux with the specified Python and Node on PATH:

```sh
python3.13 scripts/dev.py bootstrap
python3.13 scripts/dev.py check
python3.13 scripts/dev.py dev
```

`bootstrap` creates `backend/.venv`, installs pinned backend tools from
`backend/requirements-dev.txt`, installs the backend package in editable mode and runs
`npm ci` in `frontend`. No environment activation or Make installation is required.
Repeated bootstrap is supported. The runner exits nonzero on a failed command.

The frontend starts at http://127.0.0.1:5173 (Vite may choose a later port if occupied).
Stop it with Ctrl+C. Production frontend output is `frontend/dist/`; backend package
builds are in `backend/dist/`. Backend wheels are package verification artifacts,
not deployable Lambda bundles.

Optional configuration examples are `.env.example` and `frontend/.env.example`.
They are not required or consumed by the current shell. Copy to `.env` in the same
directory only when configuring future integrations. Never store secrets in `VITE_`
variables: they are exposed to the browser.

### Commands

Prefix each command below with `py -3.13 scripts/dev.py` on Windows or
`python3.13 scripts/dev.py` on macOS/Linux.

| Command | Action |
| --- | --- |
| `bootstrap` | Install locked local dependencies |
| `check` | Backend lint, formatting, type checks, tests; frontend formatting, lint, tests, type check/build; backend package build |
| `format` | Format backend/scripts with Ruff and frontend with Prettier |
| `backend-test` | Run baseline pytest tests |
| `backend-lint` | Run Ruff on backend and developer scripts |
| `backend-typecheck` | Run strict mypy on backend, tests and developer scripts |
| `backend-build` | Build backend sdist and wheel |
| `frontend-test` | Run Vitest once |
| `frontend-lint` | Run ESLint with warnings treated as failures |
| `frontend-typecheck` | Run TypeScript without emitting files |
| `frontend-build` | Type-check and build with Vite |
| `dev` | Run the frontend development server on loopback |

Frontend commands are also available directly via `npm run <script>` in `frontend`.
Backend commands use `backend/.venv/Scripts/python.exe` on Windows or
`backend/.venv/bin/python` on POSIX; run `-m pytest`, `-m mypy`, or `-m ruff check .`
from `backend`.

### Repository layout

- `backend/src/common/`: shared namespaces and immutable checklist-template persistence.
- `backend/src/`: reserved handler/worker directories from Technical Design section 17.
- `backend/tests/unit/`: package, health handler and health response-contract checks.
- `backend/tests/integration/` and `contract/`: local DynamoDB repository integration tests; live cloud tests deferred to TASK-021.
- `frontend/src/` and `frontend/tests/`: minimal shell and rendering test.
- `infra/`: dev database/observability/auth/api/lambda composition; remaining modules reserved.
- `docs/api/` and `docs/events/`: contract locations for later implementations.
- `scripts/dev.py`: cross-platform local commands.
- `.github/workflows/pull-request.yml`: baseline checks on PRs and main pushes.

Seed/demo scripts, deployment/destruction workflows, further API/event schemas and
remaining Terraform resources arrive in their assigned tasks.

### Terraform checks

Use Terraform 1.14.x (verified and CI-pinned: 1.14.9) from the repository root:

```sh
python scripts/package_health.py
python -m pip install -r backend/requirements-runtime.txt
python scripts/package_cases.py
terraform fmt -check -recursive infra
terraform -chdir=infra/environments/dev init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/environments/dev validate
terraform -chdir=infra/environments/dev test
```

On this Windows workstation, use `./.tools/terraform-1.14.9/terraform.exe` in place of
`terraform`. The checks require no AWS credentials; initial provider download requires
network access. These are separate from application `scripts/dev.py check` and run in
PR CI. See [infra/README.md](infra/README.md) for inputs, outputs, state handling and
provider lockfile updates. No cloud deployment is included in TASK-002.

### Dependency updates and local runtimes

Frontend versions are exact in `package.json`; commit `package-lock.json` after intentional updates.
Backend development ranges are declared in `backend/pyproject.toml`; the fully resolved
versions for Python 3.13 are pinned in `backend/requirements-dev.txt`. After an intentional
tool update, regenerate pins from a clean Python 3.13 environment, exclude the local editable
package, and run the complete check command. Do not use an unrelated global environment.

On the initial Windows workstation, Node 22.23.2 was downloaded from nodejs.org and verified
against its published SHA256 checksum. It lives under `.tools/node-v22.23.2-win-x64/`.
The developer runner automatically uses a project-local Node 22 Windows distribution if
present; other machines can install Node normally. `.tools/` is ignored and is not required
in version control. Existing system runtimes are retained. Use `py -3.13` explicitly because
the Python launcher may default to Anaconda 3.10. Restart your terminal after changing PATH.

Node compatibility reference: [Vite getting started](https://vite.dev/guide/).

## Human reading order

1. `docs/PRD.md`
2. `docs/TECHNICAL_DESIGN.md`
3. `docs/tasks.md`

## AI/Codex reading order

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/tasks.md`
4. `docs/CHANGELOG.md`
5. `docs/DECISIONS.md`

Normal execution prompt:

```text
执行 TASK-XXX。
```

The current next task is recorded in `PROJECT_STATUS.md`.

TASK-005 adds Case command/query handlers and local boto3/Moto API integration tests.
See docs/api/README.md for routes, pagination and response contracts. For local
packaging on Windows use backend/.venv/Scripts/python.exe scripts/package_cases.py.
No AWS deployment occurs from GitHub pushes; cloud verification remains in TASK-021.


TASK-007 adds a local-verified document upload API with private S3 Terraform,
ten-minute direct PUT signing and atomic initial Document/audit reservation.
File bytes bypass API Gateway/Lambda. Soft deletion is implemented in TASK-008; processing is implemented locally in TASK-010. See docs/adr/010-private-document-upload.md and docs/verification/TASK-007.md.
All AWS deployment and actual browser/S3 expiry checks remain deferred to TASK-021.


TASK-008 adds audited document soft deletion with state/ownership gates, retry
safety and retained history; Case detail hides deleted documents. Physical S3
cleanup remains separate. See docs/verification/TASK-008.md and ADR-011.

TASK-009 adds the default-bus S3-to-SQS pipeline and processing DLQ locally.
Exact bucket/cases-prefix filtering and queue policies are verified with mocks;
TASK-010 supplies the processor. See docs/verification/TASK-009.md and ADR-012.

TASK-010 implements document validation, bounded hashing, leased idempotency and
atomic audit/outbox completion. Partial SQS batch failures and local forced-DLQ
tests are included; actual cloud acceptance remains TASK-021. See ADR-013 and
docs/verification/TASK-010.md. TASK-011 supplies outbox publication.

TASK-011 implements the outbox publisher with conditional dispatch, stable event
IDs and DynamoDB Stream filtering/partial retries. TASK-012 now creates and connects the custom bus with ingestion enabled in Terraform. See docs/verification/TASK-011.md
and ADR-014; local tests are not live AWS evidence.

TASK-012 connects the dedicated domain bus and verifies the three implemented
event envelopes using local producer-to-bus tests. Command handlers still write
outbox records without publishing. See docs/verification/TASK-012.md and ADR-015.


TASK-013 locally implements validated submit/resubmit, durable idempotency and
atomic attempt updates with document-set concurrency protection (ADR-016).
Both operations persist SUBMITTED. TASK-014 implements workflow start and technical failure handling; cloud
acceptance remains NOT RUN under TASK-021. GitHub publication does not deploy AWS.

TASK-014 adds a Standard workflow foundation, defensive validation, conditional
start acknowledgement and stream/HTTP/operator recovery (ADR-017). TASK-015 now
creates the review and waits for a trusted callback (ADR-018). AWS live
acceptance remains deferred. See docs/runbooks/workflow-recovery.md for recovery.


TASK-015 adds retry-safe review/checklist creation, atomic REVIEW_PENDING/audit/outbox,
backend-only callback tokens, and reviewer/admin GET /reviews and /reviews/{taskId}.
GSI1 available/mine queues use scoped cursors and current assignment checks.
TASK-016 implements claim/start/check writes; TASK-017 adds decisions/finalization.
See docs/verification/TASK-015.md. Local implementation does not deploy AWS.


TASK-016 implements POST review claim/start and PUT checklist result. Conditional
transactions prevent competing claims, restrict mutations to the assigned subject
(including admins), and record IN_REVIEW/audit/ReviewStarted together. Checklist
updates preserve tokens and use optimistic versions; retries avoid duplicate effects.
See ADR-019 and docs/verification/TASK-016.md. TASK-017 adds decision/callback delivery.


TASK-017 implements POST review decision with UUID idempotency, persisted callback
retry and three guarded workflow finalization branches. Task tokens remain backend
only; technical failures retain review history. See ADR-020 and
docs/verification/TASK-017.md. TASK-018 owns information-request/resubmission E2E.
No cloud resources are deployed by task completion or GitHub publication.


TASK-018 verifies replacement and additive-document resubmission through a second
review to APPROVED, preserving old history. From backend, run:

    .venv/Scripts/python.exe -m pytest tests/integration/test_resubmission_e2e.py -q

This uses production handlers with Moto and a workflow service double. Browser
upload signatures, hosted orchestration and AWS IAM/JWT remain TASK-021.
See docs/verification/TASK-018.md. Next: TASK-019 domain notifications.


TASK-019 adds four domain email templates, custom-bus notification rules, queue/
DLQ and an isolated leased worker. Delivery defaults disabled until approved
notification_email_config supplies sender/reviewer addresses and an existing
verified SES identity. Local testing never sends real email. See ADR-021,
docs/runbooks/notifications.md and docs/verification/TASK-019.md.


TASK-020 adds safe JSON/correlation logging, DocFlow EMF metrics, active platform
tracing, a read-only pending-work monitor, alarms and an operations dashboard.
See [operations runbook](docs/runbooks/operations.md) and [ADR-022](docs/adr/022-operational-observability.md).
Alarm actions default to console-only. Deployment and real cloud validation remain
TASK-021 and require explicit approval; a GitHub push does not deploy resources.
