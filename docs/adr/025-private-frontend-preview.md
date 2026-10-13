# ADR-025: Private frontend design preview

- Status: Accepted
- Date: 2026-09-29

## Context

The user requested GitHub publication and an online preview of the completed
frontend design. The existing GitHub repository is private. GitHub rejected Pages
activation with HTTP 422 because the current plan does not support Pages for this
repository. Changing repository visibility or upgrading the plan is not authorized.

## Decision

Keep React/TypeScript source in the existing private GitHub repository. Host only
the built synthetic-data frontend on an owner-private Site. This is a design
preview, not the AWS production deployment. AWS resources, authentication, backend
APIs and real documents are not connected. TASK-021 remains BLOCKED independently.

Use a separate ignored checkout containing only the Vite output and Site manifest.
Never publish the DocFlow repository root, Terraform state, credentials or cloud
acceptance evidence to the Site. Retain the Site project ID in the publishing guide
and reuse it for updates. Source updates require a new build and Site publication;
GitHub pushes alone do not automatically update the Site.

## Consequences

The owner can review interactions online without an AWS deployment. Sharing with
other users requires an explicit audience change. Production authentication and
cloud acceptance remain future work. See `frontend/PUBLISHING.md` for operation.
