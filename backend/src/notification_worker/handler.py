"""Durable event-level email delivery, isolated from Case business transactions."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from common.cases.repository import CaseRepository
from common.logging import emit, observed
from common.templates.repository import decode, encode
from outbox_publisher.handler import serialize

TITLES = {
    "CaseReadyForReview": "Ready for review",
    "AdditionalInformationRequested": "Information requested",
    "CaseApproved": "Approved",
    "CaseRejected": "Rejected",
}
PARTITION = "IDEMPOTENCY#notification-worker"


def email(value: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) > 254
        or not re.fullmatch(
            r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}", value
        )
    ):
        raise ValueError("Invalid email configuration")
    return value


class Worker:
    def __init__(
        self, repo: CaseRepository, ses: Any, cognito: Any, pool: str, sender: str, reviewer: str
    ):
        self.repo, self.ses, self.cognito, self.pool = repo, ses, cognito, pool
        self.sender, self.reviewer = email(sender), email(reviewer)

    def read(self, key: dict[str, Any]) -> dict[str, Any]:
        raw = self.repo.client.get_item(
            TableName=self.repo.table_name, Key=encode(key), ConsistentRead=True
        )
        return decode(raw["Item"]) if "Item" in raw else {}

    def recipient(self, case: str, kind: str) -> str:
        if kind == "CaseReadyForReview":
            return self.reviewer
        subject = self.repo.get(case)["requesterId"]
        if not isinstance(subject, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", subject):
            raise ValueError("Invalid requester identity")
        users = []
        request: dict[str, Any] = {
            "UserPoolId": self.pool,
            "Filter": f'sub = "{subject}"',
            "Limit": 60,
        }
        while True:
            page = self.cognito.list_users(**request)
            users.extend(page["Users"])
            if len(users) > 1:
                raise ValueError("Ambiguous requester")
            if not page.get("PaginationToken"):
                break
            request["PaginationToken"] = page["PaginationToken"]
        if len(users) != 1 or not users[0].get("Enabled"):
            raise ValueError("Requester unavailable")
        attrs = {a["Name"]: a["Value"] for a in users[0]["Attributes"]}
        if attrs.get("sub") != subject or attrs.get("email_verified") != "true":
            raise ValueError("Verified requester email required")
        return email(attrs["email"])

    def process(self, body: str) -> str:
        if not isinstance(body, str) or len(body.encode()) > 262144:
            raise ValueError("Invalid notification envelope")
        event = json.loads(body)
        kind, detail = event["detail-type"], event["detail"]
        if event["source"] != "docflow.case" or kind not in TITLES:
            raise ValueError("Unsupported notification")
        identifier, case = detail["eventId"], detail["caseId"]
        if not re.fullmatch(r"evt_[A-Za-z0-9_-]{1,124}", identifier) or not re.fullmatch(
            r"c_[A-Za-z0-9_-]{1,100}", case
        ):
            raise ValueError("Invalid event identity")
        fact = self.read({"PK": "CASE#" + case, "SK": "OUTBOX#" + identifier})
        canonical = serialize(fact)
        if fact["eventType"] != kind or json.loads(canonical) != detail:
            raise ValueError("Notification differs from committed fact")
        digest = hashlib.sha256((kind + json.dumps(detail, sort_keys=True)).encode()).hexdigest()
        key = {"PK": PARTITION, "SK": "EVENT#" + identifier}
        prior = self.read(key)
        if prior and prior.get("payloadHash") != digest:
            raise ValueError("Notification identity conflict")
        if prior.get("status") == "COMPLETED":
            return "DUPLICATE"
        now, owner = int(time.time()), uuid4().hex
        self.repo.client.put_item(
            TableName=self.repo.table_name,
            Item=encode(
                {
                    **key,
                    "entityType": "IDEMPOTENCY",
                    "status": "IN_PROGRESS",
                    "owner": owner,
                    "leaseUntil": now + 120,
                    "payloadHash": digest,
                    "eventId": identifier,
                    "caseId": case,
                    "eventType": kind,
                }
            ),
            ConditionExpression=(
                "attribute_not_exists(PK) OR "
                "(#s = :pending AND leaseUntil <= :now AND payloadHash = :hash)"
            ),
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues=encode(
                {":pending": "IN_PROGRESS", ":now": now, ":hash": digest}
            ),
        )
        try:
            destination = self.recipient(case, kind)
            sent = self.ses.send_email(
                Source=self.sender,
                Destination={"ToAddresses": [destination]},
                Message={
                    "Subject": {"Data": "DocFlow: " + TITLES[kind], "Charset": "UTF-8"},
                    "Body": {
                        "Text": {
                            "Charset": "UTF-8",
                            "Data": f"Case {case}\nReview attempt {detail['data']['attempt']}\n"
                            f"{TITLES[kind]} at {detail['occurredAt']}.\n"
                            "Sign in to DocFlow to view the case. "
                            "This message describes a recorded event.",
                        }
                    },
                },
            )
            if not sent.get("MessageId"):
                raise ValueError("SES acceptance missing")
            self.repo.client.update_item(
                TableName=self.repo.table_name,
                Key=encode(key),
                UpdateExpression=(
                    "SET #s = :done, processedAt = :now, messageId = :message REMOVE leaseUntil"
                ),
                ConditionExpression="#s = :pending AND #owner = :owner AND leaseUntil > :now",
                ExpressionAttributeNames={"#s": "status", "#owner": "owner"},
                ExpressionAttributeValues=encode(
                    {
                        ":done": "COMPLETED",
                        ":pending": "IN_PROGRESS",
                        ":owner": owner,
                        ":now": int(time.time()),
                        ":message": sent["MessageId"],
                    }
                ),
            )
        except Exception:
            # Retry only this delivery; a crash after SES acceptance can duplicate email.
            try:
                self.repo.client.update_item(
                    TableName=self.repo.table_name,
                    Key=encode(key),
                    UpdateExpression="SET leaseUntil = :zero",
                    ConditionExpression="#s = :pending AND #owner = :owner",
                    ExpressionAttributeNames={"#s": "status", "#owner": "owner"},
                    ExpressionAttributeValues=encode(
                        {":zero": 0, ":pending": "IN_PROGRESS", ":owner": owner}
                    ),
                )
            except ClientError:
                pass
            raise
        return "COMPLETED"


def handle(event: dict[str, Any], worker: Worker) -> dict[str, Any]:
    failures = []
    for record in event["Records"]:
        try:
            result = worker.process(record["body"])
            detail = json.loads(record["body"])["detail"]
            emit("notification-worker", result, fields=detail)
        except Exception:
            failures.append({"itemIdentifier": record["messageId"]})
            emit("notification-worker", "RETRY", level="ERROR", metrics={"NotificationFailures": 1})
    return {"batchItemFailures": failures}


@observed("notification-worker")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    return handle(
        event,
        Worker(
            CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"]),
            boto3.client(
                "ses",
                config=Config(retries={"max_attempts": 0}, connect_timeout=3, read_timeout=10),
            ),
            boto3.client("cognito-idp"),
            os.environ["USER_POOL_ID"],
            os.environ["SENDER_EMAIL"],
            os.environ["REVIEWER_EMAIL"],
        ),
    )
