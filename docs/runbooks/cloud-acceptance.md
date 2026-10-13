# TASK-021 operator acceptance and cleanup plan

> Privacy note (2026-10-14): private account/resource identifiers and personal home paths have been redacted for the public-release candidate. Historical outcomes are unchanged; placeholders are not live targets.

Current scope amendment: ADR-028 accepts user-approved long-duration omissions.
Those tests remain NOT RUN without gating completion; other criteria and explicit
AWS session authorization remain required. See fast-cloud-acceptance.md for the
prepared supplement. Older no-waiver language below is superseded only as stated
in ADR-028; no production timeout/retention or security contract changes.

Next-session amendment: [short-cloud-acceptance.md](short-cloud-acceptance.md)
sets a 90-minute target / 120-minute maximum proposal. The four-hour envelope
below is historical. A new deployment is not yet authorized.

Status: first approved deployment FAIL; application cleanup PASS.
See ../verification/TASK-021-20260929-session.md for current evidence.
Session task021-20260929a: 02:35:07-06:35:07 UTC (maximum four hours).
Profile: docflow-toolkit. Region: ap-southeast-2 (ADR-024).
Project: <REDACTED_AWS_ACCOUNT>, verified by STS via AWS MCP on 2026-09-29.
Account-specific billing/credit details withheld for privacy; this does not establish free operation. SES sending enabled, sandbox. One user-approved
email-address identity is now verified (GetEmailIdentity SUCCESS, 2026-09-29).
The test mailbox is saved only in ignored build/task-021/config.session.json.
Explicit consent was received for one verification message; verification is complete.
The private config contains the exact sender/reviewer/identity ARN. No SCP edits
are needed. The user approved this runbook's four-hour deployment, five synthetic journeys, fewer
than 100 notification attempts to the verified private-config mailbox, and scoped
cleanup on success or failure. Retain state bucket and SES identity. USD 10 is a
planning allowance, not a hard cap. Long retention/timeout tests remain excluded.

## Resource and time envelope for review

Proposed fresh dev environment: one DynamoDB table/two GSIs/Stream/PITR; one private
document bucket; one Cognito Lite pool/public SRP client/three groups; one HTTP API
and JWT routes; 13 Python Lambdas including notifications and monitor; one Standard
workflow; one custom domain bus; four SQS queues (two main/two DLQ); event targets,
scoped IAM; 15 log groups; approximately 29 alarms, one dashboard and at most 17
custom metric series under the current service-only dimension design.
The saved real plan is authoritative and may include more individual policy/
permission/configuration resources. Stop on updates/deletes or pre-existing state.
Bootstrap adds five Terraform resources for one protected state bucket.

Proposed initial session: up to four hours, five synthetic Case journeys, five
disposable identities, less than 100 KB synthetic PDF bytes, fewer than 100 email
attempts, no real customer data, no permanent online demo. Configure an already
verified SES identity and only user-approved test recipient mailboxes. SES sandbox
requires verified recipients; verification messages need separate explicit consent
if there is no existing identity. Alarm actions remain console-only unless an
approved existing SNS topic is supplied.

Sydney pricing lookup PASS via AWS Price List API (2026-09-29). First-tier
custom metrics USD 0.30/metric-month; standard alarms USD 0.10/alarm-metric-month;
standard custom log ingestion USD 0.67/GB. Verified product SKUs:
F52S8X9YS2XFUA7F, 9FZA8ZKS9CGQBUTK, VSJ57WXDQXM2VKQK.
With 17 custom series, up to 42 alarm metrics, four hours/730 hours per month
and at most 0.1 GB logs, the calculated subtotal is USD 0.118. This is a component
estimate, not the complete AWS bill. Budget a further USD 8 allowance for dashboard,
Lambda/API/DynamoDB/Streams/S3/SES/events/traces, requests, minimums and contingency;
these remaining components are allowances, not verified SKU-by-SKU prices.
Round the proposed four-hour planning allowance to USD 10, excluding tax and
currency conversion. No credits assumed; this is NOT an enforced cap. Stop and
review before extending the session, increasing load or generating larger logs.
Exact cost remains dependent on usage; no claim of guaranteed maximum billing.

Retained state versions (<10 MB intended) and requests remain chargeable after
cleanup. Confirm actual saved-plan counts and retention before approval.
Check spend status in AWS Settings > Billing and selected region in AWS Settings
> View all projects > Overview > Additional Info > Region.
Source: https://aws.amazon.com/cloudwatch/pricing/
Private raw pricing response: build/task-021/sydney-pricing.json.
Standard transition lookup returned no matching products; no transition-specific
price is asserted from that query.

Literal >24h stream-expiry recovery requires another approved retention window
(e.g. 26-30 hours) and another login/check-in. A real 14-day callback timeout cannot
fit in that window. Keep these rows NOT RUN; do not substitute mocks or silently
shorten production semantics. Before requesting a retention/test-configuration
exception, present the exact resources, costs and acceptance evidence it supplies.
The first short session alone therefore cannot make TASK-021 DONE.

## Local preparation commands

Use Python 3.13 and the existing backend virtual environment. On Windows substitute
backend/.venv/Scripts/python.exe for PY below, and the bundled Terraform/Node paths
if not on PATH. These local commands require no cloud authorization:

    py -3.13 scripts/dev.py check
    PY scripts/package_cases.py
    npm ci --ignore-scripts --prefix acceptance
    npm run check --prefix acceptance
    terraform fmt -check -recursive infra
    terraform -chdir=infra/environments/dev init -backend=false -input=false -lockfile=readonly
    terraform -chdir=infra/environments/dev validate
    terraform -chdir=infra/environments/dev test
    terraform -chdir=infra/bootstrap init -backend=false -input=false -lockfile=readonly
    terraform -chdir=infra/bootstrap validate
    terraform -chdir=infra/bootstrap test

Copy scripts/cloud_config.example.json to build/task-021/config.session.json.

For an approved later session reusing retained state, add `state_bootstrap_session`
with the original bootstrap session ID, retain its exact `state_bucket`, and use a
new application `session_id`. Skip bootstrap; see ADR-026. The helper verifies
owner/region/provenance and storage protections, keeps the same state key and
lock, and refuses existing managed application state. No state migration occurs.
Keep private config/plan/state/output/journals only under this ignored directory.
Refresh login locally with aws login --profile docflow-toolkit. Do not paste any key,
password, authorization code or token into chat. Fill the verified account,
unique session ID, exact bootstrap bucket name, requester test email and non-null
notification sender/reviewer/SES identity configuration. No secrets belong in config.

    PY scripts/cloud_session.py --config build/task-021/config.session.json preflight

Read-only preflight confirms identity and conservative Lambda headroom. Fresh
plan/apply repeat the headroom check; cleanup does not. It is not authorization.
Before bootstrap, use Lambda GetAccountSettings and GetFunctionConcurrency to
verify capacity for configured reserved concurrency. The first session failed:
regional total=10 and AWS minimum unreserved=10 cannot accommodate the monitor
reservation of 1. Stop before resource creation until an approved quota/configuration
resolution exists; do not silently remove the bound.

Before bootstrap, inspect existing names/tagged resources and current local/remote
state. Never adopt pre-existing data into a disposable environment. Back up private
state and restrict its filesystem access. Existing managed local state stops the
helper; review terraform init -migrate-state separately rather than overwrite it.

## Approved bootstrap and deployment

Only after explicit approval of the account/region/resource/test/cost/retention/
cleanup envelope, replace SESSION with the exact config session ID. Action flags
are operator acknowledgements, not a substitute for that approval.

    PY scripts/cloud_session.py --config build/task-021/config.session.json plan --action bootstrap --approved-action SESSION/bootstrap
    PY scripts/cloud_session.py --config build/task-021/config.session.json apply --action bootstrap --approved-action SESSION/bootstrap --plan-sha256 REVIEWED_HASH

Inspect the private plan and its safe summary first. Record the exact state bucket.
It has versioning, encryption, TLS/private-access enforcement and prevent_destroy.
Restrict operator access to its exact state key and .tflock; lock needs Get/Put/Delete,
state needs Get/Put and scoped ListBucket. Do not grant state access to application
Lambdas. Bootstrap state stays private locally; no cloud collaboration uses it.

    PY scripts/cloud_session.py --config build/task-021/config.session.json plan --action deploy --approved-action SESSION/deploy
    PY scripts/cloud_session.py --config build/task-021/config.session.json apply --action deploy --approved-action SESSION/deploy --plan-sha256 REVIEWED_HASH

The backend is remote before dev apply. Check account, creates-only plan, Lambda ZIP
hashes and no unexpected resource replacements. Each action needs its own saved
hash. Source/config/ZIP changes invalidate the review. The helper records exact
created IDs even after a partial deployment. Partial failure blocks automatic
retry; inspect its state/inventory privately and prepare a scoped recovery.
Do not delete the inventory, force-unlock or import resources to bypass guards.

## Run and record acceptance

    PY scripts/cloud_e2e.py --config build/task-021/config.session.json --approved-action SESSION/e2e
    PY scripts/cloud_evidence.py --config build/task-021/config.session.json

The first command sends approved test emails indirectly through actual workflows,
creates five users with SUPPRESS invitations and random in-memory passwords, seeds
the immutable template and runs the HTTP journeys. No private credential is saved.
It refuses to overwrite an existing fixture journal. A failure leaves identifiers
for inspection/cleanup. If tokens expire during a long manual investigation, stop
and reauthenticate privately; do not rerun setup against existing users blindly.
The second command is read-only configuration evidence; it never marks runtime PASS.

Automated subset: SRP/valid/missing/invalid/ID-token health; requester isolation;
missing documents; actual presigned PUT/create-only overwrite denial; actual async
validation; repeated submit/decision; simultaneous claim winner; approve/reject;
request-information with replacement/additive upload and fresh second task;
invalid PDF rejection. Both live service behavior and these scripts are NOT RUN
until executed on AWS. Python HTTP upload is NOT browser CORS evidence.

Use cloud-scenarios.md to complete every remaining matrix criterion. Preserve only
allowlisted evidence. Do not upload raw execution history, Terraform state or JWTs.
A short subset passing cannot change any broad matrix row to PASS until all its
listed checks have separate evidence.

## Approved cleanup, in stages

Before cleanup, export sanitized evidence and an encrypted/private backup of state
outside the disposable environment. Record intended retained state-bucket costs.
Confirm exact created IDs, fixture Cases/users/object keys and running executions.

    PY scripts/cloud_cleanup.py --config build/task-021/config.session.json
    PY scripts/cloud_cleanup.py --config build/task-021/config.session.json --execute --approved-action SESSION/fixture-cleanup

The first command is a preview. The second requires an unchanged reviewed target
list, recorded Cases/keys and session bucket tag. It stops only recorded running
attempts (1 or 2) and removes only recorded synthetic objects. It refuses unexpected
objects or versioning. Any manual/fault-injection fixtures need separately reviewed
journal additions with provenance; never widen scope to an entire unrelated bucket.

    PY scripts/cloud_session.py --config build/task-021/config.session.json plan --action unlock --approved-action SESSION/unlock
    PY scripts/cloud_session.py --config build/task-021/config.session.json apply --action unlock --approved-action SESSION/unlock --plan-sha256 REVIEWED_HASH
    PY scripts/cloud_session.py --config build/task-021/config.session.json plan --action destroy --approved-action SESSION/destroy
    PY scripts/cloud_session.py --config build/task-021/config.session.json apply --action destroy --approved-action SESSION/destroy --plan-sha256 REVIEWED_HASH

For partial-apply cleanup, the helper targets only the recorded DynamoDB/Cognito
protection resources. This prevents missing/tainted application resources from
being created or replaced during unlock. Saved-plan inspection still rejects all
other changes. A complete delete-only destroy plan must then match the captured
partial ownership inventory. Failed Terraform command logs are retained separately
under the ignored session directory, so later inventory reads cannot erase them.

Unlock may only change DynamoDB/Cognito deletion protection, preserving all other
attributes. Destroy is delete-only and must match the original resource inventory.
Cognito users disappear with this fresh pool; only test data in this fresh table
is removed. The state bucket is deliberately retained. Its later deletion needs
separate explicit scope including every object version and local backup retention.

Verify empty Terraform state AND service inventories: exact Lambda names, pool,
API, table, document bucket, queues, bus/rules, workflow, log groups, alarms/dashboard
and session IAM policies/roles no longer exist. Review provider-retained backups,
resource-policy remnants, metrics/traces/history retention and state versions.
CloudWatch metrics/Step Functions history can remain after resource deletion;
record actual service behavior and any chargeable retained item. A tag query alone
is not complete inventory proof. Later billing may lag; do not claim USD 0 from
an immediate cost query. No future billing automation is created without request.

TASK-021 stays IN_PROGRESS until all live criteria and approved cleanup pass.
GitHub completion publication happens only then; do not create a misleading
feat: complete TASK-021 commit for preparation-only work.
