"""Exercise the real repository through boto3 against an in-process DynamoDB emulator."""

from collections.abc import Iterator
from dataclasses import replace
from typing import Any
from unittest.mock import patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from common.templates.repository import (
    TemplateConflict,
    TemplateNotFound,
    TemplateRepository,
    decode,
    encode,
)
from common.templates.seed import SUPPLIER_ONBOARDING as SEED


@pytest.fixture
def repository() -> Iterator[TemplateRepository]:
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
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
        )
        yield TemplateRepository(client, "docflow-test", page_size=1)


def stored(repository: TemplateRepository) -> list[dict[str, Any]]:
    return [
        decode(item) for item in repository.client.scan(TableName=repository.table_name)["Items"]
    ]


def test_seed_is_repeatable_and_audited(repository: TemplateRepository) -> None:
    assert repository.publish(SEED, actor_id="test-operator")
    original = stored(repository)
    assert not repository.publish(SEED, actor_id="another-operator")
    assert stored(repository) == original
    assert len(original) == len(SEED.checks) + 2
    assert repository.resolve_active(SEED.case_type) == SEED
    audits = [item for item in original if item["entityType"] == "AUDIT"]
    assert len(audits) == 1
    assert audits[0]["actorId"] == "test-operator"
    assert audits[0]["action"] == "TEMPLATE_VERSION_PUBLISHED"
    assert all(item["PK"] == "TEMPLATE#supplier-onboarding" for item in original)
    assert any(item["SK"] == "VERSION#1" for item in original)
    assert any(item["SK"] == "VERSION#1#CHECK#1#company-registration-readable" for item in original)


def test_numeric_active_and_historical_versions_with_pagination(
    repository: TemplateRepository,
) -> None:
    for version in (1, 10, 2):
        repository.publish(replace(SEED, version=version), actor_id="operator")
    assert repository.resolve_active(SEED.case_type).version == 10
    assert repository.get_version(SEED.template_id, 1) == SEED
    assert repository.get_version(SEED.template_id, 2).version == 2


def test_conflicting_seed_never_overwrites(repository: TemplateRepository) -> None:
    repository.publish(SEED, actor_id="operator")
    before = stored(repository)
    changed = replace(
        SEED, checks=(replace(SEED.checks[0], instructions="Changed"), *SEED.checks[1:])
    )
    with pytest.raises(TemplateConflict):
        repository.publish(changed, actor_id="operator")
    assert stored(repository) == before


def test_no_partial_write_when_a_check_key_already_exists(repository: TemplateRepository) -> None:
    repository.client.put_item(
        TableName=repository.table_name,
        Item=encode(
            {
                "PK": "TEMPLATE#supplier-onboarding",
                "SK": "VERSION#1#CHECK#1#company-registration-readable",
                "entityType": "FOREIGN",
            }
        ),
    )
    with pytest.raises(ClientError):
        repository.publish(SEED, actor_id="operator")
    assert len(stored(repository)) == 1
    with pytest.raises(TemplateNotFound):
        repository.get_version(SEED.template_id, 1)


def test_missing_and_unknown_templates(repository: TemplateRepository) -> None:
    with pytest.raises(TemplateNotFound):
        repository.resolve_active(SEED.case_type)
    with pytest.raises(TemplateNotFound):
        repository.resolve_active("UNKNOWN")
    with pytest.raises(TemplateNotFound):
        repository.get_version(SEED.template_id, 42)


def test_damaged_check_is_not_silently_reseeded(repository: TemplateRepository) -> None:
    repository.publish(SEED, actor_id="operator")
    repository.client.delete_item(
        TableName=repository.table_name,
        Key=encode(
            {
                "PK": "TEMPLATE#supplier-onboarding",
                "SK": "VERSION#1#CHECK#1#company-registration-readable",
            }
        ),
    )
    with pytest.raises(TemplateConflict):
        repository.publish(SEED, actor_id="operator")


def test_identical_publication_race_is_recovered(repository: TemplateRepository) -> None:
    original = repository.client.transact_write_items

    def commit_then_cancel(**kwargs: Any) -> None:
        original(**kwargs)
        raise ClientError({"Error": {"Code": "TransactionCanceledException"}}, "TransactWriteItems")

    with patch.object(repository.client, "transact_write_items", side_effect=commit_then_cancel):
        assert not repository.publish(SEED, actor_id="operator")
    assert len(stored(repository)) == len(SEED.checks) + 2


def test_service_errors_are_not_reported_as_success(repository: TemplateRepository) -> None:
    error = ClientError({"Error": {"Code": "AccessDeniedException"}}, "TransactWriteItems")
    with patch.object(repository.client, "transact_write_items", side_effect=error):
        with pytest.raises(ClientError):
            repository.publish(SEED, actor_id="operator")
    assert stored(repository) == []
