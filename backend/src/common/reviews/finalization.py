"""Trusted workflow finalization reads and verifies the immutable persisted decision."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from common.cases.repository import CaseRepository
from common.cases.workflow_state import matching
from common.logging import emit
from common.reviews.commands import change, condition, transact
from common.reviews.creation import audit, put, task_id
from common.reviews.query import get_task

OUTCOMES = {
    "APPROVE": ("APPROVED", "CaseApproved"),
    "REJECT": ("REJECTED", "CaseRejected"),
    "REQUEST_INFORMATION": ("NEEDS_INFORMATION", "AdditionalInformationRequested"),
}


def finalize(repo: CaseRepository, event: dict[str, Any]) -> dict[str, Any]:
    case = matching(repo, event)
    if case is None:
        raise ValueError("Finalization identity mismatch")
    identifier = task_id(case["caseId"], int(case["submissionAttempt"]))
    task = get_task(repo, identifier)
    if (
        task.get("callbackOutput") != event.get("decision")
        or not task.get("decision")
        or task["workflowExecutionArn"] != event["executionArn"]
        or task["status"] != "COMPLETED"
        or task.get("workflowFailedAt")
        or task.get("callbackStatus") not in {"PENDING", "DELIVERED"}
    ):
        raise ValueError("Finalization decision mismatch")
    state, kind = OUTCOMES[task["decision"]]
    if task.get("finalizedAt"):
        if case["status"] != state or case.get("reviewDecisionId") != task["decisionId"]:
            raise ValueError("Finalization state mismatch")
        return {"status": state}
    if case["status"] != "IN_REVIEW":
        raise ValueError("Finalization requires active Case")
    now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    record = {
        **audit(case, "CASE_" + state, now, identifier),
        "actorId": "workflow-finalize-case",
        "resourceType": "CASE",
        "resourceId": case["caseId"],
        "previousState": "IN_REVIEW",
        "newState": state,
        "correlationId": task["decisionCorrelationId"],
    }
    event_id = "evt_" + task["decisionId"]
    detail = {
        "eventId": event_id,
        "eventVersion": "1.0",
        "occurredAt": now,
        "caseId": case["caseId"],
        "correlationId": task["decisionCorrelationId"],
        "actor": {"type": "SYSTEM", "id": "workflow-finalize-case"},
        "data": {
            "taskId": identifier,
            "attempt": task["attempt"],
            "decision": task["decision"],
            "reviewerId": task["decisionActor"],
            "decisionReason": task["decisionReason"],
            "requestedItems": task["requestedItems"],
        },
    }
    fact = {
        "PK": case["PK"],
        "SK": "OUTBOX#" + event_id,
        "entityType": "OUTBOX",
        "eventId": event_id,
        "eventVersion": "1.0",
        "eventType": kind,
        "source": "docflow.case",
        "caseId": case["caseId"],
        "correlationId": detail["correlationId"],
        "detail": detail,
        "status": "PENDING",
        "createdAt": now,
    }
    transact(
        repo,
        [
            {
                "Update": change(
                    condition(
                        repo, case, ["status", "version", "submissionAttempt", "workflowInput"]
                    ),
                    {
                        "status": state,
                        "updatedAt": now,
                        "GSI2PK": "CASE_STATUS#" + state,
                        "GSI2SK": f"UPDATED#{now}#{case['caseId']}",
                        "reviewDecisionId": task["decisionId"],
                        "decision": task["decision"],
                        "decisionReason": task["decisionReason"],
                        "requestedInformation": task["requestedItems"],
                    },
                    {"version": 1},
                )
            },
            {
                "Update": change(
                    condition(
                        repo,
                        task,
                        ["decisionId", "callbackStatus", "finalizedAt", "workflowFailedAt"],
                    ),
                    {
                        "finalizedAt": now,
                        "callbackStatus": "DELIVERED",
                        "callbackDeliveredAt": task.get("callbackDeliveredAt", now),
                    },
                )
            },
            put(repo, record),
            put(repo, fact),
        ],
        "finalization",
    )
    emit(
        "workflow-finalize-case",
        "ReviewCompleted",
        fields=detail,
        metrics={
            "ReviewDurationSeconds": max(
                0.0,
                (
                    datetime.fromisoformat(task["completedAt"])
                    - datetime.fromisoformat(task["createdAt"])
                ).total_seconds(),
            )
        },
    )
    return {"status": state}
