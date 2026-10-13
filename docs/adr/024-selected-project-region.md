# ADR-024 - Selected region for the managed AWS project

> Privacy note (2026-10-14): account-specific billing/credit details and private support identifiers are withheld for public release. Historical technical outcomes are unchanged; redacted details are not live targets.

Status: Accepted
Date: 2026-09-29
Authority: user specified ap-southeast-2 and new AWS experience, selected
docflow-toolkit, and requested continued TASK-021 implementation.

## Context and decision

The prior us-east-1 SES deny was observed outside the project's selected region.
Read-only SES queries pass in ap-southeast-2. AWS manages this experience's
organization policies; do not edit/detach SCPs or pursue organization escape.
Supersede ADR-023's profile/region with docflow-toolkit/ap-southeast-2 for this
acceptance session. Preserve the old docflow-dev profile for historical context.

Scope dev and bootstrap providers, S3 state backend, Python SDK sessions, HTTP
API and S3 upload endpoint checks, examples and evidence to ap-southeast-2.
The operator config rejects other regions/profiles. Dev root validation rejects
other regions. Independent mocked module fixtures may retain synthetic us-east-1
ARNs; they are neither resources nor authorization for cross-region deployment.
No existing resources/state are migrated: the project has not been deployed.

Toolkit catalog/MCP endpoint remains us-east-1 per its official setup contract;
that service endpoint is not authorization for DocFlow resource creation there.
Business contracts and architecture remain unchanged. Session approval, saved-plan
hash guards, exact-inventory cleanup and state retention remain mandatory.

## Evidence and constraints

MCP STS and account-plan query execution PASS; account-specific billing/credit details withheld for privacy.
SES reads PASS: sending enabled, sandbox, zero identities, 200/day and 1/second.
A user-provided test mailbox stays in ignored local configuration. Supplying the
address is not permission to send verification mail; request explicit consent.
No infrastructure deployment, policy mutation or email is authorized by this ADR.
Keep real cloud acceptance NOT RUN. Re-estimate costs for Sydney before deployment;
earlier us-east-1 sample rates are not a Sydney quote.

Reference: https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html
