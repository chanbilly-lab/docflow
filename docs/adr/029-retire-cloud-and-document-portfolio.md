# ADR-029: Retire AWS deployments and proceed to portfolio documentation

Status: Accepted. Date: 2026-09-29. User explicitly requested skipping TASK-021,
clearing AWS deployments/paid resources, changing to free if possible, then TASK-022.

TASK-021 remains BLOCKED (owner elected to skip remaining acceptance), not DONE.
Keep all real results and NOT RUN limitations. Waive its dependency gate for
TASK-022 only; documentation can be complete without claiming production readiness.
No new deployment or test emails are authorized. TASK-022 is documentation work.

The cleanup request supersedes the prior preference to retain cloud prerequisites.
Automatic approval review nevertheless requires itemized confirmation before deleting
the retained state bucket/history, SYSTEM backups, SES identity and shared API role.
Record confirmed deletions separately from attempted/blocked operations. Preserve
local source/evidence; do not remove managed access roles or close the project.

Initial clarification: user chose to keep all four listed categories and complete
TASK-022 only. This supersedes the blanket cleanup request; no deletion retry or
additional cleanup confirmation is pending. Support subscription was not checked.

Subsequent explicit amendment: owner revoked retention for the state bucket/all
versions and both SYSTEM backups. State bucket deletion is verified complete;
AWS disallows manual SYSTEM backup deletion, so both await automatic expiry at
no additional retention cost. SES identity and shared role retention is unchanged.
See verification/AWS-RETIREMENT.md for actual API results. This amendment supersedes
the initial retention direction only for the specifically authorized items.

AWS's paid plan cannot be downgraded to a free plan. Report this limitation, clean
identified resources when permitted and inspect recurring subscriptions where access
allows. Resource absence is not a zero-bill guarantee or cancellation of historical
usage. No workaround involving new accounts, plan upgrades or account closure.

Publish TASK-022 documentation under the normal completion commit format. Preserve
pre-existing unfinished TASK-021 code outside that commit; historical evidence and
decision documents may accompany the portfolio where needed to substantiate claims.
Unpublished tooling must not be presented as available in a clean clone.

Source: [AWS Free Tier FAQ](https://aws.amazon.com/free/free-tier-faqs/), checked
2026-09-29. Current cleanup evidence belongs in verification/AWS-RETIREMENT.md.
