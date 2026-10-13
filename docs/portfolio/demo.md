# Five-minute demo scenario

## Preparation

Run the [local commands](runbook.md). The [published preview](../../frontend/PUBLISHING.md)
is owner-private and may require the owner's sign-in; reviewers should use the
local checkout if they lack access. AWS cleanup does not remove this separately
hosted synthetic preview. Use only built-in fictional data.

## Presentation script

| Step | Show | Explain |
| --- | --- | --- |
| 1 | Overview counts, search and status filters | A Case centralizes review progress; displayed values are demo state |
| 2 | Select a Case, inspect documents/checklist/activity | Bound requirements and history make decisions explainable |
| 3 | Claim/start and complete required checks | The demo illustrates guards; real enforcement lives in backend handlers |
| 4 | Approve, reject with a reason, or request information | Business outcomes differ from technical workflow failure |
| 5 | Create a draft, inspect template/help, export filtered JSON | These are local UI interactions; export contains synthetic data |
| 6 | Reload/reset | No persistence, real authentication, uploads or emails are claimed |

Then open [architecture](architecture.md) and the [successful cloud-session evidence](../verification/TASK-021-20260929b-session.md).
Explain the actual five backend journeys and the distinction between that historical
API harness and the current UI demo. The replacement/additive backend resubmission
paths were tested live; the frontend does not implement those network flows.

## Reviewer questions

- Why can two reviewers not both claim? Conditional transactional writes fence task
  ownership; a two-request live race had one winner in the recorded session.
- Can email be sent twice? Yes after uncertain SES acceptance; completion receipts
  suppress normal repeats, not every crash boundary.
- Is it production ready? No such claim: broader IAM/fault/browser/retention evidence
  remains unrun or user-omitted, and the UI is not integrated with the backend.
- Why is the online backend unavailable? Resources were short-lived for acceptance;
  the owner chose retirement instead of ongoing charges and remaining tests.
