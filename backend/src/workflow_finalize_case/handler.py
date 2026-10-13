"""Trusted worker with sanitized exceptions and no sensitive payload logging."""

import os
from typing import Any

import boto3

from common.cases.repository import CaseRepository
from common.logging import observed
from common.reviews.finalization import finalize


@observed("workflow-finalize-case")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    try:
        return finalize(CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"]), event)
    except Exception:
        raise RuntimeError("Case finalization failed") from None
