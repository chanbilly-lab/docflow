# ADR-026: Reuse protected state storage across acceptance sessions

Status: Accepted for local operator implementation; cloud execution needs approval.
Date: 2026-09-29. TASK-021.

Extend ADR-023 with optional `state_bootstrap_session` in private session config.
It identifies the session that originally created the retained state bucket;
omission preserves the existing session-bound behavior. A new application session
still has its own unique session ID, approval flags, journal and resource tags.

The bucket must match the exact project/original-session naming convention. Before
backend initialization and fresh deploy apply, read-only S3 checks require the
expected owner, selected region, original Project/Purpose/AcceptanceSession tags,
enabled versioning, all four public access blocks and AES256 default encryption.
Failure stops without altering the bucket. This is not a comprehensive IAM/policy
audit; the original TLS policy and approved bootstrap remain required.

Preserve `dev/terraform.tfstate`, encryption and native S3 lockfiles. Never create
a new state key to conceal existing resources. Fresh plan inspection still rejects
any managed prior state; saved-plan/config/source checks and Terraform locking
remain in place. Reusing a bucket does not authorize adopting its application state.
No state migration, import, force-unlock, version deletion or bootstrap ownership
transfer. Bootstrap is rejected when configured to reuse another session's bucket.

This avoids proliferating retained buckets; existing versions and requests still
cost money. State remains retained after application cleanup. No production stack,
public API, business semantics or IAM policy changes. Real-service reuse remains
NOT RUN until the next specifically approved session.
