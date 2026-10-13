# Local operation and cloud retirement runbook

## Default: local only

Use Python 3.13 and Node 22.12+ (22.x). From repository root:

```text
python scripts/dev.py bootstrap
python scripts/dev.py check
python scripts/dev.py dev
```

On Windows, `py -3.13` can replace `python`. Bootstrap needs package-download
access; tests/build use the installed local dependencies. The Vite console reports
the local preview URL. Reloading resets synthetic frontend state. Stop with Ctrl+C.
Do not interpret backend test doubles or Terraform mocks as real IAM/service proof.

## Cloud is not automatically resumed

TASK-021 remaining acceptance is skipped by owner decision. Pushing this repository
does not authorize deployment. Earlier private session JSON/plans can be stale after
retirement; never apply them or reconstruct state from an old snapshot automatically.
The uncommitted local acceptance helper workspace is distinct from this documentation
publication. A clean clone must not assume those scripts/configs are present.

For a future explicitly requested deployment: verify project/region and billing,
inventory actual resources, decide whether state exists or must be freshly bootstrapped,
reverify SES if its identity was deleted, then prepare a fresh plan and bounded
test/cleanup authorization. Never create empty state over extant resources, import
them silently, force-unlock, or reuse deleted resource identities as proof of ownership.

## Incident diagnosis for a future authorized environment

1. Confirm identity, selected region, live resource IDs and spend status before
   treating AccessDenied as an IAM defect. Stop on a project mismatch.
2. Correlate HTTP, Case, task and committed event identifiers. Keep tokens, raw
   workflow history, presigned URLs and document contents out of exported logs.
3. Check queue age/DLQ, pending outbox/start age and monitor heartbeat. Absent
   telemetry is not proof that work is healthy or queues are empty.
4. Distinguish invalid business documents from technical processing failure, and
   EventBridge target delivery from SQS consumer failure. Fix the cause before retry.
5. Review the exact failed event/attempt, replay identity and duplicates. Use only
   authorized targeted recovery; do not bulk edit Case state or purge queues.
6. After recovery verify committed state, audit, outbox and downstream effects;
   Lambda Invoke HTTP 200 alone does not establish success.

Detailed original procedures: [operations](../runbooks/operations.md),
[workflow recovery](../runbooks/workflow-recovery.md),
[notifications](../runbooks/notifications.md). Their original deployment assumptions
do not authorize execution now. Use docflow-toolkit/ap-southeast-2, not older
docflow-dev/us-east-1 examples, if a new environment is explicitly approved.

## Retirement checklist

Inventory actual resource services in the selected region and global dependencies.
Preserve local evidence, identify versions/backups/subscriptions, and delete only
authorized exact resources. Check every API result and re-list afterward; tag-index
entries can outlive deleted resources. Keep access-control foundations needed to
operate the project. Record uninspectable services and billing lag honestly.
The [retirement record](../verification/AWS-RETIREMENT.md) is the current outcome.
