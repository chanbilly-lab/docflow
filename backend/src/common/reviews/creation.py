"""Prepare immutable skeletons, then atomically publish one review per attempt."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from common.cases.repository import CaseRepository
from common.cases.workflow_state import matching
from common.templates.repository import TemplateRepository, decode, encode


def task_id(case_id: str, attempt: int) -> str:
    return f"t_{case_id}_{attempt}"


def audit(case: dict[str, Any], action: str, now: str, task: str) -> dict[str, Any]:
    identifier = "a_" + uuid4().hex
    return {
        "PK": case["PK"],
        "SK": f"AUDIT#{now}#{identifier}",
        "entityType": "AUDIT",
        "auditId": identifier,
        "caseId": case["caseId"],
        "actorType": "SYSTEM",
        "actorId": "workflow-create-review-task",
        "action": action,
        "resourceType": "REVIEW_TASK",
        "resourceId": task,
        "timestamp": now,
        "correlationId": case["workflowInput"]["correlationId"],
    }


def put(repo: CaseRepository, row: dict[str, Any]) -> Any:
    return {
        "Put": {
            "TableName": repo.table_name,
            "Item": encode(row),
            "ConditionExpression": "attribute_not_exists(PK)",
        }
    }


def guard(repo: CaseRepository, case: dict[str, Any]) -> Any:
    values = {":state": case["status"], ":v": case["version"], ":input": case["workflowInput"]}
    condition = "#s = :state AND #v = :v AND workflowInput = :input"
    if "documentRevision" in case:
        condition += " AND documentRevision = :revision"
        values[":revision"] = case["documentRevision"]
    else:
        condition += " AND attribute_not_exists(documentRevision)"
    return {
        "TableName": repo.table_name,
        "Key": encode({"PK": case["PK"], "SK": "CASE"}),
        "ConditionExpression": condition,
        "ExpressionAttributeNames": {"#s": "status", "#v": "version"},
        "ExpressionAttributeValues": encode(values),
    }


def create_review(repo: CaseRepository, event: dict[str, Any]) -> dict[str, Any]:
    case = matching(repo, event)
    token, retry = event.get("taskToken"), event.get("retryCount")
    if case is None or case["status"] not in {"PROCESSING", "REVIEW_PENDING", "IN_REVIEW"}:
        raise ValueError("Review creation state mismatch")
    if (
        not isinstance(token, str)
        or not 1 <= len(token) <= 2048
        or type(retry) is not int
        or not 0 <= retry <= 999999
    ):
        raise ValueError("Invalid callback context")
    entered = datetime.fromisoformat(event["enteredTime"])
    if entered.tzinfo is None:
        raise ValueError("Invalid callback time")
    generation = entered.astimezone(UTC).isoformat(timespec="microseconds") + f"#{retry:06}"
    identifier = task_id(case["caseId"], int(case["submissionAttempt"]))
    key = {"PK": case["PK"], "SK": "TASK#" + identifier}
    found = repo.client.get_item(TableName=repo.table_name, Key=encode(key), ConsistentRead=True)
    now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if "Item" in found:
        prior = decode(found["Item"])
        pending = (
            prior["status"] == "COMPLETED"
            and prior.get("callbackStatus") == "PENDING"
            and not prior.get("workflowFailedAt")
        )
        if prior["workflowExecutionArn"] != event["executionArn"] or (
            not pending
            and prior["status"]
            not in {
                "PENDING",
                "CLAIMED",
                "IN_PROGRESS",
            }
        ):
            raise ValueError("Review identity mismatch")
        if generation < prior["callbackGeneration"]:
            return {"taskId": identifier}
        if generation == prior["callbackGeneration"]:
            if token != prior["workflowTaskToken"]:
                raise ValueError("Callback generation conflict")
            return {"taskId": identifier}
        repo.client.transact_write_items(
            TransactItems=[
                {"ConditionCheck": guard(repo, case)},
                {
                    "Update": {
                        "TableName": repo.table_name,
                        "Key": encode(key),
                        "UpdateExpression": (
                            "SET workflowTaskToken = :token, callbackGeneration = :new"
                        ),
                        "ConditionExpression": "callbackGeneration = :old AND #s = :state"
                        + (
                            " AND callbackStatus = :pending"
                            " AND attribute_not_exists(workflowFailedAt)"
                            if pending
                            else ""
                        ),
                        "ExpressionAttributeNames": {"#s": "status"},
                        "ExpressionAttributeValues": encode(
                            {
                                **({":pending": "PENDING"} if pending else {}),
                                ":token": token,
                                ":new": generation,
                                ":old": prior["callbackGeneration"],
                                ":state": prior["status"],
                            }
                        ),
                    }
                },
                put(repo, audit(case, "REVIEW_CALLBACK_REFRESHED", now, identifier)),
            ]
        )
        return {"taskId": identifier}
    intent = case["workflowInput"]
    if (
        case["status"] != "PROCESSING"
        or case.get("documentRevision", 0) != intent["documentRevision"]
        or case["checklistTemplateId"] != intent["checklistTemplateId"]
        or case["checklistTemplateVersion"] != intent["checklistTemplateVersion"]
    ):
        raise ValueError("Review preparation mismatch")
    template = TemplateRepository(repo.client, repo.table_name).get_version(
        case["checklistTemplateId"], int(case["checklistTemplateVersion"])
    )
    prepared_at = case.get("workflowSubmittedAt", case["createdAt"])
    checks = [
        {
            "PK": case["PK"],
            "SK": f"CHECK#{identifier}#{check.check_id}",
            "entityType": "CHECK_RESULT",
            "taskId": identifier,
            "checkId": check.check_id,
            "order": check.order,
            "documentType": check.document_type,
            "required": check.required,
            "instructions": check.instructions,
            "result": "NOT_REVIEWED",
            "comment": None,
            "updatedBy": None,
            "updatedAt": prepared_at,
        }
        for check in template.checks
    ]
    existing = {row["SK"]: row for row in repo.related(case["caseId"], f"CHECK#{identifier}#")}
    if set(existing) - {row["SK"] for row in checks} or any(
        existing.get(row["SK"], row) != row for row in checks
    ):
        raise ValueError("Checklist preparation mismatch")
    missing = [row for row in checks if row["SK"] not in existing]
    if missing:
        repo.client.transact_write_items(
            TransactItems=[
                {"ConditionCheck": guard(repo, case)},
                *[put(repo, row) for row in missing],
            ]
        )
    due = (
        (datetime.fromisoformat(prepared_at) + timedelta(hours=48))
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )
    task = {
        **key,
        "entityType": "REVIEW_TASK",
        "taskId": identifier,
        "caseId": case["caseId"],
        "attempt": case["submissionAttempt"],
        "status": "PENDING",
        "reviewerId": None,
        "priority": "NORMAL",
        "dueAt": due,
        "createdAt": now,
        "decision": None,
        "workflowExecutionArn": event["executionArn"],
        "workflowTaskToken": token,
        "callbackGeneration": generation,
        "GSI1PK": "REVIEWER#UNASSIGNED",
        "GSI1SK": f"TASK#PENDING#DUE#{due}#{identifier}",
    }
    change = guard(repo, case)
    change["UpdateExpression"] = (
        "SET #s = :pending, updatedAt = :now, GSI2PK = :gsi, GSI2SK = :sort ADD #v :one"
    )
    change["ExpressionAttributeValues"].update(
        encode(
            {
                ":pending": "REVIEW_PENDING",
                ":now": now,
                ":gsi": "CASE_STATUS#REVIEW_PENDING",
                ":sort": f"UPDATED#{now}#{case['caseId']}",
                ":one": 1,
            }
        )
    )
    event_id = "evt_" + uuid4().hex
    detail = {
        "eventId": event_id,
        "eventVersion": "1.0",
        "occurredAt": now,
        "caseId": case["caseId"],
        "correlationId": intent["correlationId"],
        "actor": {"type": "SYSTEM", "id": "workflow-create-review-task"},
        "data": {
            "taskId": identifier,
            "attempt": case["submissionAttempt"],
            "priority": "NORMAL",
            "dueAt": due,
        },
    }
    fact = {
        "PK": case["PK"],
        "SK": "OUTBOX#" + event_id,
        "entityType": "OUTBOX",
        "eventId": event_id,
        "eventVersion": "1.0",
        "eventType": "CaseReadyForReview",
        "source": "docflow.case",
        "caseId": case["caseId"],
        "correlationId": intent["correlationId"],
        "status": "PENDING",
        "detail": detail,
        "createdAt": now,
    }
    record = {
        **audit(case, "CASE_READY_FOR_REVIEW", now, identifier),
        "previousState": "PROCESSING",
        "newState": "REVIEW_PENDING",
    }
    repo.client.transact_write_items(
        TransactItems=[
            {"Update": change},
            put(repo, task),
            put(repo, record),
            put(repo, fact),
        ]
    )
    return {"taskId": identifier}
