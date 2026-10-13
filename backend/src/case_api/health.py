"""Authenticated liveness endpoint; API Gateway verifies token signatures."""

import json
import re
from typing import Any
from uuid import uuid4

from common.logging import observed


@observed("case-query-handler")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Require trusted JWT context and never echo credentials or request content."""
    headers = event.get("headers") or {}
    supplied = headers.get("x-correlation-id", "")
    correlation_id = (
        supplied
        if isinstance(supplied, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", supplied)
        else f"corr_{uuid4().hex}"
    )
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    authorized = (
        claims.get("token_use") == "access"
        and isinstance(claims.get("sub"), str)
        and bool(claims["sub"])
    )
    body = (
        {"status": "ok", "service": "docflow"}
        if authorized
        else {
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Authentication required.",
                "correlationId": correlation_id,
            }
        }
    )
    return {
        "statusCode": 200 if authorized else 401,
        "headers": {
            "content-type": "application/json",
            "cache-control": "no-store",
            "x-correlation-id": correlation_id,
        },
        "body": json.dumps(body),
    }
