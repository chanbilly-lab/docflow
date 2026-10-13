# Design rationale and trade-offs

| Choice | Benefit | Cost or limitation |
| --- | --- | --- |
| Presigned private S3 PUT | File bytes bypass API/Lambda; conditional creation limits overwrite | Short-lived capability must not leak; browser CORS and signed headers need real tests |
| DynamoDB single-table transactions | State, audit and outbox intent commit atomically | Keys/access patterns require planning; GSIs are eventually consistent; no arbitrary joins |
| Transactional outbox | Avoids a database/event dual-write gap | Publication is at least once; stream expiry requires durable pending-work recovery |
| Step Functions Standard | Explicit durable human-review lifecycle and callback wait | More IAM/state semantics and transition charges; token secrecy/recovery need care |
| EventBridge facts plus SQS consumers | Notifications/processing fail independently of core commands | Duplicate delivery, leases, partial failures, retry/DLQ and operator tooling are necessary |
| Conditional claims and persisted decisions | Concurrent reviewers cannot both own the same active task | Conflicts require refresh/retry; API acceptance is not immediate Case finalization |
| Immutable templates and attempts | Review history remains explainable after resubmission | Additional storage and more complex pagination/state fencing |
| Serverless and short-lived dev environments | No always-on application servers; reproducible disposable tests | Service quotas, cold starts, IAM and per-request/storage/observability costs remain |
| AI-free Project 1 | Deterministic baseline isolates workflow correctness | No automated semantic document interpretation |

The outbox does not make the entire system exactly once. Consumer idempotency limits
repeat business effects; a crash after SES acceptance but before saving completion
can still repeat email. Native X-Ray is sampled, and event counters are observations
rather than authoritative accounting. Read committed Case/audit state for truth.

The concurrency-10 acceptance session used an explicitly unreserved monitor. It
proved low-volume journeys could run, not monitor isolation or throughput under
load. Production defaults and the temporary deviation are distinguished in
[ADR-027](../adr/027-low-quota-acceptance.md).

Alternatives intentionally deferred include always-on relational/container stacks,
websocket updates and AI/RAG. They need workload evidence and an approved ADR,
not additional services solely to expand a portfolio diagram. Durable decisions
and their reasoning are indexed in [DECISIONS](../DECISIONS.md).
