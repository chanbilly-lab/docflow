"""Allowlisted JSON/EMF telemetry: no request bodies or exception strings."""

from __future__ import annotations

import json
import math
import re
import time
from collections.abc import Callable, Mapping
from contextvars import ContextVar
from datetime import UTC, datetime
from functools import wraps
from typing import Any, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])

REQUEST: ContextVar[str | None] = ContextVar("request", default=None)
COUNTERS = {
    "CaseCreated": "CasesCreated",
    "CaseSubmitted": "CasesSubmitted",
    "CaseResubmitted": "CasesSubmitted",
    "CaseApproved": "CasesApproved",
    "CaseRejected": "CasesRejected",
    "AdditionalInformationRequested": "CasesNeedsInformation",
    "DocumentValidated": "DocumentsProcessed",
    "DocumentValidationFailed": "DocumentsProcessed",
    "CaseReadyForReview": "ReviewTasksCreated",
    "CaseWorkflowFailed": "WorkflowFailures",
}
METRICS = set(COUNTERS.values()) | {
    "DocumentValidationFailures",
    "ReviewTasksPending",
    "ReviewDurationSeconds",
    "OutboxPublishFailures",
    "NotificationFailures",
    "DocumentProcessingFailures",
    "OutboxPendingAgeSeconds",
    "WorkflowStartPendingAgeSeconds",
    "MonitorSuccess",
}
IDS = {"correlationId", "caseId", "taskId", "eventId", "requestId"}


def safe(value: Any) -> str | None:
    return (
        value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value) else None
    )


def emit(
    service: str,
    message: str,
    *,
    level: str = "INFO",
    fields: dict[str, Any] | None = None,
    metrics: Mapping[str, float] | None = None,
) -> None:
    row: dict[str, Any] = {
        "level": level,
        "service": service,
        "message": message,
        "timestamp": datetime.now(UTC).isoformat(),
        "requestId": REQUEST.get(),
    }
    row.update(
        {key: safe(value) for key, value in (fields or {}).items() if key in IDS - {"requestId"}}
    )
    values = {
        key: value
        for key, value in (metrics or {}).items()
        if key in METRICS and math.isfinite(value) and value >= 0
    }
    if values:
        row.update(values)
        row["_aws"] = {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [
                {
                    "Namespace": "DocFlow",
                    "Dimensions": [["service"]],
                    "Metrics": [
                        {"Name": key, "Unit": "Seconds" if key.endswith("Seconds") else "Count"}
                        for key in values
                    ],
                }
            ],
        }
    # Direct JSON stdout preserves the root-level EMF envelope in Lambda text logs.
    try:
        print(json.dumps(row, allow_nan=False))
    except OSError:
        pass  # Telemetry transport must never roll back accepted business operations.


def observed(service: str) -> Callable[[F], F]:
    def decorate(function: F) -> F:
        @wraps(function)
        def wrapped(event: dict[str, Any], context: object, *args: Any, **kwargs: Any) -> Any:
            token = REQUEST.set(safe(getattr(context, "aws_request_id", None)))
            submission = event.get("submission")
            source = submission if isinstance(submission, dict) else event
            fields = {key: source[key] for key in IDS - {"requestId"} if key in source}
            params = event.get("pathParameters")
            if isinstance(params, dict):
                fields.update({key: params[key] for key in ("caseId", "taskId") if key in params})
            headers = event.get("headers")
            if isinstance(headers, dict):
                for key, value in headers.items():
                    if key.lower() == "x-correlation-id":
                        fields["correlationId"] = value
            try:
                result = function(event, context, *args, **kwargs)
                if isinstance(result, dict):
                    correlation = result.get("headers", {}).get("x-correlation-id")
                    if correlation:
                        fields["correlationId"] = correlation
                    failed = (
                        bool(result.get("batchItemFailures"))
                        or result.get("statusCode", 200) >= 500
                    )
                else:
                    failed = False
                emit(
                    service,
                    "InvocationRetry" if failed else "InvocationComplete",
                    level="ERROR" if failed else "INFO",
                    fields=fields,
                )
                return result
            except Exception:
                emit(service, "InvocationFailed", level="ERROR", fields=fields)
                raise
            finally:
                REQUEST.reset(token)

        return cast(F, wrapped)

    return decorate
