"""Trusted Step Functions validation entry point."""

import os
from typing import Any

import boto3

from common.cases.repository import CaseRepository
from common.cases.workflow_state import validate
from common.logging import observed


@observed("workflow-validate-case")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    return validate(CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"]), event)
