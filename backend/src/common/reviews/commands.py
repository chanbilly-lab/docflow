"""Assigned review transitions with atomic audit/outbox and optimistic finding writes."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from botocore.exceptions import ClientError

from common.cases.repository import ApiError, CaseRepository, public
from common.reviews.creation import put
from common.reviews.query import get_task
from common.templates.repository import decode, encode

RESULTS = {"NOT_REVIEWED", "PASS", "FAIL", "NOT_APPLICABLE"}


def condition(repo: CaseRepository, row: dict[str, Any], fields: list[str]) -> Any:
    names, values, terms = {}, {}, []
    for i, field in enumerate(fields):
        name, value = f"#n{i}", f":v{i}"
        names[name] = field
        if field in row:
            values[value] = row[field]
            terms.append(f"{name} = {value}")
        else:
            terms.append(f"attribute_not_exists({name})")
    return {
        "TableName": repo.table_name,
        "Key": encode({"PK": row["PK"], "SK": row["SK"]}),
        "ConditionExpression": " AND ".join(terms),
        "ExpressionAttributeNames": names,
        "ExpressionAttributeValues": encode(values),
    }


def change(guard: Any, changes: dict[str, Any], increments: dict[str, int] | None = None) -> Any:
    sets, adds = [], []
    for i, (field, value) in enumerate(changes.items()):
        name, marker = f"#set{i}", f":set{i}"
        guard["ExpressionAttributeNames"][name] = field
        guard["ExpressionAttributeValues"].update(encode({marker: value}))
        sets.append(f"{name} = {marker}")
    for i, (field, value) in enumerate((increments or {}).items()):
        name, marker = f"#add{i}", f":add{i}"
        guard["ExpressionAttributeNames"][name] = field
        guard["ExpressionAttributeValues"].update(encode({marker: value}))
        adds.append(f"{name} {marker}")
    guard["UpdateExpression"] = ("SET " + ", ".join(sets) if sets else "") + (
        " ADD " + ", ".join(adds) if adds else ""
    )
    return guard


def transact(repo: CaseRepository, writes: list[Any], operation: str) -> None:
    try:
        repo.client.transact_write_items(TransactItems=writes)
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "TransactionCanceledException" and any(
            reason.get("Code") in {"ConditionalCheckFailed", "TransactionConflict"}
            for reason in exc.response.get("CancellationReasons", [])
        ):
            code = "REVIEW_TASK_ALREADY_CLAIMED" if operation == "claim" else "REVIEW_CONFLICT"
            raise ApiError(409, code, "Review changed; refresh and retry.") from None
        raise


def execute(
    repo: CaseRepository,
    identifier: str,
    actor: str,
    groups: set[str],
    operation: str,
    payload: dict[str, Any],
    correlation: str,
    check_id: str = "",
) -> dict[str, Any]:
    if not groups & {"reviewer", "admin"}:
        raise ApiError(403, "FORBIDDEN", "Reviewer or admin required.")
    if operation not in {"claim", "start", "check"}:
        raise ApiError(404, "ROUTE_NOT_FOUND", "Route not found.")
    if operation == "check":
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", check_id):
            raise ApiError(400, "CHECK_ID_INVALID", "Invalid check ID.")
        if (
            set(payload) - {"result", "comment"}
            or not isinstance(payload.get("result"), str)
            or payload["result"] not in RESULTS
            or (
                payload.get("comment") is not None
                and (not isinstance(payload["comment"], str) or len(payload["comment"]) > 2000)
            )
        ):
            raise ApiError(
                400, "REVIEW_INPUT_INVALID", "Supply a valid result and optional comment."
            )
    elif payload:
        raise ApiError(400, "REVIEW_INPUT_INVALID", "Supply an empty JSON object.")
    task = get_task(repo, identifier)
    owner = task.get("reviewerId")
    if operation == "claim":
        if owner is not None and not (owner == actor and task["status"] == "CLAIMED"):
            raise ApiError(409, "REVIEW_TASK_ALREADY_CLAIMED", "Review task already claimed.")
    elif owner != actor:
        raise ApiError(403, "REVIEW_TASK_NOT_ASSIGNED", "Only the assigned reviewer may act.")
    case = repo.get(task["caseId"])
    replay = (operation == "claim" and owner == actor and task["status"] == "CLAIMED") or (
        operation == "start" and task["status"] == "IN_PROGRESS"
    )
    expected_case = (
        "IN_REVIEW"
        if operation == "check" or (operation == "start" and replay)
        else "REVIEW_PENDING"
    )
    expected_task = (
        "IN_PROGRESS"
        if operation == "check"
        else "CLAIMED"
        if operation == "start" or replay
        else "PENDING"
    )
    if (
        case["submissionAttempt"] != task["attempt"]
        or case["status"] != expected_case
        or (not replay and task["status"] != expected_task)
    ):
        raise ApiError(409, "REVIEW_INVALID_STATE", "Review is not active for this operation.")
    case_guard = condition(repo, case, ["status", "version", "submissionAttempt"])
    task_guard = condition(repo, task, ["status", "reviewerId", "attempt"])
    checks: list[Any] = [{"ConditionCheck": case_guard}, {"ConditionCheck": task_guard}]
    if replay:
        transact(repo, checks, operation)
        return public(
            task, "taskId status reviewerId" if operation == "claim" else "taskId status startedAt"
        )
    now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    audit_id = "a_" + uuid4().hex
    audit = {
        "PK": case["PK"],
        "SK": f"AUDIT#{now}#{audit_id}",
        "entityType": "AUDIT",
        "auditId": audit_id,
        "caseId": case["caseId"],
        "actorType": "USER",
        "actorId": actor,
        "resourceType": "REVIEW_TASK",
        "resourceId": identifier,
        "taskId": identifier,
        "attempt": task["attempt"],
        "timestamp": now,
        "correlationId": correlation,
    }
    if operation == "claim":
        updates = {
            "status": "CLAIMED",
            "reviewerId": actor,
            "claimedAt": now,
            "GSI1PK": "REVIEWER#" + actor,
            "GSI1SK": f"TASK#CLAIMED#DUE#{task['dueAt']}#{identifier}",
        }
        checks[1] = {"Update": change(task_guard, updates)}
        audit.update(action="REVIEW_CLAIMED", previousState="PENDING", newState="CLAIMED")
        response = {"taskId": identifier, "status": "CLAIMED", "reviewerId": actor}
    elif operation == "start":
        checks[0] = {
            "Update": change(
                case_guard,
                {
                    "status": "IN_REVIEW",
                    "updatedAt": now,
                    "GSI2PK": "CASE_STATUS#IN_REVIEW",
                    "GSI2SK": f"UPDATED#{now}#{case['caseId']}",
                },
                {"version": 1},
            )
        }
        checks[1] = {
            "Update": change(
                task_guard,
                {
                    "status": "IN_PROGRESS",
                    "startedAt": now,
                    "GSI1SK": f"TASK#IN_PROGRESS#DUE#{task['dueAt']}#{identifier}",
                },
            )
        }
        audit.update(action="REVIEW_STARTED", previousState="REVIEW_PENDING", newState="IN_REVIEW")
        event_id = "evt_" + uuid4().hex
        data = {
            "taskId": identifier,
            "attempt": task["attempt"],
            "reviewerId": actor,
            "startedAt": now,
        }
        detail = {
            "eventId": event_id,
            "eventVersion": "1.0",
            "occurredAt": now,
            "caseId": case["caseId"],
            "correlationId": correlation,
            "actor": {"type": "USER", "id": actor},
            "data": data,
        }
        checks.append(
            put(
                repo,
                {
                    "PK": case["PK"],
                    "SK": "OUTBOX#" + event_id,
                    "entityType": "OUTBOX",
                    "eventId": event_id,
                    "eventVersion": "1.0",
                    "eventType": "ReviewStarted",
                    "source": "docflow.review",
                    "caseId": case["caseId"],
                    "correlationId": correlation,
                    "status": "PENDING",
                    "detail": detail,
                    "createdAt": now,
                },
            )
        )
        response = {"taskId": identifier, "status": "IN_PROGRESS", "startedAt": now}
    else:
        found = repo.client.get_item(
            TableName=repo.table_name,
            Key=encode({"PK": case["PK"], "SK": f"CHECK#{identifier}#{check_id}"}),
            ConsistentRead=True,
        )
        if "Item" not in found:
            raise ApiError(404, "CHECK_NOT_FOUND", "Checklist check not found.")
        check = decode(found["Item"])
        check_guard = condition(repo, check, ["entityType", "taskId", "checkId", "version"])
        if check["result"] == payload["result"] and check.get("comment") == payload.get("comment"):
            checks.append({"ConditionCheck": check_guard})
            transact(repo, checks, operation)
            return public(check, "checkId result updatedAt")
        checks[1] = {"Update": change(task_guard, {}, {"checkRevision": 1})}
        checks.append(
            {
                "Update": change(
                    check_guard,
                    {
                        "result": payload["result"],
                        "comment": payload.get("comment"),
                        "updatedBy": actor,
                        "updatedAt": now,
                    },
                    {"version": 1},
                )
            }
        )
        audit.update(
            action="CHECK_RESULT_UPDATED",
            resourceType="CHECK_RESULT",
            resourceId=check_id,
            previousState=check["result"],
            newState=payload["result"],
        )
        response = {"checkId": check_id, "result": payload["result"], "updatedAt": now}
    checks.append(put(repo, audit))
    transact(repo, checks, operation)
    return response
