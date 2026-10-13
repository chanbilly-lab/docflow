"""Actual processor against local DynamoDB/S3/SQS; no live AWS."""

import hashlib
import json
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
from document_api.command import reserve
from document_api.deletion import delete_document
from document_processor.handler import Processor, RetryProcessing, handle, parse

BUCKET = "processor-test"
CONTENT = b"%PDF-1.7\nfixture"


def setup(
    repo: CaseRepository, content: bytes = CONTENT, **metadata: Any
) -> tuple[Processor, dict[str, Any], str]:
    case = repo.create(SEED.case_type, "alice", "test")
    doc = reserve(
        repo,
        case["caseId"],
        "alice",
        {"requester"},
        {
            "documentType": "COMPANY_REGISTRATION",
            "fileName": "registration.pdf",
            "mimeType": "application/pdf",
            "fileSize": len(content),
            **metadata,
        },
        "test",
    )
    s3 = boto3.client(
        "s3", region_name="us-east-1", aws_access_key_id="testing", aws_secret_access_key="testing"
    )
    s3.create_bucket(Bucket=BUCKET)
    result = s3.put_object(
        Bucket=BUCKET, Key=doc["s3Key"], Body=content, ContentType="application/pdf"
    )
    body = json.dumps(
        {
            "source": "aws.s3",
            "detail-type": "Object Created",
            "detail": {
                "bucket": {"name": BUCKET},
                "object": {
                    "key": doc["s3Key"],
                    "etag": result["ETag"].strip('"'),
                    "size": len(content),
                },
            },
        }
    )
    return Processor(repo, s3, BUCKET), doc, body


def rows(repo: CaseRepository) -> list[dict[str, Any]]:
    return [decode(row) for row in repo.client.scan(TableName=repo.table_name)["Items"]]


def document(processor: Processor, doc: dict[str, Any]) -> dict[str, Any]:
    return processor.read({"PK": doc["PK"], "SK": doc["SK"]})


@pytest.mark.parametrize("duplicate", [False, True])
def test_valid_atomic_effects(repo: CaseRepository, duplicate: bool) -> None:
    processor, doc, body = setup(repo)
    processor.process(body)
    before = rows(repo)
    if duplicate:
        processor.process(body)
        assert rows(repo) == before
    result = document(processor, doc)
    assert result["status"] == "VALID" and result["sha256"] == hashlib.sha256(CONTENT).hexdigest()
    assert result["scanStatus"] == "NOT_IMPLEMENTED"
    audits = [r for r in before if r.get("action", "").startswith("DOCUMENT_")]
    assert len(audits) == 4
    outbox = [r for r in before if r.get("source") == "docflow.document"]
    assert len(outbox) == 1 and outbox[0]["status"] == "PENDING"
    assert "expiresAtEpoch" not in outbox[0]
    validate(
        json.loads(json.dumps(outbox[0]["detail"], default=int)),
        json.loads(
            (
                Path(__file__).resolve().parents[3] / "docs/events/document-validation.schema.json"
            ).read_text()
        ),
    )


@pytest.mark.parametrize(
    "metadata,content,reason",
    [
        ({"fileName": "file.exe"}, CONTENT, "EXTENSION_MISMATCH"),
        ({"fileSize": 100}, CONTENT, "SIZE_INVALID"),
        ({}, b"not a PDF", "CONTENT_SIGNATURE_MISMATCH"),
        ({"mimeType": "image/png"}, CONTENT, "MIME_MISMATCH"),
        ({"documentType": ""}, CONTENT, "METADATA_MISSING"),
    ],
)
def test_invalid_business_result(
    repo: CaseRepository, metadata: dict[str, Any], content: bytes, reason: str
) -> None:
    # Required type is valid at reservation; tamper persisted metadata to exercise worker defense.
    processor, doc, body = setup(repo, content)
    repo.client.put_item(TableName=repo.table_name, Item=encode({**doc, **metadata}))
    processor.process(body)
    result = document(processor, doc)
    assert result["status"] == "INVALID" and reason in result["validationErrors"]
    outbox = [r for r in rows(repo) if r.get("source") == "docflow.document"][0]
    assert outbox["eventType"] == "DocumentValidationFailed"
    validate(
        json.loads(json.dumps(outbox["detail"], default=int)),
        json.loads(
            (
                Path(__file__).resolve().parents[3] / "docs/events/document-validation.schema.json"
            ).read_text()
        ),
    )


def test_deleted_and_delete_race(repo: CaseRepository) -> None:
    processor, doc, body = setup(repo)
    original = processor.validate

    def deleting(*args: Any) -> Any:
        result = original(*args)
        delete_document(repo, doc["caseId"], doc["documentId"], "alice", {"requester"}, "test")
        return result

    with patch.object(processor, "validate", side_effect=deleting):
        with pytest.raises(ClientError):
            processor.process(body)
    assert document(processor, doc)["status"] == "DELETED"
    assert not [r for r in rows(repo) if r.get("source") == "docflow.document"]
    with patch("document_processor.handler.time.time", return_value=9999999999):
        processor.process(body)
    assert document(processor, doc)["status"] == "DELETED"


def test_predeleted_ack(repo: CaseRepository) -> None:
    processor, doc, body = setup(repo)
    delete_document(repo, doc["caseId"], doc["documentId"], "alice", {"requester"}, "test")
    with patch.object(processor.s3, "head_object", side_effect=AssertionError):
        processor.process(body)
    assert document(processor, doc)["status"] == "DELETED"


def test_crash_lease_recovery_and_busy_retry(repo: CaseRepository) -> None:
    processor, doc, body = setup(repo)
    with patch.object(processor, "validate", side_effect=RuntimeError("forced")):
        with pytest.raises(RuntimeError):
            processor.process(body)
    assert document(processor, doc)["status"] == "VALIDATING"
    with pytest.raises(RetryProcessing):
        processor.process(body)
    with patch("document_processor.handler.time.time", return_value=9999999999):
        processor.process(body)
    assert document(processor, doc)["status"] == "VALID"
    assert len([r for r in rows(repo) if r.get("action") == "DOCUMENT_VALIDATING"]) == 1


def test_transaction_rollback(repo: CaseRepository) -> None:
    processor, doc, body = setup(repo)
    original = repo.client.transact_write_items

    def fail_final(**kwargs: Any) -> Any:
        if any(
            w.get("Put", {}).get("Item", {}).get("entityType") == {"S": "OUTBOX"}
            for w in kwargs["TransactItems"]
        ):
            raise RuntimeError("forced transaction failure")
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=fail_final):
        with pytest.raises(RuntimeError):
            processor.process(body)
    assert document(processor, doc)["status"] == "VALIDATING"
    assert not [r for r in rows(repo) if r.get("source") == "docflow.document"]
    assert [r for r in rows(repo) if r.get("entityType") == "IDEMPOTENCY"][0][
        "status"
    ] == "IN_PROGRESS"
    with patch("document_processor.handler.time.time", return_value=9999999999):
        processor.process(body)
    assert document(processor, doc)["status"] == "VALID"


@pytest.mark.parametrize("field,value", [("source", "forged"), ("detail-type", "Object Deleted")])
def test_wrong_envelope(repo: CaseRepository, field: str, value: str) -> None:
    processor, _, body = setup(repo)
    event = json.loads(body)
    event[field] = value
    with pytest.raises(ValueError):
        processor.process(json.dumps(event))
    assert not [r for r in rows(repo) if r.get("entityType") == "IDEMPOTENCY"]


@pytest.mark.parametrize(
    "field,value",
    [("key", "cases/../source"), ("etag", ""), ("size", -1), ("version-id", ""), ("size", True)],
)
def test_bad_object(repo: CaseRepository, field: str, value: Any) -> None:
    processor, _, body = setup(repo)
    event = json.loads(body)
    event["detail"]["object"][field] = value
    with pytest.raises(ValueError):
        processor.process(json.dumps(event))


def test_partial_batch(repo: CaseRepository) -> None:
    processor, doc, body = setup(repo)
    result = handle(
        {"Records": [{"messageId": "bad", "body": "broken"}, {"messageId": "good", "body": body}]},
        processor,
    )
    assert result == {"batchItemFailures": [{"itemIdentifier": "bad"}]}
    assert document(processor, doc)["status"] == "VALID"


def test_local_forced_failure_redrive(repo: CaseRepository) -> None:
    processor, _, _ = setup(repo)
    sqs = boto3.client(
        "sqs", region_name="us-east-1", aws_access_key_id="testing", aws_secret_access_key="testing"
    )
    dlq = sqs.create_queue(QueueName="processor-dlq")["QueueUrl"]
    arn = sqs.get_queue_attributes(QueueUrl=dlq, AttributeNames=["QueueArn"])["Attributes"][
        "QueueArn"
    ]
    queue = sqs.create_queue(
        QueueName="processor",
        Attributes={
            "VisibilityTimeout": "0",
            "RedrivePolicy": json.dumps({"deadLetterTargetArn": arn, "maxReceiveCount": 5}),
        },
    )["QueueUrl"]
    sqs.send_message(QueueUrl=queue, MessageBody="forced malformed event")
    for _ in range(5):
        msg = sqs.receive_message(QueueUrl=queue)["Messages"][0]
        assert handle(
            {"Records": [{"messageId": msg["MessageId"], "body": msg["Body"]}]}, processor
        )["batchItemFailures"]
    assert "Messages" not in sqs.receive_message(QueueUrl=queue)
    assert sqs.receive_message(QueueUrl=dlq)["Messages"][0]["Body"] == "forced malformed event"


def test_completed_ttl_removal_still_no_duplicate(repo: CaseRepository) -> None:
    processor, doc, body = setup(repo)
    processor.process(body)
    identity = parse(body, BUCKET)["identity"]
    repo.client.delete_item(
        TableName=repo.table_name,
        Key=encode({"PK": "IDEMPOTENCY#document-processor", "SK": "EVENT#" + identity}),
    )
    processor.process(body)
    assert document(processor, doc)["status"] == "VALID"
    assert len([r for r in rows(repo) if r.get("source") == "docflow.document"]) == 1


@pytest.mark.parametrize("mutation", ["bucket", "key", "etag", "missing"])
def test_source_errors_retry_without_business_effect(repo: CaseRepository, mutation: str) -> None:
    processor, doc, body = setup(repo)
    if mutation == "missing":
        processor.s3.delete_object(Bucket=BUCKET, Key=doc["s3Key"])
    elif mutation == "key":
        repo.client.put_item(TableName=repo.table_name, Item=encode({**doc, "s3Key": "other"}))
    else:
        event = json.loads(body)
        if mutation == "bucket":
            event["detail"]["bucket"]["name"] = "other"
        else:
            event["detail"]["object"]["etag"] = "a" * 32
        body = json.dumps(event)
    assert handle({"Records": [{"messageId": "retry", "body": body}]}, processor) == {
        "batchItemFailures": [{"itemIdentifier": "retry"}]
    }
    assert not [r for r in rows(repo) if r.get("source") == "docflow.document"]


def test_lost_lease_rolls_back_final_transaction(repo: CaseRepository) -> None:
    processor, doc, body = setup(repo)
    original = processor.validate

    def steal(*args: Any) -> Any:
        result = original(*args)
        claim = [r for r in rows(repo) if r.get("entityType") == "IDEMPOTENCY"][0]
        repo.client.put_item(
            TableName=repo.table_name, Item=encode({**claim, "owner": "new-worker"})
        )
        return result

    with patch.object(processor, "validate", side_effect=steal):
        with pytest.raises(ClientError):
            processor.process(body)
    assert document(processor, doc)["status"] == "VALIDATING"
    assert not [r for r in rows(repo) if r.get("action") == "DOCUMENT_VALID"]
    assert not [r for r in rows(repo) if r.get("source") == "docflow.document"]


@pytest.mark.parametrize(
    "mime,name,content",
    [
        ("image/jpeg", "IMAGE.JPEG", b"\xff\xd8\xfffixture"),
        ("image/png", "image.png", b"\x89PNG\r\n\x1a\nfixture"),
    ],
)
def test_image_signature_and_digest(
    repo: CaseRepository, mime: str, name: str, content: bytes
) -> None:
    processor, doc, body = setup(repo, content, mimeType=mime, fileName=name)
    processor.s3.put_object(Bucket=BUCKET, Key=doc["s3Key"], Body=content, ContentType=mime)
    processor.process(body)
    assert document(processor, doc)["status"] == "VALID"
    assert document(processor, doc)["sha256"] == hashlib.sha256(content).hexdigest()


def test_versioned_object_is_pinned(repo: CaseRepository) -> None:
    processor, doc, body = setup(repo)
    processor.s3.put_bucket_versioning(Bucket=BUCKET, VersioningConfiguration={"Status": "Enabled"})
    result = processor.s3.put_object(
        Bucket=BUCKET, Key=doc["s3Key"], Body=CONTENT, ContentType="application/pdf"
    )
    processor.s3.put_object(
        Bucket=BUCKET, Key=doc["s3Key"], Body=b"newer", ContentType="text/plain"
    )
    event = json.loads(body)
    event["detail"]["object"]["version-id"] = result["VersionId"]
    processor.process(json.dumps(event))
    assert document(processor, doc)["status"] == "VALID"
