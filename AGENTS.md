# AGENTS.md — DocFlow AI Development Contract

> Privacy note (2026-10-14): account-specific billing/credit details and private support identifiers are withheld for public release. Historical technical outcomes are unchanged; redacted details are not live targets.

2026-10-14 PRIVACY-PUBLISH-01: the owner explicitly approved preserving private
history and publishing the reviewed clean source under the original name.
Public repository: https://github.com/chanbilly-lab/docflow (ID 1418914087),
default branch codex/privacy-release; clean checkout D:/Projects/docflow-public.
The original repository (ID 1366248864) is docflow-private-archive, PRIVATE and
archived read-only. D:/Projects/docflow and the original audit mirror now point
only to that archive; their work/history remain intact. New public commits must
use GitHub noreply and the clean checkout. Never merge/push legacy private history
into this repository. Initial codex publication ran no application CI; do not
push main or create a PR while the owner's no-test instruction remains active.
No force-push, AWS action, application testing or deployment occurred. Source
publication does not establish cloud acceptance or production readiness.
See docs/PRIVACY_REVIEW.md; all runtime/security/cloud boundaries remain.

This file is the permanent operating contract for Codex and other coding agents working on DocFlow.

The normal user prompt should be only:

```text
执行 TASK-XXX。
```

The agent must infer the complete workflow below from this file.

---

## 1. Source-of-truth priority

When information conflicts, use this order:

1. `AGENTS.md` — agent operating rules
2. `PROJECT_STATUS.md` — current project/session state
3. `docs/tasks.md` — task scope, dependency, acceptance criteria
4. `docs/DECISIONS.md` and `docs/adr/*` — approved technical decisions
5. `docs/TECHNICAL_DESIGN.md` — technical baseline
6. `docs/PRD.md` — product requirements
7. `docs/api/openapi.yaml` and `docs/events/*.schema.json` — interface contracts
8. current code/tests

If code and approved documentation conflict, do not silently pick one. Record the inconsistency and resolve it only if the current task allows it.

---

## 2. Mandatory session-start protocol

Before modifying anything for `TASK-XXX`, the agent MUST:

1. Read `AGENTS.md`.
2. Read `PROJECT_STATUS.md`.
3. Read `docs/tasks.md`.
4. Read the latest relevant entries in `docs/CHANGELOG.md`.
5. Read `docs/DECISIONS.md` and relevant ADRs.
6. Read current task-related code and documentation.
7. Confirm internally:
   - current phase
   - current task state
   - dependencies
   - acceptance criteria
   - architecture constraints
   - relevant verification commands
8. Execute only `TASK-XXX`.

Do not start from chat context alone.

---

## 3. Scope rules

- Modify only content required by the current task.
- Do not perform unrelated refactors.
- Do not change architecture or technology stack without an approved decision/ADR.
- If another problem is found, record it but do not fix it unless it blocks the current task.
- Keep changes reviewable and task-bounded.
- Do not mark a task complete until its acceptance criteria are satisfied.

---

## 3.1 Local development and deferred cloud acceptance

User-approved plan, 2026-09-15 (ADR-007):
- TASK-003 through TASK-020 use local implementation acceptance. DONE requires real
  local checks and documentation; it does not assert cloud deployment.
- Local dependency completion permits the next local task. Transfer live AWS checks
  to TASK-021 and docs/CLOUD_ACCEPTANCE.md, record NOT RUN with that owner.
- Missing AWS credentials or unapproved deployment do not block a local task whose
  cloud checks are explicitly deferred. Missing code/failing local checks still block.
- TASK-021 must prepare scripts and a concrete short-lived deployment/test/cleanup
  plan before explicit user approval. Generic task prompts and GitHub pushes do not
  authorize AWS writes, automated deployment, account upgrades or destructive cleanup.
- Production architecture is unchanged. The user-approved 2026-09-29 duration
  omissions in ADR-028 stay NOT RUN and no longer gate TASK-021. All other real
  cloud acceptance and approved cleanup must pass before DONE; TASK-022 follows it.
- User exception, 2026-09-29 (ADR-029): skip remaining TASK-021 acceptance and
  proceed to TASK-022 documentation. Keep TASK-021 BLOCKED with owner-skip reason;
  TASK-022 may complete without asserting full cloud acceptance or production readiness.
- Section 7.1 automatic publication applies to locally DONE implementation tasks.
  Commit descriptions and verification records must clearly state deferred cloud checks.

---

## 4. Architecture invariants

Unless an approved ADR changes them:

1. Project 1 is serverless-first and AI-free.
2. Step Functions orchestrates one Case workflow.
3. EventBridge broadcasts domain facts.
4. Domain command Lambdas do not directly publish business events to EventBridge.
5. Business state + audit + outbox are transactional where a domain event is required.
6. DynamoDB PK/SK formats in `TECHNICAL_DESIGN.md` are stable.
7. Async consumers are idempotent.
8. SQS consumers support retry and DLQ.
9. Workflow task tokens never leave trusted backend components.
10. S3 object keys are backend-generated.
11. All business state changes produce audit records.
12. Public API changes update OpenAPI.
13. Domain event changes update JSON Schema.
14. Architecture changes update design docs and normally require an ADR.
15. Bedrock/RAG/OpenSearch/ECS/EKS/Aurora/WebSocket are not added before their planned phase without an ADR.

---

## 5. Implementation rules

- Follow existing directory and coding conventions.
- Add dependencies only when justified by the task.
- Use least-privilege IAM.
- Never commit credentials, tokens, presigned URLs, task tokens, or secrets.
- Never log sensitive document content.
- Enforce authorization on the backend.
- Use conditional writes for concurrency-sensitive transitions.
- Preserve contracts unless the task explicitly changes them.

---

## 6. Verification rules

After code changes, run all checks relevant to the task, including where applicable:

- unit tests
- integration tests
- contract tests
- lint
- formatting checks
- type check
- build
- `terraform fmt -check`
- `terraform validate`
- smoke tests

Never fabricate results.

Use only:

- `PASS`
- `FAIL`
- `NOT RUN`
- `BLOCKED`

If something cannot run, state the exact reason.

---

## 7. Mandatory end-of-task documentation update

After implementation, the agent MUST:

1. Update `TASK-XXX` status in `docs/tasks.md`.
2. Update `PROJECT_STATUS.md`:
   - current phase
   - last completed task
   - current/next task
   - blockers
   - latest verified tests/builds
   - handoff note
3. Add the task entry to `docs/CHANGELOG.md`.
4. If an important technical decision was made, update `docs/DECISIONS.md` and add/update an ADR where appropriate.
5. If API, database, event schema, architecture, security, infrastructure, or requirements changed, update the relevant source-of-truth documents.
6. Check that code and documentation agree.

`PROJECT_STATUS.md` must never be left stale.

---

## 7.1 Automatic GitHub publication

Standing user authorization, granted 2026-09-12:

After each implementation task reaches DONE and required verification/documentation
updates are complete, automatically commit and push its changes to the configured
GitHub remote. Do not ask for confirmation again for normal task publication.

- Inspect the working tree before staging. Include the completed task and its
  documentation; preserve unrelated pre-existing changes outside the commit.
- Run `git add .` from the repository root when all changes belong to the task.
  Otherwise stage the task files explicitly.
- Use the message format `feat: complete TASK-XXX <short English task summary>`.
  TASK-002 uses exactly `feat: complete TASK-002 repository foundation`.
- Run `git push` for the current branch's configured upstream and verify the remote
  branch points to the new commit. Report the commit and publication result.
- Never force-push, rewrite published history, or publish credentials/state files.
  If publication fails, report the actual blocker and retain the local commit.
- Do not publish unfinished or BLOCKED work as a completed task. A review-only task
  with no changes does not require an empty commit.

---

## 8. Task status vocabulary

Use only:

- `TODO`
- `READY`
- `IN_PROGRESS`
- `BLOCKED`
- `DONE`

---

## 9. Decision triggers

Update `docs/DECISIONS.md` when a change affects:

- architecture
- AWS service choice
- state machine semantics
- DynamoDB keys/access patterns
- API contract
- event contract
- auth/security boundary
- reliability pattern
- deployment strategy
- major dependency

Use an ADR for durable architectural decisions.

---

## 10. Required final response format

After every task, output exactly:

```text
Task：
Summary：
Files Changed：
Documentation Updated：
Tests：
Known Issues：
Next Step：
```

Requirements:

- `Task` — task ID and final status.
- `Summary` — concrete implementation result.
- `Files Changed` — exact files changed.
- `Documentation Updated` — exact docs updated, or `None`.
- `Tests` — commands/checks and real results; mark anything not run.
- `Known Issues` — unresolved/out-of-scope findings, or `None`.
- `Next Step` — next task ID from project state/task dependency order.

---

## 11. Fixed user prompts

Normal task:

```text
执行 TASK-XXX。
```

Interrupted task:

```text
继续 TASK-XXX。
```

Verification/review only:

```text
复核 TASK-XXX。
```

No other boilerplate is required unless the user explicitly overrides the task scope.

---

## 12. Stop conditions

Stop and report instead of guessing when:

- a dependency is missing
- permissions/credentials prevent required verification that is not explicitly deferred under section 3.1
- task requirements conflict with an approved decision
- source-of-truth documents contradict each other
- destructive migration is required but not authorized
- completing the task requires unrelated architecture changes


<!-- BEGIN AWS Agent Toolkit rules -->

# AWS Guidance for the new AWS experience

For environments using the managed AWS project experience, apply the following constraints. This experience supports sign-in through a social provider; use the environment-appropriate guidance below.

Where this guidance conflicts with the project's own instructions, the project's instructions take precedence.

## Context

### Terminology:

- Say "project" instead of "account" — a project contains an AWS account and settings for sharing with other collaborators
- Say "team member" instead of "IAM user" — users are invited by email, not created or federated in IAM
- Say "AWS Settings" when referring to management tasks at [settings.aws.com](https://settings.aws.com/) (project management, billing, team members, spend limits). Users view their actual AWS resources in the AWS Management Console.
- Say "selected Region" when referring to the user's Region — not "home Region"
- The user has a managed IAM experience. This includes a managed service control policies (SCP) and resource control policies (RCP) that govern the use of AWS. They will still need to use IAM to create policies to let services work with each other. If there are questions about the SCPs or RCPs, go to the documentation at https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html

### Constraints:

- All projects share a single AWS Region determined by the user's contact address. Resources cannot be created in other Regions
- When developing:
  - MUST create all Regional resources in the project's assigned Region
  - You CAN create AWS WAF and Cloudwatch Logs resources in us-east-1 when there are global resources (like a global WAF instance) that require a connection to dependencies in us-east-1. You should not use these for any other reason, because resources in the selected Region will provide lower cost (due to no cross-Region traffic), increased availability (due to no cross-Region traffic), and easier manageability (due to not needing to look in another Region). When you need to do an inventory of resources, you need to look in both the selected Region and us-east-1 for Cloudwatch Logs or WAF resources.
  - MUST NOT attempt to create Lambda, API Gateway, or other Regional resources in any other Region
  - MUST direct users to confirm their Region in AWS Settings > View all projects > Overview > Additional Info > Region. If the user cannot confirm their Region, check in ~/.aws/config
  - MUST NOT use Lambda@Edge — excluded from both Lambda and CloudFront
  - MUST NOT use CloudFormation StackSets — no multi-account or multi-Region deployments
  - MUST NOT attempt cross-Region actions — no cross-Region replication for DynamoDB/S3/RDS, no multi-Region KMS keys
  - MUST NOT use Route 53 cross-Region routing — geolocation, latency-based, and failover routing policies are not available
  - CloudFront is a global service and its actions ARE allowed in `us-east-1`. A user can create a CloudFront distribution pointing to their project-region Lambda function URL or API Gateway. However, Lambda and API Gateway themselves MUST NOT be created in `us-east-1` — they must be in the project Region.
  - Reduced availability in `eu-north-1` specifically: Amazon Rekognition, Amazon Textract, Amazon Personalize, AWS App Runner are not available in that Region.
- IAM permissions for human access are managed by AWS. Don't assign roles to team members unless absolutely necessary
- The user may have a spend limit if they are on the paid plan. The limit that pauses their project if it's exceeded. If resources suddenly become inaccessible, ask if they have a spend limit configured. Only project owners can modify a spend limit.
- When developing:
  - MUST ask about spend limit status if the user reports sudden "Access Denied" errors on operations that previously worked
  - MUST direct users to check spend status in AWS Settings > Billing
  - MUST check if a user has upgraded their account to the paid plan
  - MUST ask the user if they want to clean up the successfully created resources or keep them to reduce cost
- The user sets up billing, creates spend limits, and retrieves and pays invoices in AWS Settings. The user creates budgets and optimizes their costs in the AWS Billing and Cost Management console
- Not all AWS services are available. If a service isn't working, do the following:
  1. Run the command `aws freetier get-account-plan-state`
  2. If accountPlanType": "FREE", check the [Free Tier supported services list](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html#supported-services-free-tier) next,
  3. If accountPlanType": "PAID", check the [Paid Tier supported services list](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html#supported-services-paid-plan).
  4. If neither list shows the service, check the [Not supported for this experience list](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html#unsupported-services). The user will need to activate advanced features to access this service.
- Users can activate advanced AWS services and capabilities for their account.
- Before starting a task, check whether a relevant AWS skill is available. Load the skill with retrieve_skill and prefer its guidance over general knowledge.

### Help level

User preference: MEDIUM (confirmed 2026-09-29).

- help_level (required): LOW, MEDIUM, or HIGH. While a user is building, you MUST ask the user: "How much guidance would you like from me? Low (I only flag security risks), medium (I ask a couple of clarifying questions if something seems off), or high (I explain what I'm doing, suggest alternatives, and flag best practices)."

You CAN update this rule file to save a user's help_level.

Constraints for each level:

**LOW:**

- MUST follow all constraints in this context file
- MUST execute the user’s request without modification
- MUST NOT ask clarifying questions unless the action would create a security vulnerability
- MUST NOT suggest alternatives or improvements

**MEDIUM:**

- MUST execute the user's request
- MAY ask up to two clarifying questions per task if the request has an ambiguity or a potential issue
- MUST NOT repeat a question or suggestion the user has already dismissed
- MUST NOT explain trade-offs or alternatives unless the user asks

**HIGH:**

- MUST explain what each step does and why before executing it
- MUST suggest alternatives when a better approach exists
- MUST flag best practices and explain trade-offs
- MUST still execute the user's choice if they disagree with a suggestion

<!-- END AWS Agent Toolkit rules -->
