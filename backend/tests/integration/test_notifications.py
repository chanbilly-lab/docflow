"""Notification effects are idempotent and isolated from committed business state."""

import json
from typing import Any
from unittest.mock import Mock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from test_domain_events import make_fact
from test_submission import rows

from common.cases.repository import CaseRepository
from common.templates.repository import encode
from notification_worker.handler import PARTITION, Worker, handle

KINDS = ["CaseReadyForReview", "AdditionalInformationRequested", "CaseApproved", "CaseRejected"]


def setup(
    repo: CaseRepository, kind: str = "CaseApproved"
) -> tuple[Worker, dict[str, Any], dict[str, Any]]:
    fact = make_fact(repo, kind)
    cognito = Mock()
    cognito.list_users.return_value = {
        "Users": [
            {
                "Enabled": True,
                "Attributes": [
                    {"Name": "sub", "Value": "alice"},
                    {"Name": "email", "Value": "alice@example.com"},
                    {"Name": "email_verified", "Value": "true"},
                ],
            }
        ]
    }
    ses = Mock()
    ses.send_email.return_value = {"MessageId": "ses-accepted"}
    worker = Worker(repo, ses, cognito, "pool", "sender@example.com", "reviewers@example.com")
    event = {
        "Records": [
            {
                "messageId": "queue-message",
                "body": json.dumps(
                    {
                        "id": "transport-id",
                        "source": fact["source"],
                        "detail-type": kind,
                        "detail": fact["detail"],
                    },
                    default=int,
                ),
            }
        ]
    }
    return worker, event, fact


def business(repo: CaseRepository) -> list[dict[str, Any]]:
    return [r for r in rows(repo) if r["PK"].startswith("CASE#")]


@pytest.mark.parametrize("kind", KINDS)
def test_each_template_replay_and_business_isolation(
    repo: CaseRepository, kind: str, capsys: Any
) -> None:
    worker, event, fact = setup(repo, kind)
    before = business(repo)
    assert handle(event, worker) == {"batchItemFailures": []}
    message = json.loads(event["Records"][0]["body"])
    message["id"] = "another-transport-id"
    event["Records"][0]["body"] = json.dumps(message, sort_keys=True)
    assert handle(event, worker) == {"batchItemFailures": []}
    assert worker.ses.send_email.call_count == 1
    call = worker.ses.send_email.call_args.kwargs
    assert call["Destination"]["ToAddresses"] == [
        "reviewers@example.com" if kind == "CaseReadyForReview" else "alice@example.com"
    ]
    assert fact["caseId"] in call["Message"]["Body"]["Text"]["Data"]
    assert "decisionReason" not in json.dumps(call)
    receipt = worker.read({"PK": PARTITION, "SK": "EVENT#" + fact["eventId"]})
    assert receipt["status"] == "COMPLETED" and receipt["messageId"] == "ses-accepted"
    assert "expiresAtEpoch" not in receipt and "leaseUntil" not in receipt
    assert business(repo) == before
    assert (
        "alice@example.com" not in (output := capsys.readouterr().out)
        and "sender@example.com" not in output
    )


def test_ses_failure_retries_without_case_rollback(repo: CaseRepository, capsys: Any) -> None:
    worker, event, _ = setup(repo)
    before = business(repo)
    worker.ses.send_email.side_effect = ClientError(
        {"Error": {"Code": "MessageRejected", "Message": "private email secret"}}, "SendEmail"
    )
    assert handle(event, worker) == {"batchItemFailures": [{"itemIdentifier": "queue-message"}]}
    assert business(repo) == before and "private email secret" not in capsys.readouterr().out
    worker.ses.send_email.side_effect = None
    assert handle(event, worker) == {"batchItemFailures": []}
    assert worker.ses.send_email.call_count == 2 and business(repo) == before


def test_live_lease_is_not_acknowledged_and_expired_lease_recovers(repo: CaseRepository) -> None:
    worker, event, fact = setup(repo)

    def overlap(**kwargs: Any) -> dict[str, str]:
        assert handle(event, worker)["batchItemFailures"]
        return {"MessageId": "accepted"}

    worker.ses.send_email.side_effect = overlap
    assert handle(event, worker) == {"batchItemFailures": []}
    assert worker.ses.send_email.call_count == 1
    key = {"PK": PARTITION, "SK": "EVENT#" + fact["eventId"]}
    receipt = worker.read(key)
    repo.client.put_item(
        TableName=repo.table_name,
        Item=encode({**receipt, "status": "IN_PROGRESS", "owner": "crashed", "leaseUntil": 0}),
    )
    worker.ses.send_email.side_effect = None
    assert handle(event, worker) == {"batchItemFailures": []}
    assert worker.read(key)["owner"] != "crashed"


@pytest.mark.parametrize("bad", ["disabled", "unverified", "wrong_sub", "missing", "multiple"])
def test_invalid_recipient_never_sends(repo: CaseRepository, bad: str) -> None:
    worker, event, _ = setup(repo)
    user = worker.cognito.list_users.return_value["Users"][0]
    if bad == "disabled":
        user["Enabled"] = False
    elif bad == "unverified":
        user["Attributes"][2]["Value"] = "false"
    elif bad == "wrong_sub":
        user["Attributes"][0]["Value"] = "carol"
    elif bad == "missing":
        worker.cognito.list_users.return_value = {"Users": []}
    else:
        worker.cognito.list_users.return_value = {"Users": [user, user]}
    assert handle(event, worker)["batchItemFailures"]
    worker.ses.send_email.assert_not_called()


def test_pagination_and_partial_batch(repo: CaseRepository) -> None:
    worker, event, _ = setup(repo)
    users = worker.cognito.list_users.return_value
    worker.cognito.list_users.side_effect = [{"Users": [], "PaginationToken": "next"}, users]
    event["Records"].insert(0, {"messageId": "bad", "body": "{}"})
    assert handle(event, worker) == {"batchItemFailures": [{"itemIdentifier": "bad"}]}
    assert worker.cognito.list_users.call_args.kwargs["PaginationToken"] == "next"


@pytest.mark.parametrize("tamper", ["source", "type", "detail", "uncommitted"])
def test_only_authentic_supported_facts_send(repo: CaseRepository, tamper: str) -> None:
    worker, event, _ = setup(repo)
    data = json.loads(event["Records"][0]["body"])
    if tamper == "source":
        data["source"] = "aws.s3"
    elif tamper == "type":
        data["detail-type"] = "CaseCreated"
    elif tamper == "detail":
        data["detail"]["data"]["recipient"] = "attacker@example.com"
    else:
        data["detail"]["eventId"] = "evt_unknown"
    event["Records"][0]["body"] = json.dumps(data)
    before = rows(repo)
    assert handle(event, worker)["batchItemFailures"]
    worker.ses.send_email.assert_not_called()
    assert rows(repo) == before


def test_accepted_send_failed_mark_is_at_least_once(repo: CaseRepository) -> None:
    worker, event, _ = setup(repo)
    before = business(repo)
    original = repo.client.update_item

    def fail_mark(**kwargs: Any) -> Any:
        if "processedAt" in kwargs["UpdateExpression"]:
            raise ClientError({"Error": {"Code": "InternalServerError"}}, "UpdateItem")
        return original(**kwargs)

    with patch.object(repo.client, "update_item", side_effect=fail_mark):
        assert handle(event, worker)["batchItemFailures"]
    assert handle(event, worker) == {"batchItemFailures": []}
    assert worker.ses.send_email.call_count == 2  # SES has no idempotency token.
    assert business(repo) == before


def test_mock_bus_rules_route_only_notifications_to_queue(repo: CaseRepository) -> None:
    worker, event, fact = setup(repo, "CaseReadyForReview")
    args: dict[str, Any] = {
        "region_name": "us-east-1",
        "aws_access_key_id": "testing",
        "aws_secret_access_key": "testing",
    }
    events, sqs = boto3.client("events", **args), boto3.client("sqs", **args)
    events.create_event_bus(Name="notification-domain")
    dlq = sqs.create_queue(QueueName="notification-dlq")["QueueUrl"]
    dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq, AttributeNames=["QueueArn"])["Attributes"][
        "QueueArn"
    ]
    url = sqs.create_queue(
        QueueName="notification",
        Attributes={
            "VisibilityTimeout": "0",
            "RedrivePolicy": json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": 5}),
        },
    )["QueueUrl"]
    arn = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["QueueArn"])["Attributes"][
        "QueueArn"
    ]
    events.put_rule(
        Name="notifications",
        EventBusName="notification-domain",
        EventPattern=json.dumps({"source": ["docflow.case"], "detail-type": KINDS}),
    )
    events.put_targets(
        Rule="notifications",
        EventBusName="notification-domain",
        Targets=[{"Id": "queue", "Arn": arn}],
    )
    from outbox_publisher.handler import Publisher

    bus_arn = events.describe_event_bus(Name="notification-domain")["Arn"]
    Publisher(repo, events, bus_arn).publish(fact)
    message = sqs.receive_message(QueueUrl=url)["Messages"][0]
    assert handle(
        {"Records": [{"messageId": message["MessageId"], "body": message["Body"]}]}, worker
    ) == {"batchItemFailures": []}
    sqs.delete_message(QueueUrl=url, ReceiptHandle=message["ReceiptHandle"])
    events.put_events(
        Entries=[
            {
                "EventBusName": "notification-domain",
                "Source": "docflow.case",
                "DetailType": "ReviewStarted",
                "Detail": "{}",
            }
        ]
    )
    assert not sqs.receive_message(QueueUrl=url).get("Messages")
    # Poison message retry exhaustion enters the processing DLQ.
    sqs.send_message(QueueUrl=url, MessageBody="malformed")
    for _ in range(6):
        for poison in sqs.receive_message(QueueUrl=url).get("Messages", []):
            assert handle(
                {"Records": [{"messageId": poison["MessageId"], "body": poison["Body"]}]}, worker
            )["batchItemFailures"]
    assert len(sqs.receive_message(QueueUrl=dlq)["Messages"]) == 1
