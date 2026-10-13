# DocFlow — Cloud-native Document Review & Approval Platform

**Document:** PRD  
**Version:** 1.1  
**Status:** Approved for implementation  
**Primary Goal:** Build a portfolio-grade AWS serverless document review platform that demonstrates cloud architecture, event-driven design, workflow orchestration, security, observability, IaC, and CI/CD.

Current delivery boundary (2026-09-29, ADR-029): owner chose to skip remaining
TASK-021 acceptance and proceed to portfolio documentation. Requirements below
remain design goals; they are not a claim of complete production verification.
The frontend is synthetic and does not integrate real backend authentication/API
flows. See [portfolio guide](portfolio/README.md) and [cloud ledger](CLOUD_ACCEPTANCE.md).

---

## 1. Product Summary

DocFlow is a generic enterprise document review and approval platform.

It supports workflows such as:

- supplier onboarding
- customer/KYC document review
- employee onboarding
- compliance document review
- contract/document approval
- insurance/claim supporting-document review
- reimbursement attachment review

The product intentionally does **not** bind itself to one industry. Its reusable domain model is:

> **Case + Document + Checklist Template + Review Task + Audit Timeline**

The end-to-end workflow is:

> **Create Case → Upload Documents → Automated Validation → Submit → Human Review → Approve / Reject / Request Information → Resubmit**

---

## 2. Product Problem

Common enterprise document-review workflows suffer from:

1. Documents being scattered across email and chat.
2. No consistent application/case status.
3. Missing documents being discovered manually.
4. Repetitive validation taking reviewer time.
5. No structured resubmission flow.
6. Weak auditability.
7. Tight coupling between processing steps.
8. Lost or duplicated processing tasks during failures.
9. Difficulty scaling asynchronous workloads.
10. Difficulty adding AI assistance later without redesigning the system.

DocFlow addresses these problems using a serverless, asynchronous, event-driven architecture.

---

## 3. Product Principles

### 3.1 Serverless-first

The first production-ready portfolio version uses:

- Amazon CloudFront
- Amazon S3
- Amazon Cognito
- Amazon API Gateway
- AWS Lambda
- Amazon DynamoDB
- Amazon EventBridge
- Amazon SQS
- AWS Step Functions
- Amazon SES
- Amazon CloudWatch
- AWS X-Ray
- Terraform
- GitHub Actions

The MVP intentionally avoids EKS, ECS, RDS, OpenSearch, Aurora, and Bedrock.

### 3.2 Checklist-driven review

A review is not simply an Approve/Reject button.

Each `caseType` points to a versioned Checklist Template defining:

- required document types
- required checks
- optional checks
- reviewer instructions

This allows the same platform to support multiple business processes without rewriting the workflow.

### 3.3 Human-in-the-loop

Automated processing validates technical and structural requirements.

A human reviewer remains responsible for the final business decision.

The first project does **not** implement AI auto-approval.

### 3.4 Clear separation of orchestration and events

**Step Functions** owns the deterministic lifecycle of one submitted Case.

**EventBridge** distributes facts that have already happened to independent subscribers.

Example:

- Step Functions: `Validate Case → Create Review Task → Wait for Reviewer → Finalize Decision`
- EventBridge: `CaseApproved` can independently trigger notifications, analytics, and future integrations.

### 3.5 Reliable asynchronous processing

All asynchronous consumers must support:

- retries
- dead-letter queues
- idempotency
- correlation IDs
- structured logging

Domain events are published through a transactional outbox so a committed business state cannot silently lose its corresponding event.

---

## 4. Scope

### 4.1 MVP

The MVP includes:

- Cognito authentication
- requester/reviewer/admin roles
- Case creation and listing
- versioned checklist templates
- S3 presigned uploads
- document metadata tracking
- asynchronous document validation
- SQS retry and DLQ
- Case submission validation
- Step Functions Standard workflow
- human review task
- reviewer claim/start/decision
- Approve
- Reject
- Request More Information
- Resubmit
- immutable audit timeline
- domain-event outbox
- notification queue and email adapter
- CloudWatch logs/metrics/alarms
- X-Ray tracing
- Terraform
- GitHub Actions
- automated tests

### 4.2 Post-MVP hardening

Add after the main workflow is stable:

- malware scanning and quarantine
- WebSocket real-time status
- SLA escalation
- EventBridge archive/replay
- admin DLQ redrive UI
- WAF/rate limiting
- multi-environment deployment
- document version history UI

### 4.3 Project 2 / AI scope

The following remain outside Project 1:

- Amazon Bedrock
- RAG
- vector databases
- OCR/semantic extraction
- LLM-generated recommendations
- AI confidence scoring
- AI agents
- automatic regulatory decisions

These will be added as a separate AI engineering layer without changing the core Case workflow.

---

## 5. Personas

### Requester

Can:

- create a Case
- view own Cases
- upload/delete allowed documents
- submit
- view status
- view information requests
- resubmit
- view final decision

Cannot:

- view another user's Case
- view internal reviewer comments
- change review decisions

### Reviewer

Can:

- view available review queue
- claim a task
- view assigned tasks
- start review
- view Case documents/checklist
- record checklist findings
- add internal comments
- Approve
- Reject
- Request More Information

### Admin

Can:

- view all Cases
- view all Review Tasks
- view operational metrics
- inspect audit trails
- inspect DLQs
- manage checklist templates
- manage role assignments

---

## 6. Core Entities

### Case

Represents one business application/review unit.

Key fields:

- `caseId`
- `caseType`
- `requesterId`
- `status`
- `checklistTemplateId`
- `checklistTemplateVersion`
- `submissionAttempt`
- `workflowExecutionArn`
- `decision`
- `decisionReason`
- `createdAt`
- `submittedAt`
- `updatedAt`

### Document

Represents one uploaded file.

Key fields:

- `documentId`
- `caseId`
- `documentType`
- `fileName`
- `fileSize`
- `mimeType`
- `s3Key`
- `sha256`
- `status`
- `validationStatus`
- `scanStatus`
- `version`
- `uploadedAt`
- `processedAt`

### Checklist Template

Versioned definition of a review process.

Contains:

- case type
- required document types
- review checks
- reviewer instructions
- active version

### Review Task

Represents one human review attempt.

Key fields:

- `taskId`
- `caseId`
- `attempt`
- `reviewerId`
- `status`
- `priority`
- `dueAt`
- `workflowTaskToken`
- `decision`
- `decisionReason`
- `createdAt`
- `startedAt`
- `completedAt`

### Audit Event

Immutable business activity record.

Contains:

- `auditId`
- `caseId`
- `actorId`
- `actorType`
- `action`
- `resourceType`
- `resourceId`
- `previousState`
- `newState`
- `correlationId`
- `timestamp`

---

## 7. State Models

### Case states

```text
DRAFT
  ↓
SUBMITTED
  ↓
PROCESSING
  ↓
REVIEW_PENDING
  ↓
IN_REVIEW
  ├──→ APPROVED
  ├──→ REJECTED
  └──→ NEEDS_INFORMATION
           ↓
        RESUBMITTED
           ↓
        SUBMITTED
           ↓
        PROCESSING
```

`RESUBMITTED` is an event/action, not a long-lived persisted state. The persisted Case transitions back to `SUBMITTED`; the workflow then enters `PROCESSING` (ADR-016, TASK-013 resolution).

### Document states

Document removal is a soft delete: while a Case is DRAFT or NEEDS_INFORMATION,
the owner requester or admin can move a document to terminal DELETED metadata.
The active document list hides it, while original metadata and audit history remain.
Replacement creates a new document identity. S3 byte retention is separate; deletion
does not revoke an already issued upload URL. See ADR-011 for the implementation.


```text
REGISTERED
   ↓
UPLOADING
   ↓
UPLOADED
   ↓
VALIDATING
   ├──→ VALID
   └──→ INVALID
```

Future hardening adds:

```text
SCANNING
  ├──→ SAFE
  └──→ QUARANTINED
```

### Review Task states

```text
PENDING
  ↓
CLAIMED
  ↓
IN_PROGRESS
  ↓
COMPLETED
```

Possible terminal review decisions:

- `APPROVE`
- `REJECT`
- `REQUEST_INFORMATION`

---

## 8. Core User Flows

### Create Case

1. Requester selects a Case Type.
2. Backend resolves the active Checklist Template version.
3. Backend creates the Case in `DRAFT`.
4. System writes an audit entry.
5. System writes a `CaseCreated` outbox event.

### Upload Document

1. Requester requests an upload URL.
2. Backend validates Case ownership/state/document type.
3. Backend creates a Document metadata record.
4. Backend returns an S3 presigned PUT URL.
5. Browser uploads directly to S3.
6. S3 Object Created event reaches EventBridge default bus.
7. Rule routes the event to `document-processing-queue`.
8. Document Processor validates metadata/content constraints.
9. Document becomes `VALID` or `INVALID`.
10. State change and corresponding domain event are written transactionally.

### Submit Case

1. Requester calls Submit.
2. Backend verifies:
   - Case is in allowed state.
   - all required document types exist.
   - required documents are `VALID`.
   - no document is still processing.
3. Backend sets Case to `SUBMITTED`, increments attempt, writes audit/outbox.
4. Backend starts Step Functions execution.
5. Workflow defensively revalidates the Case.
6. Workflow creates a Review Task and waits for human callback.

### Human Review

1. Reviewer sees an unassigned task.
2. Reviewer claims it using a conditional write.
3. Reviewer starts review.
4. Reviewer completes checklist findings.
5. Reviewer submits one decision:
   - Approve
   - Reject
   - Request Information
6. Backend persists the decision and calls the Step Functions callback.
7. Workflow finalizes the Case.
8. Domain events trigger notification subscribers.

### Resubmit

1. Requester reads requested information.
2. Requester uploads replacements/additional files.
3. Requester calls Resubmit.
4. System validates the updated document set.
5. Submission attempt increments.
6. A new Step Functions execution begins.
7. A new Review Task is created while previous task/history remains immutable.

---

## 9. Functional Requirements

### Authentication & authorization

- JWT authentication through Cognito.
- API Gateway validates tokens.
- Lambda enforces role and resource ownership.
- Requester cannot access other requesters' Cases.
- Reviewer endpoints require reviewer/admin role.
- Admin endpoints require admin role.

### Checklist templates

- Template versions are immutable after activation.
- Existing Cases remain bound to the template version active at Case creation.
- A template defines required documents and review checks.

### Document upload

- Backend generates short-lived presigned URLs.
- Client uploads directly to S3.
- Backend never proxies document bodies.
- Object keys are generated by the backend.
- User-provided file names are metadata only.
- Public S3 access is disabled.

### Document validation

MVP automated validation includes:

- allowed MIME types
- file-size limits
- extension/MIME consistency checks
- required metadata
- SHA-256/hash recording
- document type allowed by template
- duplicate upload handling

### Review

- Claim must be atomic to prevent two reviewers claiming one task.
- A reviewer can decide only an assigned active task.
- Reject and Request Information require a reason.
- Request Information includes structured missing/invalid items.

### Audit

Every state-changing action records an immutable audit entry.

### Notifications

Notification service listens to domain events and supports:

- review ready
- request information
- approval
- rejection
- future SLA escalation

Email is the MVP adapter.

---

## 10. Non-Functional Requirements

### Reliability

- SQS consumers must be idempotent.
- All queues must have DLQs.
- Domain events use a transactional outbox.
- No business operation may depend on a best-effort fire-and-forget event.

### Security

- S3 Block Public Access.
- encryption at rest.
- TLS in transit.
- least-privilege IAM.
- presigned URL expiration.
- server-side authorization.
- no credentials in source control.
- sensitive values excluded/redacted from logs.

### Observability

Every request/event should carry:

- `correlationId`
- `caseId` when applicable
- `eventId` when applicable

Metrics include:

- submitted Cases
- processing failures
- pending review count
- average review duration
- DLQ depth
- workflow failures

### Cost

The architecture is optimized for portfolio/dev usage and should avoid always-on compute in the MVP.

User-approved development plan (2026-09-15, ADR-007): develop/test locally first, then
use an explicitly authorized short-lived AWS environment for consolidated acceptance
and approved cleanup. A continuously running demo is not required for development.
Product success criteria below still require real end-to-end evidence in TASK-021;
local task completion alone does not establish portfolio readiness.

---

## 11. Success Criteria

The project is considered portfolio-ready when:

1. A Requester can complete the full Case lifecycle.
2. Document processing is asynchronous.
3. Retries do not create duplicate business effects.
4. Review claims are race-safe.
5. Human decisions resume a waiting workflow.
6. Audit history is complete.
7. Failed asynchronous messages can be inspected/redriven.
8. Infrastructure can be recreated from Terraform.
9. CI validates code and infrastructure.
10. The developer can explain why each AWS service exists.

---

## 12. Architecture Decisions to Defend in Interviews

The implementation must make it possible to answer:

- Why presigned S3 upload instead of API Gateway file upload?
- Why SQS between EventBridge and processing Lambda?
- Why Step Functions and EventBridge are both needed?
- Why a custom domain event bus is separate from AWS service events?
- Why Standard Step Functions is used for human review?
- How is duplicate SQS delivery handled?
- How are document-review races prevented?
- How is the database/event dual-write problem handled?
- Why is AI excluded from Project 1?
- How can Project 2 add AI without redesigning the workflow?

### TASK-010 validation boundary

The local processor now persists uploaded/validating/valid/invalid stages with audit
and atomic validation-event intent. Validation checks size, declared MIME, extension,
required metadata and PDF/JPEG/PNG signatures, and calculates SHA-256 by streaming.
It does not claim malware scanning or complete file-format parsing. Duplicate events
do not repeat business effects; deleted documents cannot be resurrected. Technical
failures retry through SQS/DLQ, separately from business INVALID results. See ADR-013.


## TASK-016 review command clarification

Reviewer/admin users can claim available tasks. Start and checklist changes require
the authenticated user to be the assigned reviewer; admin inspection does not grant
an ownership bypass (ADR-019). Claim, start and findings are transactionally audited.
Repeated active operations do not create duplicate audit/events; stale/closed tasks
cannot be edited. Reviewer comments remain internal and do not enter domain events.


## TASK-017 review decision clarification

The assigned reviewer, including an admin who claimed the task, submits one final
decision after completing required checks. Rejection and information requests need
a reason; information requests include structured items for bound document types.
Decision retries cannot create another decision. A saved decision may temporarily
await callback recovery; the API distinguishes retry-needed 503 from delivery
accepted 202. Case finalization is asynchronous. Completed findings/decisions remain
immutable and technical workflow failure does not imply business rejection.
TASK-018 verifies the full information-request/resubmission journey (ADR-020).


## TASK-019 notification delivery boundary

Review-ready email targets one configured reviewer mailbox. Information-request,
approval and rejection emails target the enabled requester's verified Cognito
email. They reference the recorded Case event and direct users to sign in; they
do not carry document content or reviewer reasoning. Email failures retry through
SQS/DLQ independently of Case state. Completed event delivery is deduplicated,
with a documented possible repeat after uncertain SES acceptance (ADR-021).
Live email delivery remains part of TASK-021 acceptance.
