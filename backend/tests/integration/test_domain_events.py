"""Domain/default bus isolation using real local producers and publisher."""

import ast
import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import boto3
import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

from common.cases.repository import CaseRepository
from common.cases.submission import submit
from common.cases.workflow_state import fail, validate
from common.reviews.commands import execute
from common.reviews.creation import create_review
from common.reviews.decisions import decide
from common.reviews.finalization import finalize
from common.reviews.query import get_task
from common.templates.repository import decode, encode
from common.templates.seed import SUPPLIER_ONBOARDING as SEED
from document_api.command import reserve
from document_processor.handler import Processor
from outbox_publisher.handler import SOURCES, Publisher

ROOT = Path(__file__).resolve().parents[3]
BASE = "https://docflow.invalid/events/"
KINDS = [
    "CaseCreated",
    "DocumentValidated",
    "DocumentValidationFailed",
    "CaseSubmitted",
    "CaseResubmitted",
    "CaseWorkflowFailed",
    "CaseReadyForReview",
    "ReviewStarted",
    "CaseApproved",
    "CaseRejected",
    "AdditionalInformationRequested",
]
CHECKER = FormatChecker()


@CHECKER.checks("date-time", raises=ValueError)
def valid_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return True
    # stdlib check avoids silently disabled optional jsonschema format dependencies.
    return (
        bool(
            re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value
            )
        )
        and datetime.fromisoformat(value).tzinfo is not None
    )


def validator() -> Draft202012Validator:
    names = [
        "domain-event.schema.json",
        "case-created.schema.json",
        "case-submission.schema.json",
        "case-workflow-failed.schema.json",
        "case-ready-for-review.schema.json",
        "review-started.schema.json",
        "case-approved.schema.json",
        "case-rejected.schema.json",
        "additional-information-requested.schema.json",
        "document-validation.schema.json",
    ]
    registry: Registry[Any] = Registry().with_resources(
        [
            (
                BASE + name,
                Resource.from_contents(json.loads((ROOT / "docs/events" / name).read_text())),
            )
            for name in names
        ]
    )
    schema = json.loads((ROOT / "docs/events/domain-event.schema.json").read_text())
    return Draft202012Validator(schema, registry=registry, format_checker=CHECKER)


def make_fact(repo: CaseRepository, kind: str) -> dict[str, Any]:
    case = repo.create(SEED.case_type, "alice", "domain-test")
    if kind in {
        "CaseSubmitted",
        "CaseResubmitted",
        "CaseWorkflowFailed",
        "CaseReadyForReview",
        "ReviewStarted",
        "CaseApproved",
        "CaseRejected",
        "AdditionalInformationRequested",
    }:
        s3 = boto3.client(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        s3.create_bucket(Bucket="submission-documents")
        for doc_type in SEED.required_documents:
            content = b"%PDF-1.7\nfixture"
            doc = reserve(
                repo,
                case["caseId"],
                "alice",
                {"requester"},
                {
                    "documentType": doc_type,
                    "fileName": "fixture.pdf",
                    "fileSize": len(content),
                    "mimeType": "application/pdf",
                },
                "test",
            )
            uploaded = s3.put_object(
                Bucket="submission-documents",
                Key=doc["s3Key"],
                Body=content,
                ContentType="application/pdf",
            )
            processor = Processor(repo, s3, "submission-documents")
            body = json.dumps(
                {
                    "source": "aws.s3",
                    "detail-type": "Object Created",
                    "detail": {
                        "bucket": {"name": "submission-documents"},
                        "object": {
                            "key": doc["s3Key"],
                            "etag": uploaded["ETag"].strip('"'),
                            "size": len(content),
                        },
                    },
                }
            )
            processor.process(body)
            revision = repo.get(case["caseId"])["documentRevision"]
            processor.process(body)
            assert repo.get(case["caseId"])["documentRevision"] == revision
        assert repo.get(case["caseId"])["documentRevision"] == 16
        submit(repo, case["caseId"], "alice", {"requester"}, "submit", str(uuid4()), "test")
        if kind in {
            "CaseReadyForReview",
            "ReviewStarted",
            "CaseApproved",
            "CaseRejected",
            "AdditionalInformationRequested",
        }:
            current = repo.get(case["caseId"])
            event = {
                "submission": current["workflowInput"],
                "executionArn": "arn:aws:states:us-east-1:123456789012:execution:test:"
                + current["workflowExecutionName"],
                "taskToken": str(uuid4()),
                "enteredTime": "2026-09-17T00:00:00Z",
                "retryCount": 0,
            }
            assert validate(repo, event)["valid"]
            task = create_review(repo, event)["taskId"]
            if kind != "CaseReadyForReview":
                execute(repo, task, "bob", {"reviewer"}, "claim", {}, "test")
                execute(repo, task, "bob", {"reviewer"}, "start", {}, "test")
                if kind != "ReviewStarted":
                    for check in repo.related(case["caseId"], "CHECK#"):
                        execute(
                            repo,
                            task,
                            "bob",
                            {"reviewer"},
                            "check",
                            {"result": "PASS"},
                            "test",
                            check["checkId"],
                        )
                    payload: dict[str, Any] = {
                        "decision": {
                            "CaseApproved": "APPROVE",
                            "CaseRejected": "REJECT",
                            "AdditionalInformationRequested": "REQUEST_INFORMATION",
                        }[kind]
                    }
                    if kind != "CaseApproved":
                        payload["reason"] = "Review outcome"
                    if kind == "AdditionalInformationRequested":
                        payload["requestedItems"] = [
                            {
                                "documentType": SEED.required_documents[0],
                                "reasonCode": "MISSING",
                                "message": "Replacement required",
                            }
                        ]
                    decide(repo, task, "bob", {"reviewer"}, payload, str(uuid4()), "test", Mock())
                    finalize(repo, {**event, "decision": get_task(repo, task)["callbackOutput"]})

        if kind == "CaseWorkflowFailed":
            current = repo.get(case["caseId"])
            fail(
                repo,
                {
                    "submission": current["workflowInput"],
                    "executionArn": "arn:aws:states:us-east-1:123456789012:execution:test:"
                    + current["workflowExecutionName"],
                },
            )
        if kind == "CaseResubmitted":
            current = repo.get(case["caseId"])
            repo.client.put_item(
                TableName=repo.table_name, Item=encode({**current, "status": "NEEDS_INFORMATION"})
            )
            submit(repo, case["caseId"], "alice", {"requester"}, "resubmit", str(uuid4()), "test")
    elif kind != "CaseCreated":
        content = b"%PDF-1.7\nfixture" if kind == "DocumentValidated" else b"invalid fixture"
        doc = reserve(
            repo,
            case["caseId"],
            "alice",
            {"requester"},
            {
                "documentType": "COMPANY_REGISTRATION",
                "fileName": "registration.pdf",
                "fileSize": len(content),
                "mimeType": "application/pdf",
            },
            "domain-test",
        )
        s3 = boto3.client(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        s3.create_bucket(Bucket="domain-test-documents")
        uploaded = s3.put_object(
            Bucket="domain-test-documents",
            Key=doc["s3Key"],
            Body=content,
            ContentType="application/pdf",
        )
        Processor(repo, s3, "domain-test-documents").process(
            json.dumps(
                {
                    "source": "aws.s3",
                    "detail-type": "Object Created",
                    "detail": {
                        "bucket": {"name": "domain-test-documents"},
                        "object": {
                            "key": doc["s3Key"],
                            "etag": uploaded["ETag"].strip('"'),
                            "size": len(content),
                        },
                    },
                }
            )
        )
    return next(
        decode(row)
        for row in repo.client.scan(TableName=repo.table_name)["Items"]
        if row.get("eventType") == {"S": kind}
    )


def tap(events: Any, sqs: Any, bus: str, name: str) -> str:
    url = sqs.create_queue(QueueName=name)["QueueUrl"]
    arn = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["QueueArn"])["Attributes"][
        "QueueArn"
    ]
    # Identical patterns on each bus prove bus boundaries, not merely pattern differences.
    events.put_rule(
        Name=name,
        EventBusName=bus,
        EventPattern=json.dumps(
            {
                "source": ["docflow.case", "docflow.document", "docflow.review", "aws.s3"],
            }
        ),
    )
    events.put_targets(Rule=name, EventBusName=bus, Targets=[{"Id": name, "Arn": arn}])
    return str(url)


@pytest.mark.parametrize("kind", KINDS)
def test_producer_to_domain_bus_isolation(repo: CaseRepository, kind: str) -> None:
    args: dict[str, Any] = {
        "region_name": "us-east-1",
        "aws_access_key_id": "testing",
        "aws_secret_access_key": "testing",
    }
    events, sqs = boto3.client("events", **args), boto3.client("sqs", **args)
    arn = events.create_event_bus(Name="docflow-dev-domain")["EventBusArn"]
    domain, default = (
        tap(events, sqs, "docflow-dev-domain", "domain-tap"),
        tap(events, sqs, "default", "default-tap"),
    )
    fact = make_fact(repo, kind)
    assert fact["status"] == "PENDING"
    assert not sqs.receive_message(QueueUrl=domain).get("Messages")
    publisher = Publisher(repo, events, arn)
    publisher.publish(fact)
    publisher.publish(fact)
    messages = sqs.receive_message(QueueUrl=domain, MaxNumberOfMessages=10)["Messages"]
    assert len(messages) == 1
    envelope = json.loads(messages[0]["Body"])
    validator().validate(envelope)
    assert envelope["source"] == SOURCES[kind] and envelope["detail-type"] == kind
    assert envelope["detail"] == json.loads(json.dumps(fact["detail"], default=int))
    assert not sqs.receive_message(QueueUrl=default).get("Messages")
    sqs.delete_message(QueueUrl=domain, ReceiptHandle=messages[0]["ReceiptHandle"])
    # Synthetic AWS source is exclusively a Moto fixture, never published to real AWS.
    events.put_events(
        Entries=[
            {
                "EventBusName": "default",
                "Source": "aws.s3",
                "DetailType": "Object Created",
                "Detail": "{}",
            }
        ]
    )
    assert len(sqs.receive_message(QueueUrl=default)["Messages"]) == 1
    assert not sqs.receive_message(QueueUrl=domain).get("Messages")


@pytest.mark.parametrize("mutation", ["source", "kind", "version", "date", "internal", "status"])
def test_envelope_contract_rejects_mismatch(repo: CaseRepository, mutation: str) -> None:
    fact = make_fact(repo, "DocumentValidated")
    event = {
        "source": fact["source"],
        "detail-type": fact["eventType"],
        "detail": json.loads(json.dumps(fact["detail"], default=int)),
    }
    bad = copy.deepcopy(event)
    if mutation == "source":
        bad["source"] = "aws.s3"
    elif mutation == "kind":
        bad["detail-type"] = "CaseCreated"
    elif mutation == "version":
        bad["detail"]["eventVersion"] = "2.0"
    elif mutation == "date":
        bad["detail"]["occurredAt"] = "not-a-date"
    elif mutation == "internal":
        bad["detail"]["PK"] = "CASE#internal"
    else:
        bad["detail"]["data"]["validationStatus"] = "INVALID"
    with pytest.raises(ValidationError):
        validator().validate(bad)


def test_only_outbox_publisher_can_publish() -> None:
    publishers = set()
    for file in (ROOT / "backend/src").rglob("*.py"):
        for node in ast.walk(ast.parse(file.read_text())):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "put_events":
                    publishers.add(file.relative_to(ROOT / "backend/src").as_posix())
                if (
                    node.func.attr == "client"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                ):
                    if node.args[0].value == "events":
                        assert "outbox_publisher" in file.parts
    assert publishers == {"outbox_publisher/handler.py"}
    assert set(SOURCES) == set(KINDS)
