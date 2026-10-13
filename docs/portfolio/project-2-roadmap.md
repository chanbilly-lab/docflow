# Project 2: proposed AI assistance roadmap

Proposal only. Project 1 stays AI-free; no Bedrock, RAG, OpenSearch, model endpoint
or other service is added by TASK-022. Each stage needs its own requirements,
security/cost review and approved ADR before implementation or cloud writes.

| Stage | Deliverable | Gate before advancing |
| --- | --- | --- |
| 0 | Define one assistive task, e.g. extraction of required supplier fields | Evaluation dataset with permitted synthetic/redacted documents, baseline, success/cost targets |
| 1 | Offline extraction prototype behind a narrow adapter | Schema-valid output, source references, uncertainty/abstention and measured error categories |
| 2 | Asynchronous suggestion worker after deterministic validation | Idempotent version/attempt binding; no write access to decisions or workflow tokens |
| 3 | Reviewer-visible suggestions with citations | Human accept/edit/reject, provenance/version audit, no automatic approval |
| 4 | Optional retrieval of approved policy content | Document/tenant access isolation, versioned sources and retrieval evaluation |
| 5 | Bounded pilot | Reliability/security evidence, spend limits/kill switch, rollback and retention policy |

Treat document text and retrieved passages as untrusted data, never executable
instructions. Keep tools/actions allowlisted and segregate model input/output from
workflow commands. A prompt-injection attempt must not change assignment, expose
another Case or trigger a business decision. Do not send secrets or task tokens to
a model. Preserve deterministic file validation and existing human authorization.

Evaluation should report field precision/recall, citation correctness, unsupported
claims, refusal/abstention quality, adversarial-document behavior, latency and cost
per document. Compare against the deterministic/manual baseline on a held-out set.
Model choice, regional availability and prices must be rechecked when work begins;
this roadmap makes no current service purchase or performance promise.

Before any production pilot, revisit TASK-021's skipped security/reliability evidence
and integrate the frontend with real authentication/API flows. AI is not a shortcut
around those unfinished product and operational boundaries.
