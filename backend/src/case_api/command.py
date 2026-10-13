"""Case HTTP commands and trusted pending-start recovery."""

import os
from typing import Any

import boto3

from case_api.api import handle
from common.cases.repository import CaseRepository
from common.cases.workflow import configured, recover_stream
from common.logging import observed


@observed("case-command-handler")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    if "requestContext" not in event and (
        "Records" in event or event.get("operation") == "recoverWorkflowStart"
    ):
        repo = CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"])
        starter = configured(repo, os.environ["WORKFLOW_ARN"])
        if "Records" in event:
            return recover_stream(event, starter)
        # Direct IAM-authorized invocation only; never a public API route/body.
        return {"workflowExecutionId": starter.start(event["caseId"], int(event["attempt"]))}
    return handle(event, "command")
