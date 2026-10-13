# Cost model and retirement limits

> Privacy note (2026-10-14): account-specific billing/credit details and private support identifiers are withheld for public release. Historical technical outcomes are unchanged; redacted details are not live targets.

No permanent AWS application environment is required for this portfolio. The local
frontend demonstration and credential-free checks do not deploy AWS resources.
The owner requested AWS retirement on 2026-09-29; the exact completed/blocked
actions are in [retirement evidence](../verification/AWS-RETIREMENT.md).
The owner subsequently revoked retention of the state/history and two SYSTEM
backups. All 47 state versions, 12 delete markers and the bucket are now deleted.
AWS rejected manual deletion of both SYSTEM backups; they expire automatically
on 2026-11-03 and are retained at no additional cost under
[DynamoDB pricing](https://aws.amazon.com/dynamodb/pricing/). SES identity and the
shared API role remain. Subscription visibility is incomplete; do not describe
the whole project as fully emptied or on a free plan.

## What would create usage charges?

| Driver | Workload inputs to estimate before any new deployment |
| --- | --- |
| Lambda / HTTP API | Requests, memory × execution duration, retries and polling |
| DynamoDB | Reads/writes, transaction amplification, indexes, storage, PITR/backups |
| S3 | Document and state-version bytes × retention, requests and data transfer |
| Step Functions Standard | Executed transitions and retries per Case/attempt |
| EventBridge / SQS | Event size/count, polling, redelivery and fan-out |
| SES | Actual email sends, including ambiguous-acceptance retries |
| CloudWatch / X-Ray | Log ingestion/retention, metrics, alarms, dashboards and traces |

Estimate each service's billable units using its current selected-region rates;
sum usage plus retained storage and any subscriptions, then subtract only confirmed
applicable allowances/credits. Recheck rates before approval; there is no fixed
per-Case price in this document. Use the [AWS Pricing Calculator](https://calculator.aws/)
with ap-southeast-2. No calculator result or measured final bill is claimed here.

The previous successful session lasted about 37 minutes and created 189 Terraform
resources, then removed application resources. These are observed duration/resource
counts, not a cost quote. The USD 10 session allowance was contingency, never a
hard cap or statement of actual spend.

## Plan and residual billing

Account-specific billing/credit details are withheld for privacy; this does not establish free operation. AWS states that a paid plan
cannot be downgraded to a free plan; deleting resources does not change that plan.
See [AWS Free Tier FAQ](https://aws.amazon.com/free/free-tier-faqs/), checked 2026-09-29.
Free-tier eligibility is not a guarantee of a zero bill.

Deleting a versioned bucket requires removing all versions/delete markers, not just
current objects. Backups, retained state and subscription renewals need separate
inventory. Past usage and delayed billing can still appear after deletion. Savings
Plans visibility is blocked by the managed project's SCP; subscription/billing
completeness cannot be certified from the accessible resource APIs alone.

An AWS-managed Lambda KMS key remains service-managed. It cannot be scheduled for
deletion by us and has no monthly key fee; use may still incur charges. See
[KMS key types](https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html).
Managed access/service roles and a default event bus are not application workloads.

Review AWS Settings > Billing for invoices/spend status, and Support for Basic vs
Business Support+ or a renewing trial. The latter is organization-wide and must be
confirmed separately; do not infer its absence from empty Lambda/S3 inventories.
[Official support management](https://docs.aws.amazon.com/accounts/latest/reference/access-aws-support.html).
Do not create budgets, paid cost tooling or a new deployment merely to stop charges.
