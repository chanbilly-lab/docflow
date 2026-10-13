"""Scope-bound GSI queues, current authorization and explicit public DTOs."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from common.cases.repository import ApiError, CaseRepository, position_token, public, read_position
from common.templates.repository import decode, encode

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.type_defs import QueryInputTypeDef

STATES = {"PENDING", "CLAIMED", "IN_PROGRESS", "COMPLETED"}
TASK_PATTERN = r"t_(c_[A-Za-z0-9_-]{1,100})_([1-9][0-9]{0,9})"
FIELDS = "taskId caseId attempt status reviewerId priority dueAt decision createdAt"


def task_case(identifier: str) -> str:
    match = re.fullmatch(TASK_PATTERN, identifier)
    if match is None:
        raise ApiError(400, "TASK_ID_INVALID", "Invalid task ID.")
    return match[1]


def get_task(repo: CaseRepository, identifier: str) -> dict[str, Any]:
    case_id = task_case(identifier)
    result = repo.client.get_item(
        TableName=repo.table_name,
        Key=encode({"PK": "CASE#" + case_id, "SK": "TASK#" + identifier}),
        ConsistentRead=True,
    )
    if "Item" not in result:
        raise ApiError(404, "REVIEW_NOT_FOUND", "Review not found.")
    return decode(result["Item"])


def available(task: dict[str, Any], case: dict[str, Any]) -> bool:
    return (
        task["status"] == "PENDING"
        and task.get("reviewerId") is None
        and case["status"] == "REVIEW_PENDING"
        and case["submissionAttempt"] == task["attempt"]
    )


def detail(repo: CaseRepository, identifier: str, actor: str, groups: set[str]) -> dict[str, Any]:
    task = get_task(repo, identifier)
    case = repo.get(task["caseId"])
    if "admin" not in groups and task.get("reviewerId") != actor and not available(task, case):
        raise ApiError(404, "REVIEW_NOT_FOUND", "Review not found.")
    case_detail = repo.detail(case)
    checks = sorted(
        repo.related(task["caseId"], f"CHECK#{identifier}#"), key=lambda c: int(c["order"])
    )
    return {
        "task": public(task, FIELDS),
        "case": case_detail["case"],
        "documents": case_detail["documents"],
        "checks": [
            public(
                c,
                "checkId order documentType required instructions "
                "result comment updatedBy updatedAt",
            )
            for c in checks
        ],
    }


def queue(
    repo: CaseRepository, actor: str, scope: str, status: str | None, limit: int, cursor: str | None
) -> dict[str, Any]:
    if scope not in {"available", "mine"} or (status is not None and status not in STATES):
        raise ApiError(400, "QUERY_INVALID", "Invalid review scope or status.")
    if scope == "available":
        if status not in {None, "PENDING"}:
            raise ApiError(400, "QUERY_INVALID", "Available reviews must be PENDING.")
        status = "PENDING"
    owner = "UNASSIGNED" if scope == "available" else actor
    binding = json.dumps([actor, scope, status])
    prefix = "TASK#" + (status + "#DUE#" if status else "")
    pattern = (
        r"TASK#(?:PENDING|CLAIMED|IN_PROGRESS|COMPLETED)#DUE#[0-9T:.Z+-]{20,40}#" + TASK_PATTERN
    )
    position = read_position(cursor, binding, pattern)
    request: QueryInputTypeDef = {
        "TableName": repo.table_name,
        "IndexName": "GSI1",
        "Limit": limit,
        "KeyConditionExpression": "GSI1PK = :owner AND begins_with(GSI1SK, :prefix)",
        "ExpressionAttributeValues": encode({":owner": "REVIEWER#" + owner, ":prefix": prefix}),
        "ScanIndexForward": True,
    }
    if position:
        identifier = position.rsplit("#", 1)[1]
        request["ExclusiveStartKey"] = encode(
            {
                "PK": "CASE#" + task_case(identifier),
                "SK": "TASK#" + identifier,
                "GSI1PK": "REVIEWER#" + owner,
                "GSI1SK": position,
            }
        )
    result = repo.client.query(**request)
    items = []
    for raw in result.get("Items", []):
        candidate = decode(raw)
        try:
            task = get_task(repo, candidate["taskId"])
            case = repo.get(task["caseId"])
        except ApiError as exc:
            if exc.status == 404:
                continue
            raise
        if task.get("workflowFailedAt"):
            continue
        if status is not None and task["status"] != status:
            continue
        if scope == "available":
            permitted = available(task, case)
        else:
            permitted = task.get("reviewerId") == actor and (
                task["status"] == "COMPLETED"
                or (
                    case["status"] in {"REVIEW_PENDING", "IN_REVIEW"}
                    and case["submissionAttempt"] == task["attempt"]
                )
            )
        if permitted:
            items.append(public(task, FIELDS))
    last = decode(result.get("LastEvaluatedKey", {}))
    return {"items": items, "nextCursor": position_token(last["GSI1SK"], binding) if last else None}
