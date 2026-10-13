# AWS retirement inventory - 2026-09-29

> Privacy note (2026-10-14): private account/resource identifiers and personal home paths have been redacted for the public-release candidate. Historical outcomes are unchanged; placeholders are not live targets.

## Final authorized deletion results

Owner explicitly revoked the earlier retention instruction and authorized permanent
deletion of the state bucket/all versions and both SYSTEM backups.

| Action | Result | Evidence |
| --- | --- | --- |
| Identity guard | PASS | STS project <REDACTED_AWS_ACCOUNT>; selected region ap-southeast-2 |
| DeleteObjects | PASS | 47 versions + 12 delete markers deleted, zero per-object errors; no multipart uploads |
| Empty-bucket verification | PASS | ListObjectVersions returned no versions/delete markers |
| DeleteBucket | PASS | <REDACTED_STATE_BUCKET> deleted |
| Final ListBuckets/ListTables | PASS | Zero buckets and zero DynamoDB tables |
| First DeleteBackup | BLOCKED | AWS ValidationException: SYSTEM backup cannot be manually deleted; expiry 2026-11-03T03:00:10.067Z |
| Second DeleteBackup | BLOCKED | AWS ValidationException: SYSTEM backup cannot be manually deleted; expiry 2026-11-03T06:17:19.113Z |
| Final ListBackups(ALL) | PASS | Both SYSTEM backups still AVAILABLE; no USER backups |

The backup ARNs end in <REDACTED_BACKUP_ID_1> and
<REDACTED_BACKUP_ID_2> under this project's docflow-dev table. These are service
restrictions, not automatic approval review rejections. No further approval is
needed for the attempted actions, and repeated attempts will not resolve the limit.
AWS explicitly states deleted-table SYSTEM backups are retained for up to 35 days
at no additional cost: [DynamoDB pricing](https://aws.amazon.com/dynamodb/pricing/)
and [BackupSummary](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BackupSummary.html),
checked 2026-09-29. Earlier suggestions that these two backups might create ongoing
backup-storage charges are superseded by this verified finding.

Local code/evidence and GitHub were not deleted. SES identity/shared role unchanged.
No account-plan change was performed; account-specific details are withheld for privacy. Subscription/organization visibility gaps below remain; prior
usage can still be billed. No deployment, restore or project closure performed.
The following sections are historical and do not override these deletion results.

## Renewed cleanup request - 07:27 UTC

The owner again requested clearing paid AWS content. This is renewed cleanup
intent, but deletion of the specifically retained state/history and two backups
awaits the precise retention-reversal question sent in this turn. No writes ran.

- PASS: STS identity <REDACTED_AWS_ACCOUNT>; account-plan query executed; billing/credit details withheld for privacy.
- PASS: sole S3 bucket still has 47 versions, 12 delete markers, 8,245,363 bytes;
  no multipart uploads. No state contents were printed.
- PASS: ListBackups(BackupType=ALL) finds the same two AVAILABLE SYSTEM backups.
  Default ListBackups returned none; it is not evidence of absent SYSTEM backups.
- PASS: refreshed lists find no Lambda, tables, Cognito pools, APIs, queues,
  workflows, default-bus rules, alarms, dashboards, regional logs, EC2 instances,
  EBS volumes/snapshots, EIPs, NAT gateways, VPC endpoints, RDS instances/clusters,
  EC2/RDS reservations, load balancers, ECS/EKS clusters, ECR repositories,
  EFS filesystems or Secrets Manager secrets.
- PASS: refreshed CloudFront, Route 53 hosted zones, regional/global WAF,
  us-east-1 logs, Backup vaults, SNS topics, Scheduler schedules, CloudTrail
  trails/event data stores are empty.
- BLOCKED: FSx and Savings Plans reads explicitly denied by SCP <REDACTED_SCP_ID>.
- BLOCKED: browser control failed with trusted Node process exit; Support and
  Marketplace subscriptions cannot be verified through the UI in this turn.
- NOT RUN: deletions, subscription cancellation, project closure, paid billing
  queries and organization-wide resource inventory. This is not a zero-bill audit.

The earlier results below are historical, with retention clarification now pending.

Scope: accessible DocFlow project <REDACTED_AWS_ACCOUNT>, selected region ap-southeast-2;
global CloudFront and allowed us-east-1 Logs/WAF dependencies also checked.
User requested all deployments/paid content cleared, free plan if possible, and
TASK-022 after skipping TASK-021. Local source/evidence are retained.

## Results so far

Final user choice: retain all specifically listed items and complete TASK-022 only.
This supersedes the earlier blanket cleanup request. No deletion is authorized
now; no blocked deletion was retried. User has not checked the Support page.

| Check/action | Result | Observation |
| --- | --- | --- |
| Identity and plan read | PASS | Correct project; account-specific billing/credit details withheld for privacy |
| Paid-to-free change | BLOCKED | AWS does not support downgrading paid to free; no change attempted |
| Application inventory | PASS | No Lambda functions, DynamoDB tables, Cognito pools, HTTP/REST APIs, SQS queues, state machines, custom buses/rules, alarms, dashboards or log groups |
| Compute/storage inventory | PASS | No EC2 instances/EBS/snapshots/EIPs/NAT gateways/VPC endpoints, RDS instances/clusters, ECS/EKS clusters, ECR repositories, EFS file systems, secrets or load balancers |
| Global/other inventory | PASS | No CloudFront distributions, Route 53 hosted zones, WAF ACLs, us-east-1 log groups, Backup vaults, SNS topics or Scheduler schedules |
| EC2/RDS reservations | PASS | None returned |
| Savings Plans inventory | BLOCKED | DescribeSavingsPlans explicitly denied by managed SCP; absence not established |
| Extended service inventory | PASS | No CloudTrail trails/event data stores, SageMaker endpoints/notebooks, OpenSearch domains, ElastiCache clusters, Redshift clusters, Kinesis/Firehose streams or ACM certificates |
| FSx inventory | BLOCKED | DescribeFileSystems explicitly denied by managed SCP; absence not established |
| Support subscription | NOT RUN | Browser automation failed to start; user has not checked the Support page |
| State bucket deletion | NOT RUN | Automatic review initially rejected deletion; user then explicitly chose retention |
| SYSTEM backup / SES deletion | NOT RUN | Automatic review initially rejected deletion; user then explicitly chose retention |
| API Gateway shared role | NOT RUN | User explicitly chose retention |

State bucket: <REDACTED_STATE_BUCKET>. ListObjectVersions
returned 47 versions and 12 delete markers, 8,245,363 version bytes, keys limited
to dev/terraform.tfstate and its lock file. Multipart-upload list empty. No raw
state contents printed. The attempted deletion call was rejected before execution.

Two docflow-dev SYSTEM backups remain AVAILABLE; recorded expiry times are
2026-11-03 03:00:10 UTC and 06:17:19 UTC. Reported zero-size metadata does not prove
absence of synthetic data. One verified SES email identity remains. Earlier tag
index results still referenced deleted Cognito pools; direct ListUserPools was
empty, so stale tag references are not counted as live deployments.

Thirteen IAM roles include managed access/organization roles and the previously
retained API Gateway service-linked role. One KMS key has KeyManager=AWS and the
description of the default Lambda key. These findings do not justify deleting
managed login roles or changing key policies. Default service infrastructure and
service-managed histories are not application deployments.

Initial load-balancer inventory used an unsupported MCP service spelling; corrected
elbv2 and elb reads both succeeded with empty results. Reads do not cover every AWS
service/subscription/other project. No Cost Explorer paid query or new cost service
was enabled, no project closure, plan upgrade or deployment was performed.

Final bills may contain earlier usage or delayed postings. Review AWS Settings >
Billing and Support. [AWS paid/free FAQ](https://aws.amazon.com/free/free-tier-faqs/)
confirms no downgrade; [support management](https://docs.aws.amazon.com/accounts/latest/reference/access-aws-support.html)
describes separately cancelable Business Support+. Resource cleanup cannot erase
already incurred charges or prove a zero future bill while retained items/visibility
gaps remain.
