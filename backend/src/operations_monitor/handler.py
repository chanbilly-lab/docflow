"""Bounded read-only operational snapshot; never repairs business state."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import boto3

from common.logging import emit, observed
from common.templates.repository import decode


def age(value: str, now: datetime) -> float:
    return max(0.0, (now - datetime.fromisoformat(value)).total_seconds())


def snapshot(
    client: Any, table: str, *, now: datetime | None = None, page_limit: int = 100
) -> dict[str, float]:
    now = now or datetime.now(UTC)
    values = {
        "ReviewTasksPending": 0.0,
        "OutboxPendingAgeSeconds": 0.0,
        "WorkflowStartPendingAgeSeconds": 0.0,
        "MonitorSuccess": 1.0,
    }
    request: dict[str, Any] = {
        "TableName": table,
        "ConsistentRead": True,
        "Limit": 100,
        "Select": "SPECIFIC_ATTRIBUTES",
        "ProjectionExpression": (
            "entityType, #s, createdAt, workflowStartStatus, workflowSubmittedAt, updatedAt"
        ),
        "ExpressionAttributeNames": {"#s": "status"},
    }
    for _ in range(page_limit):
        page = client.scan(**request)
        for raw in page.get("Items", []):
            row = decode(raw)
            kind = row.get("entityType")
            if kind == "REVIEW_TASK" and row.get("status") in {"PENDING", "CLAIMED", "IN_PROGRESS"}:
                values["ReviewTasksPending"] += 1
            if kind == "OUTBOX" and row.get("status") == "PENDING":
                values["OutboxPendingAgeSeconds"] = max(
                    values["OutboxPendingAgeSeconds"], age(row["createdAt"], now)
                )
            if kind == "CASE" and row.get("workflowStartStatus") == "PENDING":
                values["WorkflowStartPendingAgeSeconds"] = max(
                    values["WorkflowStartPendingAgeSeconds"],
                    age(row.get("workflowSubmittedAt", row["updatedAt"]), now),
                )
        if not page.get("LastEvaluatedKey"):
            return values
        request["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    raise RuntimeError("Operational snapshot page limit exceeded")


@observed("operations-monitor")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    values = snapshot(boto3.client("dynamodb"), os.environ["TABLE_NAME"])
    emit("operations-monitor", "SnapshotComplete", metrics=values)
    return {"status": "COMPLETE"}
