"""Reviewer/admin query HTTP boundary; callback data never enters a public DTO."""

import json
import os
import re
from typing import Any
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from case_api.api import number, principal, serialize
from common.cases.repository import ApiError, CaseRepository
from common.logging import observed
from common.reviews.query import detail, queue


def handle(event: dict[str, Any], repository: CaseRepository | None = None) -> dict[str, Any]:
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
        route = event.get("routeKey")
        if route not in {"GET /api/v1/reviews", "GET /api/v1/reviews/{taskId}"}:
            raise ApiError(404, "ROUTE_NOT_FOUND", "Route not found.")
        params = event.get("queryStringParameters") or {}
        allowed = (
            {"scope", "status", "limit", "cursor"} if route == "GET /api/v1/reviews" else set()
        )
        if (
            not isinstance(params, dict)
            or set(params) - allowed
            or any(not isinstance(v, str) for v in params.values())
            or event.get("body")
        ):
            raise ApiError(400, "QUERY_INVALID", "Invalid query.")
        repo = repository or CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"])
        result = (
            queue(
                repo,
                actor,
                params.get("scope", "available"),
                params.get("status"),
                number(params.get("limit"), 20),
                params.get("cursor"),
            )
            if route == "GET /api/v1/reviews"
            else detail(repo, (event.get("pathParameters") or {}).get("taskId", ""), actor, groups)
        )
        code = 200
    except ApiError as exc:
        code = exc.status
        result = {"error": {"code": exc.code, "message": str(exc), "correlationId": correlation}}
    except (ClientError, BotoCoreError, KeyError):
        code = 503
        result = {
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Service temporarily unavailable.",
                "correlationId": correlation,
            }
        }
    return {
        "statusCode": code,
        "headers": {
            "content-type": "application/json",
            "cache-control": "no-store",
            "x-correlation-id": correlation,
        },
        "body": json.dumps(result, default=serialize),
    }


@observed("review-query-handler")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    return handle(event)
