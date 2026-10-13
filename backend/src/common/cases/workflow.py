"""Start the committed Standard execution; retry without creating another attempt."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from common.cases.repository import ApiError, CaseRepository
from common.templates.repository import decode, encode


def canonical(value: Any) -> str:
    from decimal import Decimal

    def number(item: Any) -> int:
        if isinstance(item, Decimal) and item == item.to_integral_value():
            return int(item)
        raise TypeError("Invalid workflow input")

    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=number)


class WorkflowStarter:
    def __init__(self, repo: CaseRepository, client: Any, machine: str):
        self.repo, self.client, self.machine = repo, client, machine
        parts = machine.split(":")
        if len(parts) != 7 or parts[2] != "states" or parts[5] != "stateMachine":
            raise ValueError("Require an unqualified state machine ARN")

    def start(self, case_id: str, attempt: int) -> str | None:
        case = self.repo.get(case_id)
        if case["submissionAttempt"] != attempt:
            return None
        if case.get("workflowStartStatus") == "STARTED":
            return str(case["workflowExecutionId"])
        if case.get("workflowStartStatus") != "PENDING":
            raise ApiError(503, "WORKFLOW_START_UNAVAILABLE", "Workflow start unavailable.")
        submitted = datetime.fromisoformat(case.get("workflowSubmittedAt", case["updatedAt"]))
        if datetime.now(UTC) - submitted > timedelta(days=85):
            raise ApiError(503, "WORKFLOW_RECOVERY_REQUIRED", "Operator recovery required.")
        name, payload = case["workflowExecutionName"], canonical(case["workflowInput"])
        expected = self.machine.replace(":stateMachine:", ":execution:") + ":" + name
        try:
            result = self.client.start_execution(
                stateMachineArn=self.machine, name=name, input=payload
            )
            arn = result["executionArn"]
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ExecutionAlreadyExists":
                raise
            result = self.client.describe_execution(executionArn=expected)
            if (
                result["stateMachineArn"] != self.machine
                or result["name"] != name
                or result["input"] != payload
            ):
                raise ApiError(
                    503, "WORKFLOW_IDENTITY_CONFLICT", "Workflow identity mismatch."
                ) from exc
            arn = result["executionArn"]
        if arn != expected:
            raise ApiError(503, "WORKFLOW_IDENTITY_CONFLICT", "Workflow identity mismatch.")
        try:
            self.repo.client.update_item(
                TableName=self.repo.table_name,
                Key=encode({"PK": case["PK"], "SK": "CASE"}),
                UpdateExpression="SET workflowExecutionId = :arn, workflowStartStatus = :started",
                ConditionExpression=(
                    "submissionAttempt = :attempt AND workflowExecutionName = :name "
                    "AND workflowInput = :input AND workflowStartStatus = :pending"
                ),
                ExpressionAttributeValues=encode(
                    {
                        ":arn": arn,
                        ":started": "STARTED",
                        ":attempt": attempt,
                        ":name": name,
                        ":input": case["workflowInput"],
                        ":pending": "PENDING",
                    }
                ),
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
            current = self.repo.get(case_id)
            if current["submissionAttempt"] != attempt:
                return None
            if (
                current.get("workflowStartStatus") != "STARTED"
                or current.get("workflowExecutionId") != arn
            ):
                raise
        return str(arn)


def configured(repo: CaseRepository, machine: str) -> WorkflowStarter:
    return WorkflowStarter(
        repo,
        boto3.client(
            "stepfunctions",
            config=Config(
                connect_timeout=2,
                read_timeout=3,
                retries={"max_attempts": 1},
            ),
        ),
        machine,
    )


def recover_stream(event: dict[str, Any], starter: WorkflowStarter) -> dict[str, Any]:
    for record in event["Records"]:
        sequence = record["dynamodb"]["SequenceNumber"]
        try:
            if record.get("eventSource") != "aws:dynamodb":
                raise ValueError("Unexpected source")
            row = decode(record["dynamodb"].get("NewImage", {}))
            if row.get("entityType") == "CASE" and row.get("workflowStartStatus") == "PENDING":
                starter.start(row["caseId"], int(row["submissionAttempt"]))
        except Exception:
            return {"batchItemFailures": [{"itemIdentifier": sequence}]}
    return {"batchItemFailures": []}
