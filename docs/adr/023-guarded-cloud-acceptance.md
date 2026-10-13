# ADR-023 - Guarded operator deployment and consolidated cloud acceptance

Status: Accepted
Date: 2026-09-28
Task: TASK-021 (IN_PROGRESS; no deployment approval)

Region/profile amended by ADR-024: docflow-toolkit/ap-southeast-2.
The original choice below is historical and must not be used for live deployment.

## Decision

Implement ADR-005/007's state transition now: dev uses an S3 partial backend,
versioning and AES256 encryption with S3-native use_lockfile. The separate bootstrap
root uses a protected local state under ignored build/task-021/<session>, and
creates a private, versioned, TLS-only state bucket with prevent_destroy. Dev
state and lock share the approved bucket. No DynamoDB locking table, KMS key,
GitHub OIDC role or additional cloud deployment identity is introduced.

First deployment is operator-run using the refreshed docflow-dev profile in
us-east-1. Both provider and backend restrict the verified account ID. The CLI
requires a unique session config in ignored build/task-021, explicit action
acknowledgement, review of the saved plan hash, unchanged source/Lambda artifact
fingerprint and unchanged config. These flags prevent mistakes; they do not
replace user authorization. A generic TASK prompt or CI dispatch is not approval.

Bootstrap/deploy permit only fresh create plans and reject any prior managed
state. Existing local state requires a separately reviewed backup/migration; the
tool will not silently migrate it. An apply records exact address/resource IDs,
including partial-apply resources, and refuses another deployment attempt under
that inventory. Recovery of a partial apply requires private inspection and a
reviewed follow-up; no force-unlock/state deletion/import shortcut is supplied.

Runtime Cognito protection remains ACTIVE and DynamoDB protection stays enabled.
The new Cognito flag only permits a reviewed cleanup plan to deactivate it.
Unlock plans accept only the two protection changes. Destroy requires exactly
the recorded resource inventory and delete-only actions. Source/config/plan hash
checks apply again. The document bucket retains force_destroy=false: only recorded
synthetic object keys in a verified session-tagged bucket may be deleted by the
cleanup tool. Versioned/unrecorded objects or executions stop cleanup for review.
The state bucket and its history are explicitly retained; no state purge is provided.

## CI and fixtures

Existing push/PR checks stay credential-free and read-only. Pin all GitHub Actions
to resolved commit SHAs, bound job duration, cancel superseded checks and support
manual check dispatch. CI tests both Terraform roots with mock providers and
installs/checks the locked test-only SRP helper. There is no apply step,
id-token:write, cloud secret or push-triggered deployment.

The operator harness provisions five disposable Cognito users with invitation
messages suppressed, generates passwords in memory, and uses the actual
production SRP client through amazon-cognito-identity-js 6.3.20 (separate locked
acceptance package). This test-only dependency avoids inventing SRP cryptography
or weakening production auth flows. The helper receives passwords over stdin and
returns tokens over captured stdout to its parent; never run it with terminal
output redirected to evidence. Storage is memory-only. AWS CLI export-credentials
is captured directly in memory for boto3; no credentials file/export is printed.
The helper is not bundled into frontend or Lambda artifacts.

Fixture journal contains only resource identifiers and check outcomes. Public
HTTP paths drive create/upload/validation/submit/review/decisions/resubmission;
direct DynamoDB writes are limited to the existing atomic template seed. The
test suite never claims its automated subset covers the entire deferred matrix.
Read-only evidence is allowlisted configuration, not proof of service delivery.

## Scope and limits

All live matrix rows, actual IAM, alarm actions, S3 browser behavior, true stream
expiry and fault-injection recovery remain mandatory. A two-hour session cannot
prove a >24-hour Streams expiry. Actual 14-day workflow timeout likewise cannot
be asserted from a short test. Any shortened-timeout service probe must be
identified as a separate test configuration; the original criterion remains
NOT RUN unless its owner explicitly accepts that equivalence.

No live AWS operation, email, infrastructure bootstrap or cleanup has been
authorized/performed in this preparation. The expired-login finding is evidence
only of unavailable current identity. TASK-021 cannot be marked DONE or published
as completed until live criteria and approved cleanup pass.

## References

- [Terraform S3 backend and lockfiles](https://developer.hashicorp.com/terraform/language/backend/s3)
- [Amazon Cognito Identity SDK](https://www.npmjs.com/package/amazon-cognito-identity-js)
