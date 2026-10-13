"""At-least-once outbox publication; committed domain IDs survive every retry."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import ClientError

from common.cases.repository import CaseRepository
from common.logging import COUNTERS, emit, observed
from common.templates.repository import decode, encode

SOURCES = {
    "CaseCreated": "docflow.case",
    "CaseSubmitted": "docflow.case",
    "CaseResubmitted": "docflow.case",
    "CaseWorkflowFailed": "docflow.case",
    "CaseReadyForReview": "docflow.case",
    "ReviewStarted": "docflow.review",
    "CaseApproved": "docflow.case",
    "CaseRejected": "docflow.case",
    "AdditionalInformationRequested": "docflow.case",
    "DocumentValidated": "docflow.document",
    "DocumentValidationFailed": "docflow.document",
}


def json_number(value: Any) -> int:
    # Current contracts contain only integral numbers; never silently round Decimal.
    if isinstance(value, Decimal) and value.is_finite() and value == value.to_integral_value():
        return int(value)
    raise ValueError("Unsupported JSON value")


def serialize(row: dict[str, Any]) -> str:
    if SOURCES.get(row["eventType"]) != row["source"]:
        raise ValueError("Unsupported event contract")
    detail = row["detail"]
    if not isinstance(detail, dict) or set(detail) != {
        "eventId",
        "eventVersion",
        "occurredAt",
        "correlationId",
        "caseId",
        "actor",
        "data",
    }:
        raise ValueError("Invalid domain envelope")
    for field in ("eventId", "eventVersion", "caseId", "correlationId"):
        if detail[field] != row[field]:
            raise ValueError("Envelope identity mismatch")
    if (
        row["eventVersion"] != "1.0"
        or row["PK"] != "CASE#" + row["caseId"]
        or row["SK"] != "OUTBOX#" + row["eventId"]
    ):
        raise ValueError("Invalid outbox identity")
    for field in ("eventId", "caseId", "correlationId"):
        if not isinstance(row[field], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", row[field]):
            raise ValueError("Invalid correlation identity")
    encoded = json.dumps(detail, default=json_number, allow_nan=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > 250_000:
        raise ValueError("Oversized domain event")
    return encoded


class Publisher:
    def __init__(self, repo: CaseRepository, events: Any, bus_arn: str):
        if not re.fullmatch(
            r"arn:aws[a-z-]*:events:[a-z0-9-]+:[0-9]{12}:event-bus/[A-Za-z0-9_.-]+", bus_arn
        ) or bus_arn.endswith("/default"):
            raise ValueError("Explicit custom domain bus ARN required")
        self.repo, self.events, self.bus_arn = repo, events, bus_arn

    def read(self, key: dict[str, str]) -> dict[str, Any]:
        result = self.repo.client.get_item(
            TableName=self.repo.table_name, Key=encode(key), ConsistentRead=True
        )
        if "Item" not in result:
            raise ValueError("Outbox record missing")
        return decode(result["Item"])

    def publish(self, image: dict[str, Any]) -> None:
        key = {"PK": image["PK"], "SK": image["SK"]}
        if not key["PK"].startswith("CASE#") or not key["SK"].startswith("OUTBOX#"):
            raise ValueError("Unexpected outbox key")
        row = self.read(key)
        if row.get("entityType") != "OUTBOX":
            raise ValueError("Unexpected persisted entity")
        if row.get("status") == "DISPATCHED":
            return
        if row.get("status") != "PENDING":
            raise ValueError("Unexpected outbox state")
        # Stream images are hints; never publish stale or altered committed facts.
        immutable = (
            "eventId",
            "eventType",
            "eventVersion",
            "source",
            "caseId",
            "correlationId",
            "detail",
        )
        if any(row.get(field) != image.get(field) for field in immutable):
            raise ValueError("Outbox fact changed")
        detail = serialize(row)
        # PutEvents can return success for a nonexistent bus. Fail closed first.
        if self.events.describe_event_bus(Name=self.bus_arn).get("Arn") != self.bus_arn:
            raise ValueError("Domain bus mismatch")
        result = self.events.put_events(
            Entries=[
                {
                    "EventBusName": self.bus_arn,
                    "Source": row["source"],
                    "DetailType": row["eventType"],
                    "Detail": detail,
                }
            ]
        )
        entries = result.get("Entries", [])
        if (
            result.get("FailedEntryCount") != 0
            or len(entries) != 1
            or entries[0].get("ErrorCode")
            or not entries[0].get("EventId")
        ):
            raise RuntimeError("EventBridge entry not accepted")
        now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        try:
            self.repo.client.update_item(
                TableName=self.repo.table_name,
                Key=encode(key),
                UpdateExpression="SET #state = :sent, dispatchedAt = :now",
                ConditionExpression=(
                    "#state = :pending AND entityType = :entity AND eventId = :id "
                    "AND #detail = :detail AND #source = :source AND eventType = :kind"
                ),
                ExpressionAttributeNames={
                    "#state": "status",
                    "#detail": "detail",
                    "#source": "source",
                },
                ExpressionAttributeValues=encode(
                    {
                        ":sent": "DISPATCHED",
                        ":now": now,
                        ":pending": "PENDING",
                        ":entity": "OUTBOX",
                        ":id": row["eventId"],
                        ":detail": row["detail"],
                        ":source": row["source"],
                        ":kind": row["eventType"],
                    }
                ),
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
            current = self.read(key)
            if current.get("status") != "DISPATCHED" or any(
                current.get(field) != row.get(field) for field in immutable
            ):
                raise
        metrics = {COUNTERS[row["eventType"]]: 1} if row["eventType"] in COUNTERS else {}
        if row["eventType"] == "DocumentValidationFailed":
            metrics["DocumentValidationFailures"] = 1
        emit("outbox-publisher", "OUTBOX_DISPATCHED", fields=row, metrics=metrics)


def handle(event: dict[str, Any], publisher: Publisher) -> dict[str, Any]:
    for record in event["Records"]:
        # A malformed stream sequence must fail the invocation, not acknowledge data.
        sequence = record["dynamodb"]["SequenceNumber"]
        if not isinstance(sequence, str) or not sequence.isdigit():
            raise ValueError("Invalid stream sequence")
        try:
            if record.get("eventSource") != "aws:dynamodb":
                raise ValueError("Unexpected stream source")
            if record.get("eventName") not in {"INSERT", "MODIFY"}:
                continue
            image = decode(record["dynamodb"]["NewImage"])
            if image.get("entityType") != "OUTBOX" or image.get("status") != "PENDING":
                continue
            publisher.publish(image)
        except Exception:
            # Stop at the first failed sequence; preserve per-shard replay ordering.
            emit(
                "outbox-publisher",
                "OUTBOX_RETRY",
                level="ERROR",
                metrics={"OutboxPublishFailures": 1},
            )
            return {"batchItemFailures": [{"itemIdentifier": sequence}]}
    return {"batchItemFailures": []}


@observed("outbox-publisher")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    publisher = Publisher(
        CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"]),
        boto3.client("events"),
        os.environ["DOMAIN_BUS_ARN"],
    )
    if event.get("operation") == "recoverOutbox" and "Records" not in event:
        case, identifier = event.get("caseId"), event.get("eventId")
        if not isinstance(case, str) or not re.fullmatch(r"c_[A-Za-z0-9_-]{1,100}", case):
            raise ValueError("Invalid recovery identity")
        if not isinstance(identifier, str) or not re.fullmatch(
            r"evt_[A-Za-z0-9_-]{1,124}", identifier
        ):
            raise ValueError("Invalid recovery identity")
        try:
            publisher.publish(publisher.read({"PK": "CASE#" + case, "SK": "OUTBOX#" + identifier}))
        except Exception:
            emit(
                "outbox-publisher",
                "OUTBOX_RETRY",
                level="ERROR",
                metrics={"OutboxPublishFailures": 1},
            )
            raise RuntimeError("Outbox recovery failed") from None
        return {"status": "DISPATCHED"}
    return handle(event, publisher)
