# DocFlow portfolio guide

Illustrated introductions: [中文](guide-zh.md) / [English](guide-en.md).
Offline editions with embedded screenshots: [中文 HTML](DocFlow-中文介绍.html) /
[English HTML](DocFlow-English-Guide.html). Download and open HTML in a browser;
GitHub normally displays its source instead of rendering the page.

DocFlow models a document review as a Case, uploaded Documents, an immutable
Checklist Template, an assigned Review Task and an Audit Timeline. The first
example is supplier onboarding; the architecture separates human decisions from
asynchronous validation and notifications.

## Review in ten minutes

| Question | Read |
| --- | --- |
| What was built and how do components communicate? | [Architecture](architecture.md) |
| Why these services and reliability patterns? | [Design rationale and trade-offs](trade-offs.md) |
| Who can see or change data? | [Security](security.md) |
| What creates costs, and what remains deployed? | [Cost and retirement](cost.md) |
| How do I run, diagnose or recover it? | [Runbook](runbook.md) |
| What can I demonstrate without AWS? | [Demo scenario](demo.md) |
| How could AI be added responsibly? | [Project 2 roadmap](project-2-roadmap.md) |

## Evidence boundary

- TASK-003 through TASK-020 completed local implementation acceptance.
- On 2026-09-29, an explicitly approved short AWS session ran five real journeys:
  approve, reject, replacement resubmission, additive resubmission and invalid
  document rejection. Deployment and application cleanup passed. See the
  [session record](../verification/TASK-021-20260929b-session.md).
- The latest local working-tree check passed 574 backend tests and six frontend
  tests, lint/format/type/build. Additional acceptance tooling remains local and
  is not part of the TASK-022 documentation publication; a clean clone can have
  fewer tests. Exact scope is in [fast preparation evidence](../verification/TASK-021-FAST.md).
- Twelve notification completion receipts proved SES acceptance, not confirmed
  inbox delivery. No claim of end-to-end exactly-once email delivery is made.
- The owner elected to skip the remaining TASK-021 acceptance and retire cloud
  resources. TASK-021 is not DONE; TASK-022 documents these limits under
  [ADR-029](../adr/029-retire-cloud-and-document-portfolio.md).
- The frontend is a synthetic in-memory design demo. It has no Cognito/API/upload
  integration. Its private preview is separate from AWS retirement.

This is a portfolio implementation with partial real-service evidence, not a
production-readiness certification. Read the [cloud ledger](../CLOUD_ACCEPTANCE.md)
before making availability, security, disaster-recovery or load-capacity claims.
