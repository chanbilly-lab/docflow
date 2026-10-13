"""HTTP API v2 boundary with trusted authorizer claims and explicit DTOs."""

from __future__ import annotations

import base64
import json
import os
import re
from decimal import Decimal
from typing import Any, Literal
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from common.cases.repository import STATES, ApiError, CaseRepository
from common.cases.submission import submit
from common.cases.workflow import WorkflowStarter, configured
from common.templates.repository import CASE_TEMPLATES, TemplateConflict, TemplateNotFound


def principal(event: dict[str, Any]) -> tuple[str, set[str]]:
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    actor = claims.get("sub")
    if (
        claims.get("token_use") != "access"
        or not isinstance(actor, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", actor)
    ):
        raise ApiError(401, "UNAUTHORIZED", "Authentication required.")
    raw = claims.get("cognito:groups", [])
    if isinstance(raw, str):
        raw = re.split(r"[\s,]+", raw.strip("[]").replace('"', "").replace("'", ""))
    groups = (
        set(raw) & {"requester", "reviewer", "admin"}
        if isinstance(raw, list) and all(isinstance(g, str) for g in raw)
        else set()
    )
    if not groups:
        raise ApiError(403, "FORBIDDEN", "A permitted role is required.")
    return actor, groups


def number(value: str | None, default: int) -> int:
    if value is None:
        return default
    if not re.fullmatch(r"[0-9]{1,3}", value) or not 1 <= int(value) <= 100:
        raise ApiError(400, "QUERY_INVALID", "Limit must be between 1 and 100.")
    return int(value)


def serialize(value: object) -> int:
    if isinstance(value, Decimal) and value == value.to_integral_value():
        return int(value)
    raise TypeError("Unsupported response value.")


def handle(
    event: dict[str, Any],
    mode: Literal["command", "query"],
    repository: CaseRepository | None = None,
    starter: WorkflowStarter | None = None,
) -> dict[str, Any]:
    headers = {key.lower(): value for key, value in (event.get("headers") or {}).items()}
    supplied = headers.get("x-correlation-id", "")
    correlation = (
        supplied
        if isinstance(supplied, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", supplied)
        else f"corr_{uuid4().hex}"
    )
    try:
        actor, groups = principal(event)
        route = event.get("routeKey")
        allowed = (
            {
                "POST /api/v1/cases",
                "POST /api/v1/cases/{caseId}/submit",
                "POST /api/v1/cases/{caseId}/resubmit",
            }
            if mode == "command"
            else {
                "GET /api/v1/cases",
                "GET /api/v1/cases/{caseId}",
                "GET /api/v1/cases/{caseId}/activity",
            }
        )
        if route not in allowed:
            raise ApiError(404, "ROUTE_NOT_FOUND", "Route not found.")
        params = event.get("queryStringParameters") or {}
        if not isinstance(params, dict) or any(not isinstance(v, str) for v in params.values()):
            raise ApiError(400, "QUERY_INVALID", "Invalid query parameters.")
        permitted = (
            {"limit", "cursor", "status", "owner"}
            if route == "GET /api/v1/cases"
            else {"limit", "cursor"}
            if str(route).endswith("/activity")
            else set()
        )
        if set(params) - permitted:
            raise ApiError(400, "QUERY_INVALID", "Unsupported query parameter.")
        if route == "POST /api/v1/cases":
            if not groups & {"requester", "admin"}:
                raise ApiError(403, "FORBIDDEN", "Case creation is not permitted.")
            try:
                body = event.get("body") or ""
                if len(body) > 4096:
                    raise ValueError
                if event.get("isBase64Encoded"):
                    body = base64.b64decode(body, validate=True).decode()
                payload = json.loads(body)
                if (
                    not isinstance(payload, dict)
                    or set(payload) != {"caseType"}
                    or payload["caseType"] not in CASE_TEMPLATES
                ):
                    raise ValueError
            except (ValueError, TypeError, UnicodeError) as exc:
                raise ApiError(
                    400, "CASE_TYPE_INVALID", "Supply a supported caseType only."
                ) from exc
        repo = repository or CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"])
        if route == "POST /api/v1/cases":
            result, status_code = repo.create(payload["caseType"], actor, correlation), 201
        elif route in {
            "POST /api/v1/cases/{caseId}/submit",
            "POST /api/v1/cases/{caseId}/resubmit",
        }:
            try:
                body = event.get("body")
                if not isinstance(body, str) or len(body) > 4096:
                    raise ValueError
                if event.get("isBase64Encoded"):
                    body = base64.b64decode(body, validate=True).decode()
                if json.loads(body) != {}:
                    raise ValueError
            except (ValueError, TypeError, UnicodeError) as exc:
                raise ApiError(
                    400, "SUBMISSION_INPUT_INVALID", "Supply an empty JSON object."
                ) from exc
            result = submit(
                repo,
                (event.get("pathParameters") or {}).get("caseId", ""),
                actor,
                groups,
                str(route).rsplit("/", 1)[1],
                headers.get("idempotency-key", ""),
                correlation,
            )
            workflow = starter
            if workflow is None and repository is None:
                workflow = configured(repo, os.environ["WORKFLOW_ARN"])
            if workflow is not None:
                result = {
                    **result,
                    "workflowExecutionId": workflow.start(result["caseId"], int(result["attempt"])),
                }
            status_code = 202
        elif route == "GET /api/v1/cases":
            if not groups & {"requester", "admin"}:
                raise ApiError(403, "FORBIDDEN", "Case listing is not permitted.")
            owner, state = params.get("owner", "mine"), params.get("status")
            if owner not in {"mine", "all"} or (state is not None and state not in STATES):
                raise ApiError(400, "QUERY_INVALID", "Invalid owner or status.")
            if owner == "all" and "admin" not in groups:
                raise ApiError(403, "FORBIDDEN", "Admin role required.")
            if owner == "all" and state is None:
                raise ApiError(400, "QUERY_INVALID", "Status is required for owner=all.")
            result = repo.list_cases(
                actor, owner, state, number(params.get("limit"), 20), params.get("cursor")
            )
            status_code = 200
        else:
            item = repo.get((event.get("pathParameters") or {}).get("caseId", ""))
            repo.authorize(item, actor, groups)
            result = (
                repo.activity(
                    item["caseId"], actor, number(params.get("limit"), 50), params.get("cursor")
                )
                if str(route).endswith("/activity")
                else repo.detail(item)
            )
            status_code = 200
    except TemplateNotFound:
        result, status_code = (
            {
                "error": {
                    "code": "TEMPLATE_UNAVAILABLE",
                    "message": "No active template is available.",
                    "correlationId": correlation,
                }
            },
            503,
        )
    except ApiError as exc:
        result, status_code = (
            {"error": {"code": exc.code, "message": str(exc), "correlationId": correlation}},
            exc.status,
        )
    except (ClientError, BotoCoreError, TemplateConflict, KeyError):
        result, status_code = (
            {
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Service temporarily unavailable.",
                    "correlationId": correlation,
                }
            },
            503,
        )
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
            "cache-control": "no-store",
            "x-correlation-id": correlation,
        },
        "body": json.dumps(result, default=serialize),
    }
