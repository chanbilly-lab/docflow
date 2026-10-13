# ADR-006: Initial authenticated health path

> Privacy note (2026-10-14): account-specific billing/credit details and private support identifiers are withheld for public release. Historical technical outcomes are unchanged; redacted details are not live targets.

**Status:** Accepted
**Date:** 2026-09-15

## Context

TASK-003 requires Cognito, HTTP API JWT validation and an authenticated request.
The user authorized local implementation/testing only; no deployment.

## Decision

- Compose the existing auth/api/lambda boundaries alongside the foundation.
- Use an invite-only Cognito Lite pool with deletion protection, strong passwords,
  a public SRP/refresh client, no user credentials or client secret in Terraform.
- MFA is off for this initial dev pool; production authentication requirements remain
  separate. Access/ID tokens last 15 minutes, refresh tokens one day.
- Groups are requester/reviewer/admin, without attached IAM roles.
- Validate issuer/client in HTTP API. GET /api/v1/health requires the Cognito API
  sign-in scope aws.cognito.signin.user.admin to exclude ID tokens. This scope does
  not grant DocFlow admin privileges. Business APIs must enforce groups/ownership.
- Reuse case-query-handler and its central log group: Python 3.13 arm64, 128 MB,
  three-second timeout, log-only execution IAM, invocation restricted to this route.
- Log only API request ID/route/status, throttle dev to 2 requests/second and burst 5.
  Throttling is not a spending limit. No new billable always-on compute.
- Build a deterministic dependency-free ZIP before Terraform tests, with no additional
  provider. ZIP/state remain ignored. Use canonical /api/v1/health in all contracts.

## Consequences

Mock plans cannot establish cloud permissions, signature validation or HTTP behavior.
ADR-007 supersedes this completion timing: TASK-003 can be locally DONE; live
acceptance is owned by TASK-021 and remains NOT RUN until verified.
Account-specific billing/credit details are withheld for privacy; the user chose no deployment.
No account-plan changes are authorized. No hosted login or frontend login is included.

References:
- https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html
- https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html

ADR-009 supersedes the initial log-only query-function configuration: the same
function now serves health and authorized Case queries with table/index read access.
