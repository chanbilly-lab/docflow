# ADR-019 - Assigned review commands and atomic findings

Status: Accepted
Date: 2026-09-17
Task: TASK-016

TASK-016 acceptance requires only the assigned reviewer to start/update. This
resolves the broader Admin=Yes cells in design section 14 for these two commands:
reviewer/admin may claim, but neither may bypass assignment for start/check updates.
Admin inspection remains unchanged. Decision authorization stays with TASK-017.

Claim requires current-attempt Case REVIEW_PENDING and task PENDING/unassigned.
The existing explicit DynamoDB NULL reviewerId and legacy absent attribute both
mean unassigned, resolving section 8.8's absent-only wording against ADR-018 rows.
Transaction checks Case state/version/attempt and changes Task ownership/status/
GSI1 with immutable audit. Different claimant gets 409 REVIEW_TASK_ALREADY_CLAIMED.
Same owner replay while still CLAIMED is a guarded no-op. No reassignment route.

Start requires assigned CLAIMED task/current REVIEW_PENDING Case. Atomically update
Task IN_PROGRESS/startedAt/GSI1, Case IN_REVIEW/version/GSI2, audit and ReviewStarted
outbox, source docflow.review, data taskId/attempt/reviewerId/startedAt. An assigned
IN_PROGRESS/IN_REVIEW replay returns the original startedAt with no second fact.
Other ownership is 403; stale/inactive state is 409. Conditional races return 409.

Checklist PUT requires assigned IN_PROGRESS task and same-attempt IN_REVIEW Case,
plus an existing bound skeleton (never upsert). result accepts NOT_REVIEWED, PASS,
FAIL, NOT_APPLICABLE. comment is null or at most 2000 characters; omitted clears it.
Reject unknown fields/invalid IDs/bodies. Atomically check Case and task ownership,
update result/comment/updatedBy/updatedAt and internal check version, increment
task checkRevision, and append audit. Per-check version rejects stale concurrent
writes even with equal timestamps. Identical result/comment replay uses guarded
checks and makes no mutation/audit. Comment text is never copied to audit/events/logs.

checkRevision starts implicitly at zero and increments only on changed findings.
TASK-017 must fence decision validation with this task aggregate revision when
checking checklist completeness. Existing Task/Check keys and public DTOs stay stable.
Callback token refresh changes only its own fields; commands never overwrite tokens.
Current Case state/attempt fences timeout, finalization and stale-attempt races.

HTTP routes use JWT and review-command-handler. Its table-only read and CASE-only
transactional Put/Update/ConditionCheck IAM cannot send callbacks or publish events.
CORS adds PUT. No new dependency, cloud deployment, decisions or notification consumer.
Real DynamoDB concurrency/JWT/IAM/event delivery remains NOT RUN, TASK-021.
