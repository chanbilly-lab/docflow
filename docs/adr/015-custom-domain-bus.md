# ADR-015 - Custom domain bus and envelope contracts

Status: Accepted
Date: 2026-09-16
Task: TASK-012

## Decision

Implement Technical Design 9.1 with a domain_events Terraform module creating
docflow-{env}-domain. Dev exports its actual name/ARN, passes that ARN to the
existing outbox publisher's environment/IAM, and enables its Stream mapping.
The resource reference establishes creation ordering; no hand-constructed bus ARN
or caller-identity lookup remains. This completes ADR-014's temporary disabled
mapping stage. Configuration enabled is not evidence of AWS deployment.

Raw S3 events remain on the default bus and existing document queue. Domain facts
remain on the custom bus. Do not add bus-forwarding rules or mix AWS source events
with domain facts. This module adds no public/cross-account resource policy,
archive, schema discovery or subscriber. Existing publisher identity IAM allows
PutEvents/DescribeEventBus on exactly the new bus. Command Lambdas retain no
publisher policy and no EventBridge calls. Future notification routing belongs
to TASK-019; subscriber-free EventBridge acceptance is not consumer delivery.

## Contracts

Keep existing detail schemas and producer payloads unchanged. Add
docs/events/domain-event.schema.json as the delivered EventBridge routing-envelope
contract. It binds source/detail-type to the corresponding existing detail schema:

| Source | Detail type | Detail schema |
| --- | --- | --- |
| docflow.case | CaseCreated | case-created.schema.json |
| docflow.document | DocumentValidated | document-validation.schema.json (VALID, no errors) |
| docflow.document | DocumentValidationFailed | document-validation.schema.json (INVALID, one or more errors) |

AWS transport fields may coexist with source/detail-type/detail. Detail retains
business eventId/eventVersion/occurredAt/correlationId/caseId/actor/data, with no
internal database keys. The schema ID under docflow.invalid is an offline identifier,
not a hosted endpoint. Tests register all references locally and explicitly check
timestamp syntax without an optional format package. These are repository contracts;
EventBridge does not automatically validate events against these JSON files.

Production publisher behavior, source allowlist and runtime dependencies are
unchanged. Any later event producer must extend its allowlist, the envelope schema
and contract tests together. Consumers deduplicate detail.eventId; bus transport
IDs are not business identity. ADR-014's at-least-once and 24-hour stream recovery
limits still apply.

## Verification

Moto integration exercises actual Case creation, document reservation/validation,
outbox publisher and SQS observation targets on two separate buses. Identical
observation patterns prove bus selection, rather than only pattern exclusion.
Observation queues/rules and synthetic aws.s3 events are local fixtures, not new
production resources or instructions to publish AWS sources live.

Provider-mocked tests verify actual module ARN wiring, enabled mapping and command
roles without publishing grants. AST guard enforces publication/client ownership
within the current backend; it is a regression guard, not an IAM/security proof.
Cloud bus isolation, policies, delivery and checkpoints remain NOT RUN, TASK-021.
No AWS resources were created or modified.
