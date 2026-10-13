"""Persist one immutable human decision before attempting backend callback delivery."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from botocore.exceptions import BotoCoreError, ClientError

from common.cases.repository import ApiError, CaseRepository
from common.cases.submission import submission_key
from common.reviews.commands import change, condition, transact
from common.reviews.creation import audit, put
from common.reviews.query import get_task
from common.templates.repository import TemplateRepository

DECISIONS = {"APPROVE", "REJECT", "REQUEST_INFORMATION"}


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision")
    if not isinstance(decision, str) or decision not in DECISIONS:
        raise ApiError(400, "DECISION_INVALID", "Supply a supported decision.")
    allowed = {"decision"} if decision == "APPROVE" else {"decision", "reason"}
    if decision == "REQUEST_INFORMATION":
        allowed.add("requestedItems")
    if set(payload) - allowed:
        raise ApiError(400, "DECISION_INVALID", "Unsupported decision fields.")
    reason = payload.get("reason")
    if decision != "APPROVE" and (
        not isinstance(reason, str) or not reason.strip() or len(reason) > 2000
    ):
        raise ApiError(400, "DECISION_INVALID", "A reason of 1-2000 characters is required.")
    items = payload.get("requestedItems", [])
    if decision == "REQUEST_INFORMATION":
        if not isinstance(items, list) or not 1 <= len(items) <= 50:
            raise ApiError(400, "DECISION_INVALID", "Supply 1-50 requested items.")
        seen = set()
        for item in items:
            if (
                not isinstance(item, dict)
                or set(item) != {"documentType", "reasonCode", "message"}
                or not isinstance(item["documentType"], str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", item["documentType"])
                or item["documentType"] in seen
                or not isinstance(item["reasonCode"], str)
                or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", item["reasonCode"])
                or not isinstance(item["message"], str)
                or not item["message"].strip()
                or len(item["message"]) > 2000
            ):
                raise ApiError(400, "DECISION_INVALID", "Invalid requested item.")
            seen.add(item["documentType"])
    return {"decision": decision, "decisionReason": reason, "requestedItems": items}


def response(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "taskId": task["taskId"],
        "decision": task["decision"],
        "processingStatus": "WORKFLOW_RESUMING",
    }


def decide(
    repo: CaseRepository,
    identifier: str,
    actor: str,
    groups: set[str],
    payload: dict[str, Any],
    key: str,
    correlation: str,
    service: Any,
) -> dict[str, Any]:
    if not groups & {"reviewer", "admin"}:
        raise ApiError(403, "FORBIDDEN", "Reviewer or admin required.")
    key = submission_key(key)
    normalized = normalize(payload)
    digest = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()
    task = get_task(repo, identifier)
    if task.get("reviewerId") != actor:
        raise ApiError(403, "REVIEW_TASK_NOT_ASSIGNED", "Only the assigned reviewer may decide.")
    if task.get("decision") is not None:
        if task.get("decisionKey") != key or task.get("decisionHash") != digest:
            raise ApiError(409, "DECISION_ALREADY_RECORDED", "The first decision is immutable.")
        deliver(repo, identifier, service)
        return response(task)
    case = repo.get(task["caseId"])
    if (
        task["status"] != "IN_PROGRESS"
        or case["status"] != "IN_REVIEW"
        or case["submissionAttempt"] != task["attempt"]
    ):
        raise ApiError(409, "REVIEW_INVALID_STATE", "An active current review is required.")
    template = TemplateRepository(repo.client, repo.table_name).get_version(
        case["checklistTemplateId"], int(case["checklistTemplateVersion"])
    )
    checks = {c["checkId"]: c for c in repo.related(case["caseId"], f"CHECK#{identifier}#")}
    if set(checks) != {c.check_id for c in template.checks} or any(
        c.required and checks[c.check_id]["result"] not in {"PASS", "FAIL", "NOT_APPLICABLE"}
        for c in template.checks
    ):
        raise ApiError(422, "CHECKLIST_INCOMPLETE", "Complete all required checks.")
    if any(
        item["documentType"] not in template.required_documents
        for item in normalized["requestedItems"]
    ):
        raise ApiError(
            422, "REQUESTED_DOCUMENT_INVALID", "Use document types from the bound template."
        )
    now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    output = {**normalized, "taskId": identifier, "decisionId": "dec_" + uuid4().hex}
    updates = {
        **normalized,
        "decisionId": output["decisionId"],
        "decisionKey": key,
        "decisionHash": digest,
        "decisionActor": actor,
        "decisionCorrelationId": correlation,
        "callbackOutput": output,
        "callbackStatus": "PENDING",
        "status": "COMPLETED",
        "completedAt": now,
        "GSI1SK": f"TASK#COMPLETED#DUE#{task['dueAt']}#{identifier}",
    }
    record = {
        **audit(case, "REVIEW_DECIDED", now, identifier),
        "actorType": "USER",
        "actorId": actor,
        "correlationId": correlation,
        "previousState": "IN_PROGRESS",
        "newState": "COMPLETED",
        "decision": normalized["decision"],
    }
    writes = [
        {"ConditionCheck": condition(repo, case, ["status", "version", "submissionAttempt"])},
        {
            "Update": change(
                condition(
                    repo, task, ["status", "reviewerId", "attempt", "decision", "checkRevision"]
                ),
                updates,
            )
        },
        put(repo, record),
    ]
    try:
        transact(repo, writes, "decision")
    except ApiError as exc:
        if exc.status != 409:
            raise
        current = get_task(repo, identifier)
        if current.get("decisionKey") != key or current.get("decisionHash") != digest:
            raise
    deliver(repo, identifier, service)
    return response({**task, **updates})


def deliver(repo: CaseRepository, identifier: str, service: Any) -> None:
    task = get_task(repo, identifier)
    if task.get("workflowFailedAt") or task.get("callbackStatus") == "FAILED":
        raise ApiError(409, "WORKFLOW_FAILED", "The workflow requires operator recovery.")
    if task.get("callbackStatus") == "DELIVERED":
        return
    if not task.get("decision") or task.get("callbackStatus") != "PENDING":
        raise ApiError(409, "CALLBACK_NOT_PENDING", "No pending decision callback.")
    case = repo.get(task["caseId"])
    if case["status"] != "IN_REVIEW" or case["submissionAttempt"] != task["attempt"]:
        raise ApiError(409, "REVIEW_INVALID_STATE", "The decision attempt is no longer active.")
    try:
        service.send_task_success(
            taskToken=task["workflowTaskToken"],
            output=json.dumps(task["callbackOutput"], sort_keys=True),
        )
        now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        transact(
            repo,
            [
                {
                    "Update": change(
                        condition(
                            repo,
                            task,
                            [
                                "decisionId",
                                "callbackStatus",
                                "callbackGeneration",
                                "workflowFailedAt",
                            ],
                        ),
                        {"callbackStatus": "DELIVERED", "callbackDeliveredAt": now},
                    )
                },
                put(
                    repo,
                    {
                        **audit(case, "REVIEW_CALLBACK_DELIVERED", now, identifier),
                        "actorId": "review-command-handler",
                        "correlationId": task["decisionCorrelationId"],
                    },
                ),
            ],
            "callback",
        )
    except (ClientError, BotoCoreError, ApiError):
        # Closed/expired tokens are ambiguous, never proof of successful delivery.
        current = get_task(repo, identifier)
        if current.get("callbackStatus") == "DELIVERED" and not current.get("workflowFailedAt"):
            return
        raise ApiError(503, "CALLBACK_PENDING", "Decision saved; retry the same request.") from None
