"""JWT HTTP command boundary; no callback fields or reviewer-supplied identities."""

import base64
import json
import os
import re
from typing import Any
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from case_api.api import principal, serialize
from common.cases.repository import ApiError, CaseRepository
from common.logging import observed
from common.reviews.commands import execute
from common.reviews.decisions import decide
from common.templates.repository import TemplateConflict, TemplateNotFound

ROUTES = {
    "POST /api/v1/reviews/{taskId}/claim": "claim",
    "POST /api/v1/reviews/{taskId}/decision": "decision",
    "POST /api/v1/reviews/{taskId}/start": "start",
    "PUT /api/v1/reviews/{taskId}/checks/{checkId}": "check",
}


def handle(
    event: dict[str, Any], repository: CaseRepository | None = None, service: Any = None
) -> dict[str, Any]:
    supplied = {k.lower(): v for k, v in (event.get("headers") or {}).items()}.get(
        "x-correlation-id", ""
    )
    correlation = (
        supplied
        if isinstance(supplied, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", supplied)
        else "corr_" + uuid4().hex
    )
    try:
        actor, groups = principal(event)
        if not groups & {"reviewer", "admin"}:
            raise ApiError(403, "FORBIDDEN", "Reviewer or admin required.")
        operation = ROUTES.get(event.get("routeKey", ""))
        if operation is None:
            raise ApiError(404, "ROUTE_NOT_FOUND", "Route not found.")
        if event.get("queryStringParameters"):
            raise ApiError(400, "QUERY_INVALID", "Query parameters are not supported.")
        try:
            raw = event.get("body")
            if raw is None or raw == "":
                raw = "{}"
            if not isinstance(raw, str) or len(raw) > 32768:
                raise ValueError
            if event.get("isBase64Encoded"):
                raw = base64.b64decode(raw, validate=True).decode("utf-8")
            if len(raw.encode("utf-8")) > 16384:
                raise ValueError
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError
        except (ValueError, TypeError, UnicodeError):
            raise ApiError(400, "REVIEW_INPUT_INVALID", "Supply a valid JSON object.") from None
        path = event.get("pathParameters") or {}
        identifier, check_id = path.get("taskId", ""), path.get("checkId", "")
        if not isinstance(identifier, str) or not isinstance(check_id, str):
            raise ApiError(400, "REVIEW_INPUT_INVALID", "Invalid route identifiers.")
        repo = repository or CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"])
        if operation == "decision":
            headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
            result = decide(
                repo,
                identifier,
                actor,
                groups,
                payload,
                headers.get("idempotency-key", ""),
                correlation,
                service or boto3.client("stepfunctions"),
            )
            status = 202
        else:
            result = execute(
                repo, identifier, actor, groups, operation, payload, correlation, check_id
            )
            status = 200
    except ApiError as exc:
        status = exc.status
        result = {"error": {"code": exc.code, "message": str(exc), "correlationId": correlation}}
    except (ClientError, BotoCoreError, KeyError, TemplateConflict, TemplateNotFound):
        status = 503
        result = {
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Service temporarily unavailable.",
                "correlationId": correlation,
            }
        }
    return {
        "statusCode": status,
        "headers": {
            "content-type": "application/json",
            "cache-control": "no-store",
            "x-correlation-id": correlation,
        },
        "body": json.dumps(result, default=serialize),
    }


@observed("review-command-handler")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    return handle(event)
