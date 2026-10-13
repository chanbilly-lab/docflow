"""Attempt-scoped workflow transitions with transactional audit and failure facts."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from common.cases.repository import CaseRepository
from common.cases.workflow import canonical
from common.templates.repository import TemplateRepository, encode


def matching(repo: CaseRepository, event: dict[str, Any]) -> dict[str, Any] | None:
    submission = event.get("submission")
    execution = event.get("executionArn")
    if not isinstance(submission, dict) or not isinstance(execution, str):
        return None
    case_id = submission.get("caseId")
    if not isinstance(case_id, str) or not re.fullmatch(r"c_[A-Za-z0-9_-]{1,100}", case_id):
        return None
    case = repo.get(case_id)
    if (
        canonical(submission) != canonical(case.get("workflowInput"))
        or case["submissionAttempt"] != submission.get("attempt")
        or not execution.endswith(":" + case.get("workflowExecutionName", "!"))
        or not re.fullmatch(
            r"arn:[a-z-]+:states:[a-z0-9-]+:[0-9]{12}:execution:[A-Za-z0-9_-]+:case-[a-f0-9]{64}",
            execution,
        )
        or (
            case.get("workflowExecutionId") is not None and case["workflowExecutionId"] != execution
        )
    ):
        return None
    return case


def transition(
    repo: CaseRepository, case: dict[str, Any], state: str, event: dict[str, Any]
) -> None:
    now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    audit_id = "a_" + uuid4().hex
    failure = state == "WORKFLOW_FAILED"
    code = "WORKFLOW_TECHNICAL_FAILURE" if failure else None
    values = {
        ":before": case["status"],
        ":after": state,
        ":version": case["version"],
        ":attempt": case["submissionAttempt"],
        ":input": case["workflowInput"],
        ":now": now,
        ":one": 1,
        ":gsi": "CASE_STATUS#" + state,
        ":sort": f"UPDATED#{now}#{case['caseId']}",
    }
    condition = (
        "#s = :before AND #v = :version AND submissionAttempt = :attempt AND workflowInput = :input"
    )
    update = "SET #s = :after, updatedAt = :now, GSI2PK = :gsi, GSI2SK = :sort ADD #v :one"
    if failure:
        values[":failure"] = {"code": code, "occurredAt": now, "attempt": case["submissionAttempt"]}
        update = update.replace(" ADD", ", workflowFailure = :failure ADD")
    else:
        if "documentRevision" in case:
            condition += " AND documentRevision = :revision"
            values[":revision"] = case["documentRevision"]
        else:
            condition += " AND attribute_not_exists(documentRevision)"
    audit = {
        "PK": case["PK"],
        "SK": f"AUDIT#{now}#{audit_id}",
        "entityType": "AUDIT",
        "auditId": audit_id,
        "caseId": case["caseId"],
        "actorType": "SYSTEM",
        "actorId": "workflow-failure-handler" if failure else "workflow-validate-case",
        "action": "CASE_WORKFLOW_FAILED" if failure else "CASE_PROCESSING",
        "resourceType": "CASE",
        "resourceId": case["caseId"],
        "previousState": case["status"],
        "newState": state,
        "timestamp": now,
        "correlationId": case["workflowInput"]["correlationId"],
        "attempt": case["submissionAttempt"],
    }
    rows = [audit]
    if failure:
        event_id = "evt_" + hashlib.sha256((event["executionArn"] + ":failed").encode()).hexdigest()
        detail = {
            "eventId": event_id,
            "eventVersion": "1.0",
            "occurredAt": now,
            "caseId": case["caseId"],
            "correlationId": audit["correlationId"],
            "actor": {"type": "SYSTEM", "id": "workflow-failure-handler"},
            "data": {"attempt": case["submissionAttempt"], "failureCode": code},
        }
        rows.append(
            {
                "PK": case["PK"],
                "SK": "OUTBOX#" + event_id,
                "entityType": "OUTBOX",
                "eventId": event_id,
                "eventType": "CaseWorkflowFailed",
                "eventVersion": "1.0",
                "source": "docflow.case",
                "caseId": case["caseId"],
                "correlationId": detail["correlationId"],
                "detail": detail,
                "status": "PENDING",
                "createdAt": now,
            }
        )
    writes: list[Any] = [
        {
            "Update": {
                "TableName": repo.table_name,
                "Key": encode({"PK": case["PK"], "SK": "CASE"}),
                "UpdateExpression": update,
                "ConditionExpression": condition,
                "ExpressionAttributeNames": {"#s": "status", "#v": "version"},
                "ExpressionAttributeValues": encode(values),
            }
        }
    ]
    if failure:
        # Late import avoids the creation/matching module cycle.
        from common.reviews.commands import change
        from common.reviews.commands import condition as task_condition
        from common.reviews.creation import task_id
        from common.templates.repository import decode

        identifier = task_id(case["caseId"], int(case["submissionAttempt"]))
        found = repo.client.get_item(
            TableName=repo.table_name,
            Key=encode({"PK": case["PK"], "SK": "TASK#" + identifier}),
            ConsistentRead=True,
        )
        if "Item" in found:
            task = decode(found["Item"])
            if task["workflowExecutionArn"] != event["executionArn"]:
                raise ValueError("Failure task identity mismatch")
            writes.append(
                {
                    "Update": change(
                        task_condition(
                            repo,
                            task,
                            ["status", "decision", "callbackStatus", "callbackGeneration"],
                        ),
                        {
                            "status": "COMPLETED",
                            "workflowFailedAt": now,
                            "completedAt": task.get("completedAt", now),
                            "callbackStatus": "DELIVERED"
                            if task.get("callbackStatus") == "DELIVERED"
                            else "FAILED",
                            "GSI1SK": f"TASK#COMPLETED#DUE#{task['dueAt']}#{identifier}",
                        },
                    )
                }
            )
            rows.append(
                {
                    **audit,
                    "SK": audit["SK"] + "#TASK",
                    "auditId": audit_id + "_task",
                    "action": "REVIEW_WORKFLOW_FAILED",
                    "resourceType": "REVIEW_TASK",
                    "resourceId": identifier,
                    "previousState": task["status"],
                    "newState": "COMPLETED",
                }
            )
    writes.extend(
        {
            "Put": {
                "TableName": repo.table_name,
                "Item": encode(row),
                "ConditionExpression": "attribute_not_exists(PK)",
            }
        }
        for row in rows
    )
    repo.client.transact_write_items(TransactItems=writes)


def validate(repo: CaseRepository, event: dict[str, Any]) -> dict[str, Any]:
    case = matching(repo, event)
    if case is None or case["status"] not in {"SUBMITTED", "PROCESSING"}:
        return {"valid": False}
    intent = case["workflowInput"]
    if (
        case["checklistTemplateId"] != intent["checklistTemplateId"]
        or case["checklistTemplateVersion"] != intent["checklistTemplateVersion"]
        or case.get("documentRevision", 0) != intent["documentRevision"]
    ):
        return {"valid": False}
    template = TemplateRepository(repo.client, repo.table_name).get_version(
        case["checklistTemplateId"], int(case["checklistTemplateVersion"])
    )
    docs = [d for d in repo.related(case["caseId"], "DOC#") if d["status"] != "DELETED"]
    if set(template.required_documents) - {d["documentType"] for d in docs} or any(
        d["status"] != "VALID" or d.get("validationStatus") != "VALID" for d in docs
    ):
        return {"valid": False}
    if case["status"] == "SUBMITTED":
        transition(repo, case, "PROCESSING", event)
    return {
        "valid": True,
        "caseId": case["caseId"],
        "attempt": int(case["submissionAttempt"]),
        "checklistTemplateId": template.template_id,
        "checklistTemplateVersion": template.version,
    }


def fail(repo: CaseRepository, event: dict[str, Any]) -> dict[str, Any]:
    case = matching(repo, event)
    if case is None or case["status"] not in {
        "SUBMITTED",
        "PROCESSING",
        "REVIEW_PENDING",
        "IN_REVIEW",
    }:
        return {"recorded": False}
    transition(repo, case, "WORKFLOW_FAILED", event)
    return {"recorded": True}
