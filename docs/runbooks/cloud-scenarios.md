# TASK-021 live scenario worksheet

2026-09-29 update: five journeys have PASS evidence in TASK-021-20260929b-session.md.
The original "all NOT RUN" below describes preparation. ADR-028 now omits actual
>24-hour/14-day/literal 85-day waits from gating. Delayed procedures below are
archival, not instructions to retain resources overnight. Non-omitted clauses
still need evidence. See fast-cloud-acceptance.md.

All scenarios below are NOT RUN. This worksheet expands CLOUD_ACCEPTANCE.md;
the ledger remains authoritative and each clause needs its own observed result.
Automated journey success is only a subset. Record UTC time, source fingerprint,
sanitized IDs, expected/actual outcome and restoration result per clause. Keep raw
state, tokens, signed URLs, credentials and private log payloads out of evidence.

## Bounded first session

Use cloud_e2e.py only after approved deploy and verified SES sender/recipients.
It covers production SRP access/ID tokens, missing/invalid auth, seed replay,
requester isolation, missing/invalid documents, real conditional S3 PUT, validation,
approval/rejection, competing reviewers, decision replay, and replacement/additive
resubmission to second approval. The journal records checks actually reached;
an exception is FAIL, never completion. Do not rerun over an existing journal.

cloud_evidence.py records configuration observations, not behavioral PASS.
Use the following manual checks to close gaps, recording each ledger clause
separately. Fault injection needs reviewed exact resources, mutation and restoration
steps within session approval. No unbounded scans, queue purges or broad policies.

| Origin | Procedure and required observation |
| --- | --- |
| 002/003 | Inspect fresh Terraform inventory and actual Cognito/client/JWT configuration. Use an expired token and tokens from separately approved wrong issuer/client fixtures; assert rejection and no writes. Retain status/issuer metadata only, never tokens. |
| 004/005/006 | Invoke seed concurrently against synthetic versions; inspect exact audit count and immutable historical definitions. Exercise numeric version selection, multi-page and filtered-empty queries. Run every role/combined-group/cross-Case/removed-assignment case from TASK-006 with real JWTs; compare scoped Case/audit/outbox before/after denied writes and forced transaction failure. |
| 007/008 | Upload a raw browser Blob from each exact configured origin; inspect OPTIONS and actual PUT. Tamper each signed header independently, test overwrite, wait beyond 600 seconds and separately expire signing credentials. Race reservation/deletion/state changes; verify one audit, atomic rollback, immutable-state denial and retained bytes for tombstones. Never copy signed URLs into evidence. |
| 009/010 | Inspect actual source rule, queue policy, encryption, visibility and redrive settings. Send matching/nonmatching bucket/prefix events in disposable fixtures; observe routing. Replay duplicates, mixed batches, deleted-document events and expired/stale leases; compare version/hash and atomic completion. Inject one bounded poison fixture and observe five receives then DLQ, distinct from target delivery failure. Restore and review exact-message redrive. |
| 011/012 | Compare all eleven emitted types with schemas, exact bus ARN, stable IDs and DISPATCHED writes. Temporarily inject reviewed per-entry publish/mark failures; prove accepted-send replay and conditional marking, checkpoint/bisection, typed filtering and missing-bus failure. Test actual command-role PutEvents denial. Do not broaden production role IAM to make the test pass. Use the delayed procedure below for retention expiry. |
| 013 | Race same/different UUID submit and resubmit, replay after lost response/later state, and reuse across operations; assert one attempt and durable receipt. Race document reservation/delete/processor updates across paginated reads; force transaction conflict and verify no partial audit/outbox/receipt. Verify allowed headers and transaction-only IAM. |
| 014 | Inspect actual Standard name/input and ARN, retry running and closed starts. In approved fixtures inject lost start response and failed ARN save; exercise stream and targeted recovery with original identity. Test 85-day guard with synthetic old metadata (not a claim of elapsed 85 days). Force validation/revision races and failure-handler outage, then restore and recover with atomic failure evidence. |
| 015 | Observe callback wait and retried token replacement privately. Prepare a 98-check synthetic template, interrupt/retry preparation and race creators; assert one public task and complete checklist. Exercise queue pagination/GSI lag/stale assignment and inspect public HTTP/events/allowlisted logs for absence of token fields. Record IAM denial results; timeout remains separate below. |
| 016 | Extend automated claim race to same-owner retries, admin assignment restrictions, concurrent check versions and task revisions, finalization/timeout fencing. Compare GSI transitions and exactly one ReviewStarted/audit fact. Validate PUT CORS and CASE-only transaction permissions. |
| 017 | Race decisions/check updates with distinct UUIDs. Inject lost callback send/ack and generation refresh; replay the persisted winner only. Exercise expired/closed token handling without exposing token bytes. Verify each finalizer uses original context and commits task/Case/audit/outbox together; observe technical closure on actual timeout. |
| 018 | Compare prior task/check/audit/source snapshots before/after both second attempts. Inject duplicate and late prior-attempt messages; prove fresh task/checklist/execution and no cross-attempt mutation. Verify missing/pending rejection and same-key replay. |
| 019 | Confirm rules enabled, raw delivery, exact-rule/TLS policies and actual sender/recipient verification. Observe delivered test email plus SES acceptance; sender acceptance alone does not prove delivery. Test verified/enabled sub lookup, duplicate/expired leases and uncertain send receipt; Case state stays independent. Exercise five-receive DLQ and approved exact-message recovery. |
| 020 | Follow one correlation across HTTP/upload/workflow/decision, inspect safe EMF metrics and native X-Ray. Verify monitor pagination/zero gauges/read-only IAM. Inject bounded error/retry/pending/heartbeat/target failure and both DLQ conditions, observe each expected alarm then recovery. Inspect workflow failure/abort and actual timeout separately. Record console-only alarms unless separately approved SNS recipients/actions exist. |
| 021 | Prove remote state locking with a second concurrent plan attempt without force-unlock. Record exact versions/plans/hashes, every prior row, cleanup review, protection-only plan, delete-only plan and service-by-service remaining inventory. Hosted CI needs a real run; local checks are insufficient. |

## Delayed evidence and remaining time constraint

Streams retention: separately approve a 26-30 hour window, resource/cost ceiling,
mapping changes and restoration. Create one synthetic durable pending fact while
its exact mapping is disabled; record creation time/sequence privately. After more
than 24 real hours verify the original stream record is unavailable, restore the
mapping and use the existing exact-fact recovery runbook. Assert original event ID,
one business state transition and final dispatch. Repeat the workflow-start recovery
path as required. Stop if unrelated workload appears. A changed timestamp alone
does not prove actual Streams expiry.

Callback timeout: production ASL waits 1,209,600 seconds (14 days). A forced abort,
SendTaskFailure or shortened test definition does not establish that real timeout.
The initial four-hour session cannot close this criterion. Obtain a separately
approved duration/cost/cleanup plan, or an explicitly approved acceptance decision
before substituting a shorter-duration experiment. Keep the original criterion
NOT RUN until resolved. Do not leave resources running without approved retention.

## Cleanup and evidence

Follow cloud-acceptance.md. Add manual fixture provenance to the reviewed journal
before cleanup; the current helper accepts recorded attempts 1 and 2 only.
Any additional attempt needs explicit cleanup review, not relaxed wildcard deletion.
Preserve sanitized evidence and record restoration of fault injections first.
Inventory exact IDs through their service APIs after Terraform state empties.
Record retained state versions, backups, metrics/history and residual costs.
