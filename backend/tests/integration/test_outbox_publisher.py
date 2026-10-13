"""Outbox publisher integration with local DynamoDB/Streams and EventBridge."""

import copy
import json
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import patch

import boto3
import pytest
from botocore.exceptions import ClientError
from jsonschema import validate

from common.cases.repository import CaseRepository
from common.templates.repository import decode, encode
from common.templates.seed import SUPPLIER_ONBOARDING as SEED
from outbox_publisher.handler import Publisher, handle, json_number

ROOT = Path(__file__).resolve().parents[3]


def setup(repo: CaseRepository) -> tuple[Publisher, dict[str, Any]]:
    repo.create(SEED.case_type, "alice", "outbox-test")
    row = next(
        decode(item)
        for item in repo.client.scan(TableName=repo.table_name)["Items"]
        if item.get("entityType") == {"S": "OUTBOX"}
    )
    events = boto3.client(
        "events",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    arn = events.create_event_bus(Name="docflow-test-domain")["EventBusArn"]
    return Publisher(repo, events, arn), row


def record(row: dict[str, Any], sequence: str = "1", operation: str = "INSERT") -> dict[str, Any]:
    return {
        "eventSource": "aws:dynamodb",
        "eventName": operation,
        "dynamodb": {"SequenceNumber": sequence, "NewImage": encode(row)},
    }


def persisted(publisher: Publisher, row: dict[str, Any]) -> dict[str, Any]:
    return publisher.read({"PK": row["PK"], "SK": row["SK"]})


@pytest.mark.parametrize("operation", ["INSERT", "MODIFY"])
def test_publish_case_and_duplicate_replay(repo: CaseRepository, operation: str) -> None:
    publisher, row = setup(repo)
    with patch.object(publisher.events, "put_events", wraps=publisher.events.put_events) as send:
        assert handle({"Records": [record(row, operation=operation)]}, publisher) == {
            "batchItemFailures": []
        }
        assert handle({"Records": [record(row, operation=operation)]}, publisher) == {
            "batchItemFailures": []
        }
    assert send.call_count == 1
    entry = send.call_args.kwargs["Entries"][0]
    assert entry["Source"] == "docflow.case" and entry["EventBusName"] == publisher.bus_arn
    validate(
        json.loads(entry["Detail"]),
        json.loads((ROOT / "docs/events/case-created.schema.json").read_text()),
    )
    current = persisted(publisher, row)
    assert current["status"] == "DISPATCHED" and current["dispatchedAt"].endswith("Z")
    assert current["detail"] == row["detail"] and "expiresAtEpoch" not in current


@pytest.mark.parametrize(
    "kind,status", [("DocumentValidated", "VALID"), ("DocumentValidationFailed", "INVALID")]
)
def test_document_contract(repo: CaseRepository, kind: str, status: str) -> None:
    publisher, row = setup(repo)
    row.update(source="docflow.document", eventType=kind)
    row["detail"]["actor"] = {"type": "SYSTEM", "id": "document-processor"}
    row["detail"]["data"] = {
        "documentId": "d_fixture",
        "documentVersion": Decimal(1),
        "validationStatus": status,
        "validationErrors": [] if status == "VALID" else ["SIZE_INVALID"],
        "sha256": None,
    }
    repo.client.put_item(TableName=repo.table_name, Item=encode(row))
    with patch.object(publisher.events, "put_events", wraps=publisher.events.put_events) as send:
        publisher.publish(row)
    detail = json.loads(send.call_args.kwargs["Entries"][0]["Detail"])
    validate(detail, json.loads((ROOT / "docs/events/document-validation.schema.json").read_text()))
    assert type(detail["data"]["documentVersion"]) is int


@pytest.mark.parametrize(
    "result",
    [
        {"FailedEntryCount": 1, "Entries": [{"ErrorCode": "InternalFailure"}]},
        {"FailedEntryCount": 0, "Entries": [{"ErrorCode": "InternalFailure"}]},
        {"FailedEntryCount": 0, "Entries": [{}]},
        {"FailedEntryCount": 0, "Entries": []},
        {"Entries": [{"EventId": "accepted"}]},
    ],
)
def test_entry_failure_never_dispatches(repo: CaseRepository, result: dict[str, Any]) -> None:
    publisher, row = setup(repo)
    with patch.object(publisher.events, "put_events", return_value=result):
        assert handle({"Records": [record(row, "12")]}, publisher) == {
            "batchItemFailures": [{"itemIdentifier": "12"}]
        }
    assert persisted(publisher, row)["status"] == "PENDING"
    publisher.publish(row)
    assert persisted(publisher, row)["status"] == "DISPATCHED"


def test_send_exception_and_missing_bus(repo: CaseRepository) -> None:
    publisher, row = setup(repo)
    with patch.object(publisher.events, "put_events", side_effect=RuntimeError("network")):
        assert handle({"Records": [record(row)]}, publisher)["batchItemFailures"]
    publisher.events.delete_event_bus(Name="docflow-test-domain")
    with patch.object(publisher.events, "put_events") as send:
        assert handle({"Records": [record(row)]}, publisher)["batchItemFailures"]
        send.assert_not_called()
    assert persisted(publisher, row)["status"] == "PENDING"


def test_accepted_then_mark_failure_reuses_domain_id(repo: CaseRepository) -> None:
    publisher, row = setup(repo)
    with patch.object(publisher.events, "put_events", wraps=publisher.events.put_events) as send:
        with patch.object(repo.client, "update_item", side_effect=RuntimeError("crash after send")):
            assert handle({"Records": [record(row)]}, publisher)["batchItemFailures"]
        assert persisted(publisher, row)["status"] == "PENDING"
        publisher.publish(row)
    assert send.call_count == 2
    details = [json.loads(call.kwargs["Entries"][0]["Detail"]) for call in send.call_args_list]
    assert details[0] == details[1] and details[0]["eventId"] == row["eventId"]


def test_concurrent_dispatch_mark_is_safe(repo: CaseRepository) -> None:
    publisher, row = setup(repo)
    original = repo.client.update_item

    def concurrent(**kwargs: Any) -> Any:
        original(**kwargs)
        return original(**kwargs)

    with patch.object(repo.client, "update_item", side_effect=concurrent):
        publisher.publish(row)
    assert persisted(publisher, row)["status"] == "DISPATCHED"


def test_changed_fact_after_send_not_overwritten(repo: CaseRepository) -> None:
    publisher, row = setup(repo)
    original = publisher.events.put_events

    def changed(**kwargs: Any) -> Any:
        response = original(**kwargs)
        mutated = copy.deepcopy(row)
        mutated["detail"]["data"]["requesterId"] = "other"
        repo.client.put_item(TableName=repo.table_name, Item=encode(mutated))
        return response

    with patch.object(publisher.events, "put_events", side_effect=changed):
        with pytest.raises(ClientError):
            publisher.publish(row)
    assert persisted(publisher, row)["status"] == "PENDING"


@pytest.mark.parametrize(
    "entity,state,operation",
    [
        ("CASE", "PENDING", "INSERT"),
        ("AUDIT", "PENDING", "INSERT"),
        ("OUTBOX", "DISPATCHED", "MODIFY"),
        ("OUTBOX", "PENDING", "REMOVE"),
    ],
)
def test_unrelated_stream_changes_ignored(
    repo: CaseRepository, entity: str, state: str, operation: str
) -> None:
    publisher, row = setup(repo)
    row.update(entityType=entity, status=state)
    with patch.object(publisher.events, "put_events") as send:
        assert handle({"Records": [record(row, operation=operation)]}, publisher) == {
            "batchItemFailures": []
        }
        send.assert_not_called()


def test_first_failure_preserves_stream_order(repo: CaseRepository) -> None:
    publisher, row = setup(repo)
    with patch.object(
        publisher, "publish", side_effect=[None, RuntimeError("fail"), None]
    ) as publish:
        response = handle({"Records": [record(row, str(i)) for i in (1, 2, 3)]}, publisher)
    assert publish.call_count == 2
    assert response == {"batchItemFailures": [{"itemIdentifier": "2"}]}


@pytest.mark.parametrize("mutation", ["source", "detail", "key", "missing", "unknown", "malformed"])
def test_invalid_outbox_fails_closed(repo: CaseRepository, mutation: str) -> None:
    publisher, row = setup(repo)
    image = copy.deepcopy(row)
    if mutation == "source":
        image["source"] = "aws.s3"
    elif mutation == "detail":
        image["detail"]["eventId"] = "evt_forged"
    elif mutation == "key":
        image["PK"] = "TEMPLATE#other"
    elif mutation == "missing":
        repo.client.delete_item(
            TableName=repo.table_name, Key=encode({"PK": row["PK"], "SK": row["SK"]})
        )
    elif mutation == "unknown":
        image["eventType"] = "UnplannedEvent"
        repo.client.put_item(TableName=repo.table_name, Item=encode(image))
    else:
        image["detail"] = "{}"
        repo.client.put_item(TableName=repo.table_name, Item=encode(image))
    with patch.object(publisher.events, "put_events") as send:
        assert handle({"Records": [record(image)]}, publisher)["batchItemFailures"]
        send.assert_not_called()


@pytest.mark.parametrize("value", [Decimal("1.5"), Decimal("NaN"), Decimal("Infinity"), b"bytes"])
def test_no_lossy_json_conversion(value: Any) -> None:
    with pytest.raises(ValueError):
        json_number(value)


def test_real_local_stream_record(repo: CaseRepository) -> None:
    repo.client.update_table(
        TableName=repo.table_name,
        StreamSpecification={"StreamEnabled": True, "StreamViewType": "NEW_AND_OLD_IMAGES"},
    )
    publisher, _ = setup(repo)
    arn = repo.client.describe_table(TableName=repo.table_name)["Table"]["LatestStreamArn"]
    streams = boto3.client(
        "dynamodbstreams",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    shard = streams.describe_stream(StreamArn=arn)["StreamDescription"]["Shards"][0]["ShardId"]
    iterator = streams.get_shard_iterator(
        StreamArn=arn, ShardId=shard, ShardIteratorType="TRIM_HORIZON"
    )["ShardIterator"]
    records = streams.get_records(ShardIterator=iterator)["Records"]
    assert any(
        r.get("dynamodb", {}).get("NewImage", {}).get("entityType") == {"S": "OUTBOX"}
        for r in records
    )
    # Moto exposes real SDK stream records with DynamoDB SequenceNumber.
    assert handle({"Records": records}, publisher) == {"batchItemFailures": []}


@pytest.mark.parametrize(
    "bus",
    ["default", "docflow-dev-domain", "arn:aws:events:us-east-1:123456789012:event-bus/default"],
)
def test_custom_bus_required(repo: CaseRepository, bus: str) -> None:
    with pytest.raises(ValueError):
        Publisher(repo, object(), bus)


@pytest.mark.parametrize("sequence", ["", "not-a-sequence", None])
def test_malformed_sequence_fails_entire_batch(repo: CaseRepository, sequence: Any) -> None:
    publisher, row = setup(repo)
    event = record(row)
    event["dynamodb"]["SequenceNumber"] = sequence
    with pytest.raises(ValueError):
        handle({"Records": [event]}, publisher)


def test_safe_correlation_logging(repo: CaseRepository, capsys: pytest.CaptureFixture[str]) -> None:
    publisher, row = setup(repo)
    publisher.publish(row)
    text = capsys.readouterr().out
    logs = [json.loads(line) for line in text.splitlines()]
    assert len(logs) == 1
    assert logs[0]["message"] == "OUTBOX_DISPATCHED"
    for field in ("eventId", "caseId", "correlationId"):
        assert logs[0][field] == row[field]
    assert logs[0]["_aws"]["CloudWatchMetrics"][0]["Dimensions"] == [["service"]]
    assert logs[0]["CasesCreated"] == 1
    assert "alice" not in text and "SUPPLIER_ONBOARDING" not in text
