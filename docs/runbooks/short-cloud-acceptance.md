# TASK-021 shortened, cost-conscious acceptance plan

> Privacy note (2026-10-14): private account/resource identifiers and personal home paths have been redacted for the public-release candidate. Historical outcomes are unchanged; placeholders are not live targets.

2026-09-29 amendment: ADR-028 accepts user-approved long-duration omissions.
24-hour/14-day waits stay NOT RUN with omission reason and no longer gate DONE.
Earlier no-waiver language below is historical. Follow fast-cloud-acceptance.md
for prepared follow-up; other unverified criteria remain required.

## Concurrency-10 amendment (ADR-027)

User requested testing at quota 10. Set `acceptance_low_concurrency: true` in the
private session JSON; monitor shares unreserved capacity (-1), default remains 1.
Guard requires 10 available unreserved executions; the old 101 guard below applies
only to normal mode. Keep alarms/tracing/read-only scan bounds and retries.
Run five journeys sequentially, retaining the two-request claim race. This is
not a load test; throttling and overlapping monitor retries remain possible.

Concrete proposed session: project <REDACTED_AWS_ACCOUNT> / ap-southeast-2 / docflow-toolkit;
new application session; reuse <REDACTED_STATE_BUCKET> with
state_bootstrap_session=task021-20260929a and the same backend key, no bootstrap.
Same dev resource set below; target 90 minutes, maximum 120 including cleanup,
start cleanup by minute 60. Five synthetic cases/users, <100 KB documents, fewer
than 100 notification attempts only to the previously approved verified mailbox.
USD 10 allowance is planning contingency, not a guaranteed bill or hard cap.
On success/failure clean only the new session's fixtures/resources, including
reviewed DynamoDB/Cognito protection unlock. Retain state, SES and shared API
Gateway role. Stop on existing application resources or scope changes. No 24-hour
or 14-day waits. Obtain explicit new-session deployment/email/cleanup approval.
Do not duplicate/cancel the pending quota request or automatically change mode
if it is approved. This amendment supersedes waiting for quota increase as a
prerequisite for this opt-in mode; other acceptance criteria remain unchanged.

Date: 2026-09-29. Preparation only; no new deployment approval.
This supersedes the four-hour envelope for the next proposed session, not its
historical evidence or the full acceptance matrix. TASK-021 remains BLOCKED.

## Local first

Run application/contract tests, lint/type/build, provider-mocked Terraform tests,
fixture checks and packaging before starting a cloud window. Read-only identity,
plan and Lambda capacity checks precede Terraform initialization/creation. Repeat
capacity checks before fresh apply; cleanup is never blocked by this quota guard.

Current verified project: <REDACTED_AWS_ACCOUNT>, ap-southeast-2, docflow-toolkit.
STS/GetAccountSettings/GetAccountPlanState PASS: account-specific billing/credit details withheld for privacy;
total and unreserved Lambda concurrency both 10, function count 0.
The existing monitor reserves 1 (ADR-022), rejected by AWS in the first session.
No plan upgrade, purchased capacity or production concurrency change is proposed.

The local guard conservatively requires 101 unreserved executions, using AWS's
published floor of 100 plus the existing monitor reservation. The managed project
previously reported a floor of 10. This is a conservative operator guard, not a
claim that its actual floor changed. A documented project-specific alternative
requires a reviewed guard change. Passing is not a guarantee against quota races.

## Proposed short session after the blocker is resolved

Target 90 minutes; maximum approved envelope to request: 120 minutes, including
cleanup. This is an operator schedule, not an automatic timeout or billing cap.

| Elapsed time | Activity / stop rule |
| --- | --- |
| 0-20 minutes | Fresh plan review and deploy. On failure, start cleanup immediately; no repeated apply. |
| 20-60 minutes | Run existing five synthetic journeys sequentially, collect evidence. Start ten-minute signed-URL expiry check early so its wait overlaps other tests. |
| By 60 minutes | Stop starting test scenarios and begin cleanup even if some checks remain NOT RUN. |
| 60-90 minutes | Export sanitized evidence, fixture cleanup, protection-only unlock, delete-only destroy and independent inventories. |
| 90-120 minutes | Cleanup contingency only. Escalate incomplete cleanup immediately; never report automatic deletion or zero residual cost. |

Use the existing resource architecture (13 Lambdas, DynamoDB/GSIs/Stream/PITR,
private S3, Cognito Lite, HTTP API, Standard workflow, EventBridge, four queues,
15 logs, alarms/dashboard/tracing). Do not remove required security, audit,
reliability or observability checks to label the result free.
Keep five synthetic cases/five users/<100 KB PDFs, one approved verified mailbox
and fewer than 100 notification attempts. These are reviewed scope bounds, not
an implemented hard email/spending cap. Keep console-only alarms; add no SNS/SMS,
paid support, custom domain, provisioned concurrency, SnapStart or always-on demo.
Do not query paid Cost Explorer APIs merely to refresh this estimate.

The existing runbook's USD 10 allowance remains a conservative contingency for
review, not a new price estimate, purchase or hard cap. Do not assume charges
halve when duration halves: retained metrics/state/backups and delayed metering
remain. Confirm current pricing and saved-plan counts before deployment approval.
Fully local preparation avoids new application usage; AWS live acceptance is not
guaranteed free; account-specific billing/credit details are withheld for privacy. Existing retained
resources can still accrue charges. Check AWS Settings > Billing for spend status.

Reuse is now implemented locally under ADR-026. Set `state_bootstrap_session`
to the original bucket-creation session and keep `state_bucket` equal to that
session's exact bucket name. Use a new `session_id` for new application resources.
Skip bootstrap. Owner/region/tags/versioning/public-block/encryption checks run
before initialization and deploy apply. Preserve the original state key/lock;
any existing managed application state still stops a fresh plan. Actual reuse
remains NOT RUN until explicitly approved; do not bypass guards or create another
retained bucket merely to evade an existing-state error.
Keep the verified SES identity and shared API Gateway role as previously directed.
All test/deploy/cleanup commands remain those in cloud-acceptance.md with explicit
session approval and saved-plan checks. Approval for the first failed session does
not authorize this new session.

## Evidence that cannot fit

The >24-hour real Streams expiry and 14-day production callback timeout remain
NOT RUN. Shortened isolated probes could test recovery mechanics, but are not
equivalent evidence without an explicitly approved acceptance decision. No such
change is made here. Five journeys also do not cover the entire failure/IAM matrix.
Do not retain a running environment overnight to wait for these tests.

## Quota resolution

2026-09-29 execution update: user explicitly authorized the request below.
RequestServiceQuotaIncrease PASS, desired 1000; ID
67f8f7f522db429088c4d6029ac575cc5kM3zDV3. Latest state CASE_OPENED, AWS case
179065969600893; effective total/unreserved still 10/10. Read this existing
request on continuation; do not submit another or buy support. Only this quota
request is authorized, not the next deployment. The proposal below is historical.

Preferred next review: request standard Lambda regional concurrency quota of
1000 through Service Quotas, if supported for this managed project. This changes
a quota ceiling, not provisioned capacity, and leaves reservation 1 unchanged.
Do not submit until explicitly authorized; approval is not guaranteed. If the
managed experience denies it, report that result without buying support/upgrading
features or changing architecture. Any unreserved-monitor alternative requires
an ADR addressing overlap/scan bounds; it is not implemented implicitly.

Sources: [Lambda concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html),
[Lambda pricing](https://aws.amazon.com/lambda/pricing/).
