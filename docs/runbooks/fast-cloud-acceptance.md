# TASK-021 fast follow-up after duration omissions

> Privacy note (2026-10-14): private account/resource identifiers and personal home paths have been redacted for the public-release candidate. Historical outcomes are unchanged; placeholders are not live targets.

Date: 2026-09-29. Preparation only; a new scoped cloud session must be approved.
ADR-028 is the accepted duration exception. It does not waive other security or
failure-path checks. Session b already proves five live journeys and clean teardown.

## Prepared executable supplement

`scripts/cloud_fast_e2e.py` extends the existing five-case harness. It records only
checks reached successfully, stops on error, captures secrets privately in memory,
and uses the same ownership inventory and synthetic-fixture cleanup journal.

- Real DynamoDB concurrent identical seed: exactly one winner and one audit;
  reject conflicting immutable version; versions 2/10, numeric latest selection,
  historical version 1 preserved; consistent two-item query pagination.
- Real JWT Case isolation, admin read, reviewer creation denial, cross-owner submit
  denial and unchanged Case/audit snapshot.
- Assigned-only review start/check for other reviewer, requester and admin; replay
  same-owner start with no additional business/audit mutation.
- Three signed-header tamper denials: MIME, content length, conditional-write header.
- Real headless Edge Blob PUT from both default origins localhost:5173 and
  127.0.0.1:5173; API preflight including idempotency/correlation headers; S3 CORS,
  exposed ETag, overwrite rejection and denied unlisted origin localhost:5174.
  Only blank test documents are locally fulfilled. AWS requests are never mocked,
  browser security remains enabled, no existing dev server is stopped or rebound.
- Existing approve/reject/replacement/additive/invalid-document journeys and claim
  race remain included because a fresh environment has no prior fixtures.

Use the bundled Playwright module without adding a production dependency. Set
DOCFLOW_PLAYWRIGHT_MODULE and DOCFLOW_BROWSER_EXECUTABLE to verified local paths.
Do not set DOCFLOW_LOCAL_HARNESS for AWS; it is loopback-only fake-service testing.
Node command check covers both auth and browser helper syntax. Local browser
contract test uses `node --test acceptance/browser-probe.test.mjs` from repo root.

After an approved fresh deployment:

```text
python scripts/cloud_fast_e2e.py --config build/task-021/config.fast.json --approved-action <session>/fast-e2e
python scripts/cloud_evidence.py --config build/task-021/config.fast.json
```

The script is a bounded supplement, not an assertion that the full remaining
matrix is automated. Record individual live PASS observations separately from
local tests and duration omissions. Do not run it over an existing fixture journal.

## Reviewable next-session envelope

Project <REDACTED_AWS_ACCOUNT>; ap-southeast-2; profile docflow-toolkit; concurrency-10 mode.
Fresh session task021-20260929c, same original retained state bucket/key, no
bootstrap. Review a fresh create-only plan, expected same 189 application resources
(13 Lambdas, API/Cognito/DynamoDB/S3/queues/workflow/EventBridge/logs/alarms/dashboard).
Five disposable users/cases; template versions 1/2/10 with synthetic content;
under 100 KB PDFs and fewer than 100 notifications only to the already verified
mailbox. No paid capacity, new AWS features, SNS recipient, quota or plan changes.

Target 45-60 minutes, maximum 120 including cleanup; stop new tests and begin
cleanup at minute 60. USD 10 contingency, not guaranteed cost or hard cap; account-specific billing/credit details are withheld for privacy; free operation cannot be promised. Never retain an
environment overnight. On failure/success clean only this session's synthetic
data and application resources, with the reviewed protection-only DynamoDB/Cognito
unlock and delete-only inventory match. Keep original state/versions, SES and
shared API Gateway role; record automatic SYSTEM backup/history retention.
Any existing application resources, unexpected plan or extra scope stops apply.

## Remaining manual evidence outside the executable supplement

The detailed per-clause procedures remain in cloud-scenarios.md. Still outstanding
are wrong-client/issuer/expired JWT cases, broader role/cursor/assignment combinations,
transaction conflicts, worker duplicate/lease/mixed-batch faults, accepted-send/lost-ack
recovery, exact IAM runtime denials, 98-check preparation/races, late prior-attempt
isolation, delivery confirmation, actual DLQ/alarm/recovery behavior and hosted CI
for the final code. Do not report these PASS from five journeys or policy inspection.

Any fault-injection mutation must have its exact fixture/resource and restoration
reviewed before execution. The envelope above approves no disabling mappings,
policy edits, queue purge, synthetic metric injection or state-machine change by
implication. Complete read-only observations during the same session; obtain
specific authority for additional mutations. Local tests can prepare these cases
without extending AWS uptime. This is why the task is not DONE merely by omitting
the two long waits.
