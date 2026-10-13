# ADR-018 - Callback review creation and authorized queues

Status: Accepted
Date: 2026-09-17
Task: TASK-015

Keep Case/Task/CHECK/GSI1 key formats. Task IDs are deterministically
t_{caseId}_{attempt}, allowing validated base-table lookup without a new index,
Scan or user-supplied partition. IDs are identifiers, not authorization credentials.
Review creation requires matching original submission/execution, PROCESSING and
unchanged template/revision. Priority NORMAL; dueAt is first submission time +48h
(initial operational default, separate from the 14-day callback technical ceiling).

Preserve the accepted 98-check template limit. First prepare all NOT_REVIEWED
skeletons using at most 98 conditional inserts plus a guarded Case ConditionCheck.
Identical preparations resume after a crash. Checks have no public visibility until
a Review Task exists; failed preparations are retained for diagnosis, not TTL-deleted.
Then atomically publish Task, Case REVIEW_PENDING/version/GSI2, audit and
CaseReadyForReview outbox (four actions). All checks must already match their immutable
template skeletons. Future check writes require an existing task (TASK-016).
A retry finds the deterministic existing task before touching checks; it never resets
reviewer findings. Concurrent preparation/publication fails conditionally and retries.

ASL invokes lambda:invoke.waitForTaskToken with original submission, execution ARN,
backend-only task token, State.EnteredTime and State.RetryCount. Lambda returns only
taskId, while Standard waits. Same token is idempotent. Newer invocation generations
(UTC entered time then retry count) can conditionally replace tokens on the same
active task with audit, preserving findings/ownership/history; stale generations
cannot overwrite newer tokens. Equal generation/different token fails closed.
Automatic redrive is not added. Callback timeout goes to WORKFLOW_FAILED; it is not
retried as another 14-day wait. Failure handler now accepts REVIEW_PENDING and IN_REVIEW. Task
status may remain PENDING after failure, but queues filter against current Case;
TASK-017 owns terminal review lifecycle updates.

Reviewer/admin queues support scope=available (unassigned PENDING) and scope=mine
(current subject), optional status, limit 1-100, and scope-bound continuation.
GSI1 uses existing reviewer partition and TASK#status#DUE#dueAt#taskId ordering.
Each candidate is strongly re-read with Case state to exclude stale assignment/
failed active attempts before projection; assigned COMPLETED history remains visible.
Cursor may accompany an empty filtered page.
Cross-scope/principal cursors fail. No Scan or arbitrary owner selection.

GET /reviews/{taskId} permits admin, assigned reviewer, or unassigned PENDING review
while the Case is REVIEW_PENDING. Requester-only access denied. Assigned historical
review detail is allowed; another reviewer's task is hidden with 404. Available
review detail enables inspection before claim without widening the Case GET route.
Public task/case/document/check DTOs whitelist fields; no token, task execution ARN,
callback generation, DB keys or nested internal values. The existing submission response's
workflowExecutionId contract is preserved. Logs and events omit tokens.

CreateReviewTaskAndWait replaces FoundationComplete. On callback the intermediate
ReviewCallbackReceived terminal records no business decision; TASK-017 replaces
it with finalizers. TASK-016 owns claim/start/check mutation. No callback-send grant,
decision endpoint or fake approval in this task. Reuse centralized logs and existing
table/query IAM with new review_creator and review_query access modes; actual
AWS callback/IAM/GSI consistency is NOT RUN, TASK-021. No runtime dependency changes.

References:
- https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html
- https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html
