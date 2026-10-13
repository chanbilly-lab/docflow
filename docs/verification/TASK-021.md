# TASK-021 verification - current evidence through 2026-09-29

> Privacy note (2026-10-14): private account/resource identifiers and personal home paths have been redacted for the public-release candidate. Historical outcomes are unchanged; placeholders are not live targets.

Current status: BLOCKED (remaining non-omitted acceptance; short-session cleanup PASS).
ADR-028 omits long elapsed-time checks at the user's request; they stay NOT RUN,
not completion blockers. Current preparation: [fast supplement](TASK-021-FAST.md).
Current profile/region: docflow-toolkit/ap-southeast-2.
Latest evidence: [2026-09-29 low-quota session](TASK-021-20260929b-session.md).
ADR-027 opt-in unreserved monitor permits testing with total concurrency 10.
Deployment, five live journeys and cleanup PASS; full matrix remains incomplete.
Earlier sections below are dated historical evidence and superseded where they
conflict with the latest session record. Default reserved-monitor mode still
requires sufficient quota; low-quota evidence does not prove default isolation.
Base: dffde6aef5ffaf81153336d5f347c356baadd8a0 (TASK-020).

## Results

| Command/check | Result | Evidence |
| --- | --- | --- |
| py -3.13 scripts/dev.py check | PASS | Exit 0; 531 backend tests in 524.88s, including 21 new operator guards; Ruff lint/82 formatted files; mypy 73 + 8 files; frontend format/lint/1 test/TypeScript/Vite; Python sdist/wheel. Private local build/task-021-check.log. |
| backend/.venv/Scripts/python.exe -m pytest backend/tests/unit/test_cloud_session.py -q | PASS | 21 guard tests; account/action, fresh-only plan, exact inventory, cleanup targets, fingerprint, token-field and upload-host guards, immutable check-only CI. |
| terraform fmt -check -recursive infra | PASS | Terraform 1.14.9. |
| terraform -chdir=infra/environments/dev init -backend=false -input=false -lockfile=readonly; validate; test | PASS | AWS 6.64.0; 40 mocked plan tests; build/task-021-terraform.log. No service calls. |
| terraform -chdir=infra/bootstrap init -backend=false -input=false -lockfile=readonly; validate; test | PASS | One mocked protection/encryption/private-state test; build/task-021-bootstrap.log. |
| npm ci --ignore-scripts --registry=https://registry.npmjs.org; npm run check (acceptance/) | PASS | Locked 22 packages installed; node --check auth.mjs; Node 22.23.2, Cognito SDK 6.3.20. |
| git diff --check | PASS | No whitespace errors. |
| AWS STS caller identity | BLOCKED | docflow-dev login expired; no credentials or tokens printed. |
| Hosted GitHub CI | NOT RUN | Changes remain local; unfinished task is not published as complete. |
| Terraform real plan/apply, live journeys, IAM/delivery/alarms and cleanup | NOT RUN | Await verified account/SES inputs and explicit approved session. Every CLOUD_ACCEPTANCE.md row remains NOT RUN. |

Initial local checks exposed HCL formatting, a test type annotation and script
mypy import-path problems; corrected before the PASS runs above. Registry lookup
did not supply SDK 6.3.21; the lock pins available 6.3.20. No unresolved local
verification failure is concealed by these final results.

## Limits and next evidence

Read ../runbooks/cloud-acceptance.md for proposed resources/costs and staged cleanup,
and ../runbooks/cloud-scenarios.md for scenario-specific evidence. The automated
harness covers a subset; manual fault/IAM/concurrency/retention rows are not claimed
automated or passed. Public-client tokens expire; stop/re-auth privately if a live
run outlasts token validity. Existing journals are deliberately not blindly replayed.

A four-hour session cannot establish actual >24h Streams expiry or the production
14-day callback timeout. No criterion is waived. Approve separate retention windows
or an explicit acceptance decision before substituting evidence. Retained protected
state storage has residual charges; it is not included in application teardown.

No completion commit or push was made under AGENTS.md 7.1. TASK-022 remains TODO.

## Exact changed files

- `.github/workflows/pull-request.yml`
- `.gitignore`
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `acceptance/README.md`
- `acceptance/auth.mjs`
- `acceptance/package-lock.json`
- `acceptance/package.json`
- `backend/pyproject.toml`
- `backend/tests/unit/test_cloud_session.py`
- `docs/CHANGELOG.md`
- `docs/CLOUD_ACCEPTANCE.md`
- `docs/DECISIONS.md`
- `docs/TECHNICAL_DESIGN.md`
- `docs/adr/023-guarded-cloud-acceptance.md`
- `docs/adr/024-selected-project-region.md`
- `docs/runbooks/cloud-acceptance.md`
- `docs/runbooks/cloud-scenarios.md`
- `docs/runbooks/ses-scp-access.md`
- `docs/tasks.md`
- `docs/verification/AWS-TOOLKIT-SETUP.md`
- `docs/verification/TASK-021.md`
- `docs/verification/TASK-021-20260929-session.md`
- `infra/README.md`
- `infra/bootstrap/.terraform.lock.hcl`
- `infra/bootstrap/main.tf`
- `infra/bootstrap/tests/state.tftest.hcl`
- `infra/environments/dev/health.tf`
- `infra/environments/dev/main.tf`
- `infra/environments/dev/outputs.tf`
- `infra/environments/dev/terraform.tfvars.example`
- `infra/environments/dev/tests/foundation.tftest.hcl`
- `infra/environments/dev/variables.tf`
- `infra/environments/dev/versions.tf`
- `infra/modules/auth/main.tf`
- `infra/modules/auth/variables.tf`
- `scripts/cloud_cleanup.py`
- `scripts/cloud_config.example.json`
- `scripts/cloud_e2e.py`
- `scripts/cloud_evidence.py`
- `scripts/cloud_session.py`

## 2026-09-29 login continuation

- aws login --profile docflow-dev: BLOCKED pending browser authorization callback;
  process started successfully and remains waiting (shell session 39316). This
  does not establish successful authentication. Local diagnostics are ignored.
- STS and SES read-only discovery for this retry: NOT RUN pending authentication.
- Deployment/email: NOT RUN; no such action authorized. No source code changed,
  so implementation checks above were not rerun.

## Authenticated preflight result

2026-09-29: Login and STS identity PASS for docflow-dev/us-east-1 (account ending 8998). SES GetAccount and ListEmailIdentities BLOCKED by explicit AWS Organizations SCP deny (<REDACTED_SCP_ID>). Verified identities, sandbox status and test mailbox remain unknown. Organization administrator action is required. No AWS policy changes, deployment or email performed.

- PASS: aws login --profile docflow-dev; aws sts get-caller-identity.
- BLOCKED: aws sesv2 get-account; aws sesv2 list-email-identities.
- NOT RUN: live deployment/E2E/cleanup; no credentials or tokens printed.
- No implementation changes; previous local checks not rerun.


## TASK-021 SCP remediation diagnosis - 2026-09-29

DescribeOrganization PASS: organization management account identified (ending 1268).
DescribePolicy BLOCKED: current member role cannot read <REDACTED_SCP_ID>. Only
docflow-dev is configured locally. Need authorized organization administrator
access/policy content before a scoped patch can be prepared. No policy changed.
See docs/runbooks/ses-scp-access.md (repository-relative) for diagnostic commands,
minimal-change constraints and an unsent administrator request. Task remains BLOCKED.

## Corrected project-region preflight - 2026-09-29

2026-09-29 Toolkit setup: AWS CLI 2.37.5 and uv 0.12.20 installed.
docflow-toolkit login/STS PASS, selected region ap-southeast-2; existing docflow-dev
region left unchanged. Official configure agent-toolkit PASS, 24 default skills
installed, catalog lists 110 skills, aws-mcp profile bound and original Codex config
preserved. New-experience rules appended to AGENTS.md without replacing the contract.
SES GetAccount/ListEmailIdentities PASS in ap-southeast-2: sending enabled,
production access false (sandbox), zero identities. No SCP changes, email or
deployment performed. MCP availability in a restarted Codex session is NOT RUN.

The prior us-east-1 deny remains historical evidence, not a requirement to edit
AWS-managed SCPs. Deployment scripts have not yet been migrated to ap-southeast-2.
No real acceptance criterion is waived; TASK-021 remains BLOCKED.

## 2026-09-29 selected-region verification

- PASS: 27 tests in tests/unit/test_cloud_session.py (1.41s), including 6 new
  region/profile/backend/upload rejection checks.
- PASS: Ruff lint; mypy 73 source/test files and 8 scripts.
- PASS: terraform fmt -check -recursive infra, dev/bootstrap validate;
  dev 41 and bootstrap 1 mocked plan tests.
- PASS: MCP STS GetCallerIdentity, Free Tier GetAccountPlanState, SES GetAccount
  and ListEmailIdentities. Account-specific billing/credit details withheld for privacy; sandbox/zero identities.
  Initial snake_case MCP operation names failed lookup; PascalCase retry passed.
- PASS: targeted Sydney CloudWatch Price List lookup and deterministic component
  calculation; see cloud-acceptance.md. Remaining service costs are allowances.
  Step Functions price filter returned zero products, not a zero price.
- PASS: git diff --check.
- NOT RUN: full application suite on this regional-only change; previous 531-test
  baseline remains dated 2026-09-28. Production handlers/frontend unchanged.
- NOT RUN: live deployment/runtime E2E, SES identity creation/email and cleanup.
  User provided mailbox in ignored config; explicit send authorization is pending.
- No completion commit/push. ADR-024/DEC-028 resolve the region inconsistency;
  no SCP changes. TASK-022 remains TODO.


## 2026-09-29 authorized SES verification

PASS: STS identity guard and SES GetEmailIdentity not-found check.
The MCP sandbox did not define documented ClientError; its catch failed after the
API reported NotFoundException. No write occurred in that failed read script.
PASS: one separately executed CreateEmailIdentity after explicit user consent.
VerifiedForSendingStatus=false; verification completion is NOT RUN pending user
link click. No application deployment or test send; mailbox stays outside Git.


## SES verified result - 2026-09-29

PASS: GetEmailIdentity reports SUCCESS and VerifiedForSendingStatus=true after
the approved verification request. Private session config contains sender, reviewer
and exact identity ARN. No test email or deployment. Session approval pending.
