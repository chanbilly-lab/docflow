# ADR-005: Dev Terraform foundation and initial state

**Status:** Accepted
**Date:** 2026-09-12

## Context

TASK-002 needs a reproducible dev foundation and credential-free fmt/validate.
The approved baseline separates state by environment and assigns the table to
database and log groups to observability. No shared state service or AWS environment
has been deployed.

## Decision

- Compose only database and baseline observability in infra/environments/dev.
  Retain all existing module boundaries.
- Use Terraform 1.14.x (verified patch 1.14.9) and HashiCorp AWS provider >=6.64.0, <7.0.0,
  with the selected provider version and package checksums committed in the dev lockfile.
- Use an explicit local backend in the dev directory for the initial single-operator
  foundation. State, plans and local variable files remain ignored. Backend bootstrap,
  remote state configuration and migration must precede shared or automated deployment
  in TASK-021 (or an earlier task that needs shared deployment). Do not reuse dev state
  for staging/prod or store state in Git. This task performs no apply.
- Preserve section 6 keys. Name indexes GSI1/GSI2 with ALL projections for the
  documented requester/reviewer/admin queries; backend response filtering remains
  mandatory, including workflow task tokens.
- Use on-demand billing, TTL expiresAtEpoch, NEW_AND_OLD_IMAGES Streams, point-in-time
  recovery and deletion protection enabled by default. Use DynamoDB's default
  AWS-owned encryption; no new KMS key or IAM policy.
- Manage log groups centrally, with 14-day dev retention, for the 12 section 8
  Lambdas, HTTP API and Standard workflow. Future compute/API/workflow modules
  must reuse these names/ARNs and depend on log group creation.
- Run provider-mocked plan tests locally and in PR CI, with no cloud credentials.

## Consequences

This implements the existing architecture without business handlers or deployment.
Local state is unsuitable for multiple operators and CI deployment; backup and later
migration are required before introducing those workflows. PITR and index projections
have storage cost after deployment. TTL applies only to records deliberately given an
expiry; audit/business records must not be assigned an expiry by default.

Log groups alone do not enable service logging, tracing, metrics or alarms. Those
integrations remain in their assigned tasks. Mock tests verify configuration contracts,
not AWS permissions or live service behavior.
