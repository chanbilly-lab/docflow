"""Local EventBridge-to-SQS routing of the exact Terraform pattern; no live AWS."""

import json
from pathlib import Path
from typing import Any

import boto3
import pytest
from moto import mock_aws

PATTERN = (
    Path(__file__).resolve().parents[3] / "infra/modules/document_pipeline/s3-created.json.tftpl"
)
BUCKET = "docflow-dev-documents-test"


@pytest.mark.parametrize(
    "source,kind,bucket,key,expected",
    [
        ("aws.s3", "Object Created", BUCKET, "cases/c_one/documents/d_one/v1/source", True),
        ("aws.s3", "Object Created", BUCKET, "cases/c_two/documents/d_two/v2/source", True),
        ("aws.s3", "Object Deleted", BUCKET, "cases/c_one/documents/d_one/v1/source", False),
        (
            "aws.s3",
            "Object Created",
            "other-bucket",
            "cases/c_one/documents/d_one/v1/source",
            False,
        ),
        (
            "docflow.document",
            "Object Created",
            BUCKET,
            "cases/c_one/documents/d_one/v1/source",
            False,
        ),
        ("aws.s3", "Object Created", BUCKET, "quarantine/c_one/source", False),
        ("aws.s3", "Object Created", BUCKET, "cases-other/source", False),
        ("aws.s3", "Object Created", BUCKET, "Cases/c_one/source", False),
        ("aws.s3", "Object Created", BUCKET, None, False),
        ("aws.s3", "Object Created", None, "cases/c_one/source", False),
    ],
)
def test_document_event_routing(
    source: str, kind: str, bucket: str | None, key: str | None, expected: bool
) -> None:
    rendered = PATTERN.read_text().replace("${jsonencode(bucket_name)}", json.dumps(BUCKET))
    # The single substitution above mirrors templatefile's one jsonencoded variable.
    json.loads(rendered)
    with mock_aws():
        args: dict[str, Any] = {
            "region_name": "us-east-1",
            "aws_access_key_id": "testing",
            "aws_secret_access_key": "testing",
        }
        events = boto3.client("events", **args)
        sqs = boto3.client("sqs", **args)
        queue = sqs.create_queue(QueueName="document-processing")["QueueUrl"]
        arn = sqs.get_queue_attributes(QueueUrl=queue, AttributeNames=["QueueArn"])["Attributes"][
            "QueueArn"
        ]
        events.put_rule(Name="document-created", EventBusName="default", EventPattern=rendered)
        events.put_targets(
            Rule="document-created", EventBusName="default", Targets=[{"Id": "queue", "Arn": arn}]
        )
        detail: dict[str, Any] = {"object": {"size": 12, "etag": "fixture", "sequencer": "001"}}
        if bucket is not None:
            detail["bucket"] = {"name": bucket}
        if key is not None:
            detail["object"]["key"] = key
        # AWS-owned source is a synthetic Moto fixture, never an instruction to publish to AWS.
        result = events.put_events(
            Entries=[
                {
                    "Source": source,
                    "DetailType": kind,
                    "Detail": json.dumps(detail),
                    "EventBusName": "default",
                    "Resources": [f"arn:aws:s3:::{BUCKET}"],
                }
            ]
        )
        assert result["FailedEntryCount"] == 0
        messages = sqs.receive_message(QueueUrl=queue, WaitTimeSeconds=0).get("Messages", [])
        assert len(messages) == int(expected)
        if expected:
            envelope = json.loads(messages[0]["Body"])
            assert envelope["source"] == source and envelope["detail-type"] == kind
            assert envelope["detail"] == detail
            # Moto does not add the AWS account field to its synthetic envelope.
            assert {"id", "time", "region", "resources", "version"} <= envelope.keys()
