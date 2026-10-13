# Terraform dev foundation

> Privacy note (2026-10-14): account-specific billing/credit details and private support identifiers are withheld for public release. Historical technical outcomes are unchanged; redacted details are not live targets.

TASK-002 through TASK-020 define the serverless backend. A short real acceptance
session deployed and cleaned application resources on 2026-09-29. The owner then
skipped remaining TASK-021 checks and requested retirement; see
[current inventory and blockers](../docs/verification/AWS-RETIREMENT.md).
The published documentation does not authorize a new apply. Some TASK-021 operator
tools and infrastructure refinements remain in the local unfinished workspace.

## Configuration

| Component | Dev configuration |
| --- | --- |
| Terraform | 1.14.x; local verification and CI use 1.14.9 |
| AWS provider | >=6.64.0, <7.0.0; lockfile selects 6.64.0 |
| Region | `ap-southeast-2`, restricted selected project region (ADR-024) |
| State | Partial S3 backend; protected bootstrap and native lockfile (ADR-023) |
| Table | `docflow-dev`, PAY_PER_REQUEST |
| Primary key | String `PK` / `SK` |
| Indexes | `GSI1`: GSI1PK/GSI1SK; `GSI2`: GSI2PK/GSI2SK; String keys, ALL projections |
| TTL / Stream | `expiresAtEpoch`; `NEW_AND_OLD_IMAGES` |
| Recovery | PITR and deletion protection enabled by default |
| Encryption | Default DynamoDB AWS-owned encryption; no customer-managed key |
| Logs | Successful acceptance configuration: 13 Lambda, one HTTP API and one workflow group; 14-day retention |
| Tags | `Project=docflow`, `Environment=dev`, `ManagedBy=terraform`, resource `Name` |

Only key attributes are declared in the table schema. Item PK/SK value formats remain
those in Technical Design section 6. Do not assign expiry to audit/business items by
default. Future APIs must filter internal fields, including workflow tokens, from
GSI/query results.

Log groups are owned exclusively by `observability`:

- `/aws/lambda/docflow-dev-{function}`, including the scheduled monitor.
- `/aws/apigateway/docflow-dev-api`.
- `/aws/vendedlogs/states/docflow-dev-case-review-workflow`.

Lambda/API/workflow modules reuse root log group outputs. Queues, stream publishers,
workflow, notification and operations modules were added by subsequent tasks.
Configuration existence alone does not prove runtime IAM, recovery or alarm behavior.

## Credential-free verification

Install [Terraform 1.14.9](https://releases.hashicorp.com/terraform/1.14.9/) or a
compatible 1.14.x patch. Initial provider download requires network access.
From the repository root, with Terraform on PATH (PowerShell or POSIX shell):

```sh
python scripts/package_health.py
python -m pip install -r backend/requirements-runtime.txt
python scripts/package_cases.py
terraform fmt -check -recursive infra
terraform -chdir=infra/environments/dev init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/environments/dev validate
terraform -chdir=infra/environments/dev test
```

On this Windows workstation, replace `terraform` with
`./.tools/terraform-1.14.9/terraform.exe`. This ignored local binary was verified
against HashiCorp's SHA256 manifest; no global installation is required.

Plan-only tests use a mocked AWS provider to check composition, DynamoDB contracts,
retention overrides and invalid inputs. Counts depend on the source revision;
the latest local workspace recorded 42 dev tests. No AWS credentials are required
or AWS APIs called. These checks do not
establish deployability or IAM correctness. PR CI runs the same four commands as a
separate job with `contents: read` permissions.

Application checks remain `py -3.13 scripts/dev.py check` on Windows. Terraform checks
are separate and do not require application dependencies.

## State and controlled deployment

TASK-021 uses a partial S3 backend. Credential-free checks use init -backend=false.
The operator tool bootstraps a private, encrypted, versioned, prevent-destroy state
bucket and supplies exact bucket/key/region/account plus use_lockfile=true.
Bootstrap state stays in the ignored private session directory; application state
is remote before deployment. Neither backend is configured by a normal Git push.

Follow [the session runbook](../docs/runbooks/cloud-acceptance.md) for approval,
saved-plan review, deployment, fixtures and scoped cleanup. Existing local managed
state blocks the fresh-session tool; back it up and review explicit migration
separately. Never start empty state over existing resources. AWS credentials remain
outside source/config logs. DynamoDB and Cognito protection default to enabled;
only the approved protection-only stage may disable them before verified cleanup.

## Dependency updates

The dev lockfile pins AWS 6.64.0 with official Windows/Linux checksums.
`init -lockfile=readonly` detects unintended lock changes. For an intentional provider
update, run `init -backend=false -upgrade`, then regenerate platform hashes:

```sh
terraform -chdir=infra/environments/dev providers lock -platform=windows_amd64 -platform=linux_amd64
```

Review the lock/configuration diff and rerun Terraform checks before committing.
Add a platform when needed. Child modules do not maintain separate lockfiles.

## Design and evidence

- [Technical Design](../docs/TECHNICAL_DESIGN.md), sections 6, 18 and 18.1.
- [ADR-005](../docs/adr/005-dev-terraform-foundation.md).
- [TASK-002 verification](../docs/verification/TASK-002.md).
- [DynamoDB provider documentation](https://github.com/hashicorp/terraform-provider-aws/blob/v6.64.0/website/docs/r/dynamodb_table.html.markdown).
- [Log group provider documentation](https://github.com/hashicorp/terraform-provider-aws/blob/v6.64.0/website/docs/r/cloudwatch_log_group.html.markdown).
- [Terraform provider mocking](https://developer.hashicorp.com/terraform/language/tests/mocking).
- [Terraform local backend](https://developer.hashicorp.com/terraform/language/backend/local).

## TASK-003 local health path

Build build/health.zip with Python 3.13 before every Terraform plan/test and after
handler changes. CI also builds the ZIP before its Terraform checks. Outputs now
include user_pool_id, user_pool_client_id and health_endpoint. Cognito Lite uses an
SRP public client, invitation-only users and the three domain groups.

AWS authentication passed with docflow-dev in us-east-1 on 2026-09-15. Account-specific billing/credit details are withheld for privacy; this does not establish free operation. Do not run apply or create test users until the
user authorizes cloud deployment. No real plan/apply/live HTTP checks have run.
The existing on-demand database/PITR, logs and request-based services may incur
usage/storage costs; throttling is not a hard cost limit.

Before eventual deployment, refresh identity, inspect a real plan and verify
provider support for the local AWS CLI login session (or a separate external
credential_process profile, without exporting credentials to logs). Preserve state.
See ADR-006 and docs/api/README.md for authentication. ADR-007 assigns live acceptance
to TASK-021 (docs/CLOUD_ACCEPTANCE.md); local DONE no longer waits for AWS deployment.

## TASK-005 Case API composition

The dev composition retains module.health as the case-query-handler Terraform address
and adds module.case_command. Both use build/cases.zip. Query dispatches health plus
Case GET routes; command handles POST /api/v1/cases. Four new scoped JWT routes reuse
the existing HTTP API and central log groups. No log groups/table/indexes are added.

Build with Python 3.13 and pinned requirements-runtime.txt before Terraform checks.
The packager includes runtime distributions and application sources deterministically;
the isolated ZIP-load test requires no workstation site-packages. CI builds both ZIPs.
On this Windows workstation use backend/.venv/Scripts/python.exe.

Query permissions are table/index GetItem/Query only. Command has table reads and
CASE#-partition PutItem restricted to TransactWriteItems through EnclosingOperation.
There is no UpdateItem/DeleteItem/Scan/EventBridge permission. Both use 10-second
timeouts; Case API integrations allow 15 seconds. Real IAM evaluation remains NOT RUN.

Run fmt/validate and all 16 provider-mocked plan tests. No deployment is authorized.


TASK-007 adds the storage module and document-command-handler, reusing its existing
log group and build/cases.zip. Build that ZIP after code changes before validation.
Dev browser_origins defaults to localhost and 127.0.0.1 on port 5173; replace with
exact approved origins before cloud acceptance. No wildcard origins.

The bucket uses a generated suffix, four public-access blocks, disabled ACLs,
SSE-S3, TLS, conditional creation, signature-age policy and PUT-only CORS.
force_destroy=false; no automatic object expiry/deletion. Document IAM allows
base-table reads and Case-scoped transactional PutItem/ConditionCheckItem/UpdateItem plus
S3 PutObject only under cases/*/documents/*/v1/source. No object read/delete/list.
TASK-009 now owns EventBridge bucket notification configuration in dev composition.
The current suite has 24 mocked plan runs; real S3/IAM behavior remains TASK-021.


TASK-008 adds the scoped JWT DELETE document route and DELETE browser CORS.
Document-command IAM now includes UpdateItem only within TransactWriteItems on
CASE# partitions, alongside existing PutItem/ConditionCheckItem. S3 permissions
remain PutObject only; no physical object deletion or resource cleanup is enabled.
The 16 plan tests also assert the delete route, permission scope and CORS method.

## Document event pipeline (TASK-009)

Dev document_pipeline.tf owns the sole document-bucket notification configuration.
The document_pipeline module routes exact-bucket cases/ Object Created events
from the default bus into a standard SSE-SQS/TLS-only queue. Outputs expose main
queue ARN/URL and DLQ ARN for later consumer wiring. TASK-010 adds the Lambda mapping.

Main visibility/retention are 360 seconds/4 days, DLQ retention 14 days; polling
is 20 seconds and maxReceiveCount is 5. Rule-scoped SendMessage and queue-scoped
redrive permissions are asserted by tests. The untransformed AWS envelope is the
message body. EventBridge delivery retry is 24 hours/185 attempts with no target
DLQ; exhausted target delivery is not covered by the processing DLQ (ADR-012).

Run init with the existing lockfile, fmt -check, validate and all 24 mock tests.
No deployment is authorized. Include TASK-010's processor during consolidated
acceptance, since unconsumed messages expire after four days.

## Document processor (TASK-010)

Dev wires document_processor.handler.handler from cases.zip, its existing log
group, exact processing queue and document bucket. Lambda timeout is 60 seconds;
batch size 5, batching window 0 and ReportBatchItemFailures enabled. The worker's
120-second lease is shorter than 360-second visibility. IAM grants only queue
poll/delete/attributes, prefix GetObject/GetObjectVersion, scoped table GetItem and
transaction-only PutItem/ConditionCheckItem. No S3 writes or EventBridge grants.
Build the ZIP before Terraform checks. Local tests total 20 mocked plans. Real
service polling, IAM, timeout/redrive and delete races are TASK-021, NOT RUN.

## Outbox publisher (TASK-011)

Dev composes a 60-second outbox Lambda, exact stream IAM, custom-bus publish/describe
and CASE-partition GetItem/UpdateItem. ListStreams alone uses Resource * because
AWS does not support resource scoping for it. No S3 or command write grants.
Mapping uses TRIM_HORIZON, batch 10, partial failures, bisection and retries through
stream expiry. Filter: INSERT/MODIFY with NewImage OUTBOX/PENDING.

TASK-012 provisions docflow-dev-domain, uses its output ARN and enables mapping
in the Terraform configuration. Do not enable against a missing bus or use the
default bus. Consolidated deployment must include TASK-012. For >24-hour missed
delivery, durable PENDING rows need controlled replay (TASK-020/021), not simply a
stream restart. No TTL, new recovery queue, automatic replay or deployment added.
Build cases.zip then run readonly init/fmt/validate and all 24 mocked plans.

## Custom domain bus (TASK-012)

The domain_events module creates the custom bus and exports name/ARN; dev exposes
domain_event_bus_name/domain_event_bus_arn. Publisher environment/IAM reference
that actual ARN and mapping is enabled through resource dependency ordering.
No caller/account ARN construction remains. S3 rule/default-bus wiring is unchanged.
No cross-account/public policy, forwarding, archive or subscriber resources added.
Production notification subscriptions belong to TASK-019. New tap queues/rules exist
only in local tests. Run readonly init/fmt/validate and all 24 mocked plans.
No AWS deployment is authorized; resource existence and live IAM remain TASK-021.


TASK-013 adds scoped JWT submit/resubmit routes and Idempotency-Key browser CORS.
The Case command's transaction-only PutItem includes IDEMPOTENCY#case-submission;
processor UpdateItem is transaction-only and CASE-partition-only for documentRevision.
No Step Functions resources/grants yet (TASK-014), and no deployment is authorized.
Do not deploy the intermediate pending-start implementation before TASK-014.


TASK-014 completes the start foundation in module workflow and dev/workflow.tf.
STANDARD ASL invokes the validation/failure workers using existing centralized logs.
Case command receives the actual machine ARN and a filtered CASE/PENDING stream
mapping (independent of OUTBOX mapping). No domain event orchestration or callback
permissions. Worker writes are transactional; startup bookkeeping is conditional
CASE-only UpdateItem. Payload logging is disabled. Log-delivery administrative
actions require wildcard Resource, while Lambda invocation is exact-resource.
TASK-015 replaces FoundationComplete with callback review waiting; TASK-017 adds
business decision finalization before full-product deployment. Recovery instructions: docs/runbooks/workflow-recovery.md.


TASK-015 wires workflow-create-review-task (60 seconds) and review-query-handler
to existing centralized log groups. TASK-017 extends state-role invocation from three to four workers.
review_creator reads table and writes CASE-scoped transactions including ConditionCheck;
review_query is read-only on table/GSI1. New GET review routes use scoped Cognito JWT
and route-specific Lambda invocation. No SendTaskSuccess/Failure or direct event
permission is granted. Callback state timeout is 14 days; operational dueAt is 48h
after submission. Actual callbacks, IAM and consistency remain NOT RUN / TASK-021.


TASK-016 wires review-command-handler to its existing central log group, using
review_command access: table reads and CASE-only transactional Put/Update/
ConditionCheck; no index, callback, event publication or S3 grants. Three scoped JWT
routes cover POST claim/start and PUT checks; browser CORS includes PUT.
The ASL remains waiting; decision/callback APIs and grants belong to TASK-017.


TASK-017 adds the fourth workflow worker, workflow-finalize-case, and the decision
JWT route on review-command-handler. The ASL selects three guarded finalizers and
retains original execution identity on failure. Review command reads table Query
and has one callback action, states:SendTaskSuccess, Resource * because AWS does
not support ARN scoping for that action. No SendTaskFailure or event publish grant.
The policies are local configuration; actual IAM/callback testing is NOT RUN,
TASK-021. Terraform test uses mock_provider aws and creates no AWS resources.


TASK-019 notifications module owns standard notification queue/DLQ, two custom-bus
rules/targets and optional dedicated Lambda/IAM/SQS mapping. It reuses the central
notification log group. Null notification_email_config disables rules and omits
worker/mapping/IAM. Supply sender, reviewer, identity_arn only for the explicitly
approved session; the existing SES identity and sandbox recipients must already
be verified. No identity verification or email is sent by local tests.

Configured worker consumes only its queue, reads CASE/receipt rows, writes only
IDEMPOTENCY#notification-worker, resolves users on the exact Cognito pool, and
sends only via the exact SES identity/FromAddress. No business writes, publish,
S3 or workflow privileges. 60-second timeout/360-second visibility, batch size 1,
partial responses, 5 receives to 14-day DLQ; main retention 4 days.


TASK-020 operations module represents a five-minute read-only monitor, native
CloudWatch alarms, EMF alarms and docflow-dev-operations dashboard. observability
continues central log ownership (now 15 groups). All Lambda and Standard workflow
modules enable native X-Ray; no workflow payload logging. Build cases.zip first.
Monitor Scan IAM allows only its six status/time projection columns. At most
10,000 evaluated rows per snapshot; failure is detected by a missing heartbeat.
Existing approved SNS topics may be supplied in alarm_action_arns; the empty
default means console/dashboard alarms only, with no external notifications.
No live deployment, schedule, trace or alarm acceptance is claimed. TASK-021 must
include monitoring read/log/metric/trace costs and validate IAM/actions/redrive.
