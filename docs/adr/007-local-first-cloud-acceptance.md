# ADR-007: Local development followed by consolidated cloud acceptance

**Status:** Accepted
**Date:** 2026-09-15
**Authority:** User explicitly requested local development first and short-lived cloud acceptance later.

## Decision

TASK-003 through TASK-020 are local implementation tasks. DONE means implementation,
contracts, relevant local verification and documentation are complete. It does not
mean AWS deployment or live service acceptance has passed. Preserve TODO/READY/
IN_PROGRESS/BLOCKED/DONE; track cloud checks separately with NOT RUN/PASS/FAIL/BLOCKED.

Transfer live acceptance to TASK-021 and docs/CLOUD_ACCEPTANCE.md. Earlier dependency
edges depend on local completion, so TASK-004 can follow TASK-003 without AWS access.
Never defer a missing implementation, failing local test, or unresolved architecture
conflict as a cloud-only check. Tests must exercise the actual code; use local doubles
and provider mocks with their limitations stated. Do not replace the production AWS
architecture or claim mocks prove IAM, delivery, retries, races or signatures.

TASK-021 prepares all acceptance scripts/fixtures, cleanup inventory and deployment
workflow locally before requesting one explicit, bounded cloud session authorization.
Normal task execution, GitHub publication and a main-branch push do not authorize AWS
deployment. Deployment workflows must be manually gated, never push-triggered by default.

Before cloud writes, present account/region, resource plan, cost estimate, test scope,
session duration, backup/retention and cleanup plan. Include cleanup of only newly
created disposable session resources in the approval; existing data or protected
resources need explicit treatment. Preserve evidence outside deployed resources.
Refresh identity and use least privilege. Never imply alerts/throttles guarantee a
spending ceiling. No automatic account-plan upgrades.

Complete the TASK-021 matrix on real AWS, fix and re-test failures, perform approved
cleanup, check remaining resources and later billing data (which can lag). A failed
cloud check keeps TASK-021 open and prevents TASK-022 portfolio-ready claims; earlier
local task records remain honest about their limited scope.

ADR-005 still requires remote state before shared/automated deployment. Prepare its
configuration locally; actual bootstrap/migration is part of the authorized session.
No always-on development environment is required.

## Current transition

Existing TASK-003 evidence supports local DONE; live authentication remains NOT RUN
under TASK-021. TASK-004 becomes READY. No new cloud checks have passed as a result
of this planning change. Automatic GitHub commit/push applies to locally completed
implementation tasks under AGENTS section 7.1 and does not deploy AWS.

## Supersedes

Supersedes ADR-006's requirement to keep TASK-003 BLOCKED until live acceptance and
the previous per-phase cloud completion timing. Product scope, AWS architecture,
security requirements and final real-world acceptance criteria remain unchanged.
