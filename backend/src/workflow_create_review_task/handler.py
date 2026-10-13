"""Trusted callback creation; never log/return callback capability or SDK details."""

import os
from typing import Any

import boto3

from common.cases.repository import CaseRepository
from common.logging import observed
from common.reviews.creation import create_review


@observed("workflow-create-review-task")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    try:
        return create_review(
            CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"]), event
        )
    except Exception:
        raise RuntimeError("Review task creation failed") from None
