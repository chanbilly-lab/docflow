# ADR-028: User-approved omission of long elapsed-time acceptance

Status: Accepted. Date: 2026-09-29. Task: TASK-021.
Authority: user requested completing remaining acceptance while allowing long
tests to be omitted, explicitly naming 24-hour and 14-day checks.

Omit these wall-clock waits from the TASK-021 completion gate:

- Actual Streams expiry after more than 24 hours and recovery after that real
  expiry (outbox publication and workflow start).
- Actual production callback timeout after 1,209,600 seconds / 14 days, including
  timeout-specific task closure dependent on that wait.
- Real 85-day workflow recovery age, if interpreted as an elapsed-time test. Keep
  synthetic old-metadata boundary tests for the 85-day guard.

Evidence stays NOT RUN, reason "user-approved duration omission, ADR-028".
Never relabel a timestamp edit, shortened workflow or abort as proof of production
duration. No running environment is retained for these waits. Production timeout,
retention, recovery code, safety guards, local tests and architecture are unchanged.

Other criteria remain required: short JWT, CORS, IAM, race, idempotency, fault
recovery, queue DLQ and alarm checks are not waived merely because they are hard.
Ten-minute signature expiry and bounded SQS retries can overlap other work. Any
additional proposed omission must be explicit before relying on it for DONE.
Delivered-mail confirmation still requires actual evidence.

DONE requires all non-omitted criteria and approved cleanup PASS, with these
limitations in final evidence and portfolio claims. TASK-022 remains dependent.
This supersedes the blanket no-waiver rule only for the duration clauses above
in AGENTS 3.1, ADR-007/023/027 and acceptance runbooks/ledger. Historical session
records remain unchanged. This scope decision alone authorizes no new AWS writes.
