"""Shared local DynamoDB integration fixture; no live AWS calls."""

from collections.abc import Iterator

import boto3
import pytest
from moto import mock_aws

from common.cases.repository import CaseRepository
from common.templates.repository import TemplateRepository
from common.templates.seed import SUPPLIER_ONBOARDING as SEED


@pytest.fixture
def repo() -> Iterator[CaseRepository]:
    with mock_aws():
        client = boto3.client(
            "dynamodb",
            region_name="us-east-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        client.create_table(
            TableName="docflow-test",
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": name, "AttributeType": "S"}
                for name in ("PK", "SK", "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK")
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": name,
                    "KeySchema": [
                        {"AttributeName": name + "PK", "KeyType": "HASH"},
                        {"AttributeName": name + "SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
                for name in ("GSI1", "GSI2")
            ],
        )
        TemplateRepository(client, "docflow-test").publish(SEED, actor_id="seed")
        yield CaseRepository(client, "docflow-test")
