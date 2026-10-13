"""Case query Lambda entry point, retaining the existing health route."""

from typing import Any

from case_api.api import handle
from case_api.health import handler as health
from common.logging import observed


@observed("case-query-handler")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    if event.get("routeKey") == "GET /api/v1/health":
        return health(event, context)
    return handle(event, "query")
