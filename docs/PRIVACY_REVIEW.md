# PRIVACY-PUBLISH-01 — Public source preparation

Date: 2026-10-14. Status: prepared locally; repository-management approval pending.

The owner requested privacy review, necessary redaction and public publication of
DocFlow and the admissions project. This source candidate does not deploy an
application, change AWS resources or complete the outstanding cloud acceptance.

## Actual review

- Original remote inventory: one branch, 24 reachable commits, 666 blobs,
  7,185,407 blob bytes. All reachable blobs and commit metadata were read.
- Gitleaks 8.30.1 scanned all original refs with default rules, no repository
  allowlist, complete redaction and a private local report. Exit 1 represented
  one finding: an integration-test UUID used as an Idempotency-Key. Its original
  commit was read and its non-secret purpose confirmed; no credential was used.
- Manual source review found real cloud account/resource identifiers, personal
  user-home paths, an owner-private preview URL and internal Site identifiers.
  Thirteen source documents received 33 exact redactions. Placeholder notes
  distinguish redactions from executed commands and preserve historical outcomes.
- Additional semantic review removed account-specific plan/credit readings and
  an exact support-case identifier. Thirty account/user-context corrections were
  applied across 18 documents; seven further documents gained redaction notes.
  General technical pricing, project estimates and historical outcomes remain.
- Original author/committer metadata contained the owner's private email. It is
  retained only with the original private history, not copied to this public
  candidate's new history. New commits use the GitHub noreply address.
- The six source PNGs were actually viewed, their metadata read, and embedded
  HTML images compared to the same bytes. They are the synthetic demonstration,
  without real customer documents or personal contact data.
- All 23 remote Actions logs (23,652 lines), 45 check outputs and 59 annotations
  were read. No actionable secret/privacy finding was identified there. No PR,
  issue, release, tag, artifact, deployment, environment or repository variable
  required migration or cleanup. Platform secret values cannot be read by API.
- The post-redaction source inventory found zero remaining candidates in the
  reviewed real-information categories. Original application code, schemas,
  tests, dependency locks, infrastructure definitions and synthetic images remain
  byte-for-byte unchanged. Public dependency-maintainer contacts are not removed.
- A provisional single-commit candidate was scanned: Gitleaks exit 1 / one same
  verified non-secret test UUID. The final publish-ready repository is rebuilt
  from sanitized source only, so provisional pre-review objects/reflogs are
  excluded. Its committed tree and noreply metadata are reviewed separately.

## Proposed publication method

Keep the existing repository and all its history as a private backup, then create
a new repository at the original public-facing name from this reviewed latest
source snapshot. This avoids force-pushing, discarding the original history or
making old sensitive commits reachable in a public repository. Original working
directories are preserved; old remotes would point to the private backup and a
separate clean working copy would be used for public work.

This management operation awaits explicit selection because it renames existing
repositories and changes old-checkout remote destinations. No visibility change,
rename, history rewrite or force-push has occurred during preparation.

The source owner's public GitHub account, standard example identifiers, synthetic
test inputs and generic project-layout paths are retained. Exact private reports,
literal replacement maps, original Git mirrors and credentials are not part of
this source candidate. Initial publication will not run application CI; the
existing workflow remains available for a separately authorized future run.

## Limits

This is a static/privacy audit, not a guarantee against every undiscovered
encoding, credential or external copy. No application tests, lint, type checks,
builds, live credential probes, AWS calls or deployments were run. Old test
results remain historical records, not new results for this source candidate.

Public source does not enable the backend, connect the synthetic frontend to it,
restore retired resources or claim production readiness.
