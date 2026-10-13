# DocFlow | Document Review & Collaboration

English reference guide · 29 September 2026 · Project 1

## 1. What is this project for?

DocFlow organizes document collection, checklist review, human decisions and requests for additional information into a traceable case workflow. It helps a team answer four questions: what was submitted, who owns the review, what is missing, and why was the application approved or rejected?

The current example is **supplier onboarding**. An applicant provides company registration, director identification, bank account information and proof of address. A reviewer checks these against a defined checklist and approves, rejects or requests more information. The same model could inform employee onboarding, contract attachments or expense-document workflows. Those industry adaptations are not separately delivered products, and this project does not claim KYC or regulatory certification.

| Common problem | DocFlow approach |
| --- | --- |
| Documents scattered across messages and email | Link documents, requirements, tasks and history to one Case |
| Unclear progress | Explicit draft, pending review, in-review, information-needed and final states |
| Inconsistent review criteria | Bind each Case to an immutable checklist version |
| Earlier decisions disappear after resubmission | Preserve previous tasks, checks and audit records across attempts |
| Retries or simultaneous actions create duplicate work | Use durable idempotency records, conditional writes and transactions |

**Current delivery status:** backend business logic and infrastructure code are implemented. The interactive frontend is an in-memory demonstration without real authentication, uploads or API integration. A subset of real AWS journeys passed a short acceptance session; application resources were subsequently removed. This is a portfolio and engineering reference, not a ready-to-operate production service.

## 2. Who uses it?

| Role | Implemented backend responsibility |
| --- | --- |
| Requester | Create and read owned Cases; upload, submit and resubmit in permitted states |
| Reviewer | Inspect review queues, claim work, start a task, record checks and submit a decision |
| Admin | Perform authorized administrative inspection and Case commands; must still claim a task before review mutations |
| Background workers | Validate documents, progress workflows, deliver notifications and collect operational signals |

The demo uses a fixed synthetic identity. It does not demonstrate a real sign-in or role-switching implementation.

## 3. What has been implemented?

| Capability | Concrete implementation | Frontend demonstration |
| --- | --- | --- |
| Case management | Creation, queries, state transitions and ownership enforcement | New synthetic drafts, listing, search and status filters |
| Checklist templates | Immutable versions; new versions do not rewrite requirements on existing Cases | View an example template; no integrated editing or publishing UI |
| Private document upload | Backend-generated S3 keys and constrained presigned PUT requests | Document list and information dialog; no actual upload or PDF viewer |
| Asynchronous validation | S3 events routed through EventBridge/SQS; metadata, file-signature and SHA-256 checks | Illustrates document completeness, not an active validation engine |
| Submission and orchestration | Submission guards, durable replay records and Step Functions callback-based review | Starts from predefined synthetic case states |
| Claiming and checklist review | Transactional claims, assignment checks and optimistic version guards | Claim/start, required checkboxes and guarded approval button |
| Three review outcomes | Approval, rejection or request for information; persisted decisions and workflow finalization | Decision dialogs, reasons and local state changes |
| Resubmission | Replacement or additional documents, new attempt/task, preserved history | Information-needed state and reason; no integrated resubmission upload flow |
| Audit and events | Business state, audit and outbox intent committed together when events are required | Synthetic activity timeline rather than a live audit database |
| Email notifications | Review-ready, approval, rejection and information-request events; SES worker, retries and DLQ | No email is sent by the page |
| Reliability and operations | Consumer idempotency, partial batch failures, DLQs, pending-work recovery, logs/metrics/alarms | Demonstrated through backend evidence and infrastructure definitions |
| List export | Download the filtered synthetic frontend list as JSON | A local convenience feature, not a production reporting service |

Document validation is not antivirus scanning, full PDF parsing or semantic AI review. Project 1 is AI-free. OCR, RAG and AI assistance are future proposals only.

## 4. A visual walkthrough

All six screenshots were captured through actual interactions with the local React application on 29 September 2026. They contain fictional built-in data. The UI currently uses Traditional Chinese; the English captions explain the controls without implying that an English UI has been implemented.

### A. Overview and case navigation

![Workspace overview with status metrics, search, case list and document details](images/01-overview.png)

**Figure 1.** The left navigation opens Overview, Case Management and Review Tasks. The middle panel supports search and status filtering. The right panel shows the selected Case, its checklist version and document requirements. Metrics are computed from synthetic local state, not production activity.

### B. Claim a task and complete its checks

![Claimed review with four required checks completed](images/02-checklist.png)

**Figure 2.** Select DF-0248 and click “領取並開始示範審核” (Claim and start demo review). Complete all four required checks to enable approval. Real assignment and competing-claim protection belongs in the backend, not merely in a disabled button.

### C. Approve and inspect the activity history

![Approved case with creation, submission, review and decision history](images/03-approved-history.png)

**Figure 3.** After approval, the state and timeline reflect the decision. “歷程” means Activity history. This is a local UI result, not evidence of a new AWS execution.

### D. Request additional information

![Information-request dialog with a specific reason](images/04-request-information.png)

**Figure 4.** “要求補件” means Request information. The example asks for current proof of address consistent with the application. Rejection also requires a reason, so the outcome remains explainable.

![Information-needed case with its reason preserved in the timeline](images/05-information-history.png)

**Figure 5.** Confirmation moves the synthetic Case to Information needed and records the reason. Backend replacement/additional-document resubmission exists; it is not yet connected to this frontend.

### E. Create a new draft

![New synthetic case form with company and applicant fields](images/06-create-case.png)

**Figure 6.** Enter a company and applicant name to create a demo draft. The screenshot shows the form before submission. After submission, the new Case exists only in the page's memory and disappears on reload.

## 5. How does it work?

Business flow: Create Case → Upload documents → Asynchronous validation → Submit → Human review → Approve / Reject / Request information → Resubmit when required.

| Layer | Implementation and purpose |
| --- | --- |
| Demonstration UI | React, TypeScript and Vite; currently independent of the backend |
| Identity and API | Cognito and API Gateway HTTP API; Python 3.13 Lambda handlers enforce business authorization |
| Data and files | DynamoDB for state, audit and outbox; private S3 for document bytes |
| Asynchronous processing | EventBridge routing with SQS buffering, retries and dead-letter queues |
| Review orchestration | Step Functions Standard for one Case workflow; callback tokens remain in trusted backend components |
| Notifications and operations | SES; CloudWatch logs, metrics, alarms and dashboards; native X-Ray tracing |
| Infrastructure | Terraform; deployments require separate authorization and are not triggered by a GitHub push |

Several engineering patterns make this useful as a reference. Immutable templates protect historical criteria. A transactional outbox avoids a database/event dual-write gap. Conditional claims prevent two reviewers from owning the same active task. A new resubmission attempt preserves earlier evidence. Notification failure does not roll back a business decision. The system does not promise end-to-end exactly-once events or email: an uncertain SES acceptance followed by a crash can still result in a repeated message.

## 6. What has actually been verified?

| Scope | Evidence and limits |
| --- | --- |
| Local implementation | TASK-003 through TASK-020 passed local acceptance; this documentation work is not a fresh full-suite execution |
| Real AWS journeys | A short session on 29 September 2026 passed approval, rejection, replacement resubmission, additive resubmission and invalid-document rejection |
| Notifications | Twelve completed receipts established SES acceptance and persisted completion, not confirmed inbox delivery |
| Remaining work | Real frontend authentication/API/upload integration, plus broader browser, IAM, fault-injection, race and retention evidence |
| Long-duration tests | The owner omitted 24-hour/14-day and other long waits; omission is not PASS |
| Task state | TASK-021 remains BLOCKED with remaining acceptance skipped by owner choice; TASK-022 documentation is complete |
| Cloud status | Application resources and the state bucket were removed; two no-additional-cost SYSTEM backups await expiry. No permanent backend is running |

## 7. Run a local demonstration

Use Python 3.13 and Node 22.12 or later within the 22.x line. Initial dependency installation requires internet access. From the repository root on Windows:

```powershell
py -3.13 scripts/dev.py bootstrap
py -3.13 scripts/dev.py dev
```

Open the local address printed by Vite, normally `http://127.0.0.1:5173`. Run `py -3.13 scripts/dev.py check` separately for the local checks. On macOS/Linux, use `python3.13` instead of `py -3.13` with the required Node version on PATH.

Suggested five-minute sequence: overview and filtering → claim DF-0248 → complete four checks and approve → reload → claim the same Case and request information → inspect history → create a draft and export JSON. Reloading resets all demo changes. No AWS credentials are required and no email is sent.

A self-contained HTML edition embeds the screenshots for offline sharing. Markdown and original PNGs are suitable for GitHub review. The existing hosted preview may require the owner's sign-in; it should not be presented as a universally accessible public service.

## 8. Reference material

- [GitHub repository](https://github.com/chanbilly-lab/docflow)
- [Architecture and data flow](architecture.md), [security boundaries](security.md), [trade-offs](trade-offs.md)
- [Five real AWS journeys](../verification/TASK-021-20260929b-session.md)
- [Full acceptance ledger](../CLOUD_ACCEPTANCE.md), [current retirement evidence](../verification/AWS-RETIREMENT.md)
- [Chinese edition](guide-zh.md)

Use this as an engineering reference for event-driven document review. Production use still requires frontend/backend integration, security and capacity validation, and a newly authorized deployment plan.
