"""Atomic submission acceptance; workflow initiation follows commit."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from botocore.exceptions import ClientError

from common.cases.repository import ApiError, CaseRepository
from common.templates.repository import TemplateRepository, decode, encode

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef


def submission_key(value: object) -> str:
    try:
        if not isinstance(value, str) or len(value) != 36:
            raise ValueError
        parsed = UUID(value)
        if str(parsed) != value.lower():
            raise ValueError
        return str(parsed)
    except ValueError as exc:
        raise ApiError(400, "IDEMPOTENCY_KEY_INVALID", "Supply a UUID Idempotency-Key.") from exc


def submit(
    repo: CaseRepository,
    case_id: str,
    actor: str,
    groups: set[str],
    operation: str,
    key: str,
    correlation: str,
) -> dict[str, Any]:
    key = submission_key(key)
    if not groups & {"requester", "admin"}:
        raise ApiError(403, "FORBIDDEN", "Case submission is not permitted.")
    case = repo.get(case_id)
    if "admin" not in groups and case["requesterId"] != actor:
        raise ApiError(404, "CASE_NOT_FOUND", "Case not found.")
    digest = hashlib.sha256(json.dumps([case_id, actor, key]).encode()).hexdigest()
    receipt_key = {"PK": "IDEMPOTENCY#case-submission", "SK": "EVENT#" + digest}

    def replay() -> dict[str, Any] | None:
        found = repo.client.get_item(
            TableName=repo.table_name, Key=encode(receipt_key), ConsistentRead=True
        )
        if "Item" not in found:
            return None
        receipt = decode(found["Item"])
        if receipt["operation"] != operation:
            raise ApiError(409, "IDEMPOTENCY_KEY_REUSED", "Use a new key for this operation.")
        result: dict[str, Any] = receipt["response"]
        return result

    if previous := replay():
        return previous
    expected = {"submit": "DRAFT", "resubmit": "NEEDS_INFORMATION"}.get(operation)
    prior_attempt = int(case["submissionAttempt"])
    if (
        expected is None
        or case["status"] != expected
        or (operation == "submit" and prior_attempt != 0)
        or (operation == "resubmit" and prior_attempt < 1)
    ):
        raise ApiError(409, "CASE_INVALID_STATE", "Case does not allow this submission.")
    template = TemplateRepository(repo.client, repo.table_name).get_version(
        case["checklistTemplateId"], int(case["checklistTemplateVersion"])
    )
    documents = [doc for doc in repo.related(case_id, "DOC#") if doc["status"] != "DELETED"]
    if set(template.required_documents) - {doc["documentType"] for doc in documents}:
        raise ApiError(422, "REQUIRED_DOCUMENT_MISSING", "Supply all required document types.")
    if any(
        doc["status"] == "INVALID" or doc.get("validationStatus") == "INVALID" for doc in documents
    ):
        raise ApiError(422, "DOCUMENT_INVALID", "Remove or replace invalid documents.")
    if any(doc["status"] != "VALID" or doc.get("validationStatus") != "VALID" for doc in documents):
        raise ApiError(422, "DOCUMENT_NOT_READY", "Wait for all active documents to validate.")
    attempt = int(case["submissionAttempt"]) + 1
    now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    event_id, audit_id = "evt_" + uuid4().hex, "a_" + uuid4().hex
    kind = "CaseSubmitted" if operation == "submit" else "CaseResubmitted"
    revision = int(case.get("documentRevision", 0))
    response = {
        "caseId": case_id,
        "status": "SUBMITTED",
        "attempt": attempt,
        "workflowExecutionId": None,
    }
    workflow_input = {
        "caseId": case_id,
        "attempt": attempt,
        "checklistTemplateId": case["checklistTemplateId"],
        "checklistTemplateVersion": int(case["checklistTemplateVersion"]),
        "documentRevision": revision,
        "correlationId": correlation,
    }
    # Store the exact intended input/name once; HTTP retries never regenerate them.
    name = "case-" + hashlib.sha256(json.dumps([case_id, attempt]).encode()).hexdigest()
    updated = {
        **case,
        "status": "SUBMITTED",
        "submissionAttempt": attempt,
        "version": int(case["version"]) + 1,
        "updatedAt": now,
        "GSI2PK": "CASE_STATUS#SUBMITTED",
        "GSI2SK": f"UPDATED#{now}#{case_id}",
        "workflowStartStatus": "PENDING",
        "workflowSubmittedAt": now,
        "workflowExecutionName": name,
        "workflowInput": workflow_input,
        "workflowExecutionId": None,
    }
    audit = {
        "PK": case["PK"],
        "SK": f"AUDIT#{now}#{audit_id}",
        "entityType": "AUDIT",
        "auditId": audit_id,
        "caseId": case_id,
        "actorId": actor,
        "actorType": "USER",
        "action": "CASE_SUBMITTED" if operation == "submit" else "CASE_RESUBMITTED",
        "resourceType": "CASE",
        "resourceId": case_id,
        "previousState": case["status"],
        "newState": "SUBMITTED",
        "timestamp": now,
        "correlationId": correlation,
        "attempt": attempt,
    }
    detail = {
        "eventId": event_id,
        "eventVersion": "1.0",
        "occurredAt": now,
        "correlationId": correlation,
        "caseId": case_id,
        "actor": {"type": "USER", "id": actor},
        "data": {
            "attempt": attempt,
            "caseType": case["caseType"],
            "requesterId": case["requesterId"],
            "checklistTemplateId": case["checklistTemplateId"],
            "checklistTemplateVersion": int(case["checklistTemplateVersion"]),
            "documentRevision": revision,
        },
    }
    outbox = {
        "PK": case["PK"],
        "SK": f"OUTBOX#{event_id}",
        "entityType": "OUTBOX",
        "eventId": event_id,
        "eventType": kind,
        "eventVersion": "1.0",
        "source": "docflow.case",
        "correlationId": correlation,
        "caseId": case_id,
        "status": "PENDING",
        "detail": detail,
        "createdAt": now,
    }
    receipt = {
        **receipt_key,
        "entityType": "IDEMPOTENCY",
        "status": "COMPLETED",
        "operation": operation,
        "response": response,
        "processedAt": now,
    }
    revision_condition = (
        "documentRevision = :revision"
        if "documentRevision" in case
        else "attribute_not_exists(documentRevision)"
    )
    values = {
        ":state": expected,
        ":version": case["version"],
        ":owner": case["requesterId"],
        ":attempt": case["submissionAttempt"],
    }
    if "documentRevision" in case:
        values[":revision"] = revision
    writes: list[TransactWriteItemTypeDef] = [
        {
            "Put": {
                "TableName": repo.table_name,
                "Item": encode(updated),
                "ConditionExpression": (
                    "#s = :state AND #v = :version AND requesterId = :owner "
                    "AND submissionAttempt = :attempt AND " + revision_condition
                ),
                "ExpressionAttributeNames": {"#s": "status", "#v": "version"},
                "ExpressionAttributeValues": encode(values),
            }
        }
    ]
    writes.extend(
        {
            "Put": {
                "TableName": repo.table_name,
                "Item": encode(row),
                "ConditionExpression": "attribute_not_exists(PK)",
            }
        }
        for row in (audit, outbox, receipt)
    )
    try:
        repo.client.transact_write_items(TransactItems=writes)
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "TransactionCanceledException" and any(
            reason.get("Code") in {"ConditionalCheckFailed", "TransactionConflict"}
            for reason in exc.response.get("CancellationReasons", [])
        ):
            if previous := replay():
                return previous
            raise ApiError(409, "SUBMISSION_CONFLICT", "Case or documents changed; retry.") from exc
        raise
    return response
