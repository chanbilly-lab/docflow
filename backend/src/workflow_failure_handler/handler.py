"""Trusted technical-failure entry point; never business rejection."""

import os
from typing import Any

import boto3

from common.cases.repository import CaseRepository
from common.cases.workflow_state import fail
from common.logging import observed


@observed("workflow-failure-handler")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    return fail(CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"]), event)
