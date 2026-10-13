"""Atomic immutable publication and strongly consistent version lookup."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError

from common.templates.models import Check, Template, identifier

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient
    from mypy_boto3_dynamodb.type_defs import QueryInputTypeDef

CASE_TEMPLATES = {"SUPPLIER_ONBOARDING": "supplier-onboarding"}


class TemplateNotFound(LookupError):
    """Requested active or historical definition does not exist."""


class TemplateConflict(ValueError):
    """An immutable version already exists with different/incomplete contents."""


def encode(item: dict[str, Any]) -> dict[str, Any]:
    serializer = TypeSerializer()
    return {key: serializer.serialize(value) for key, value in item.items()}


def decode(item: dict[str, Any]) -> dict[str, Any]:
    deserializer = TypeDeserializer()
    return {key: deserializer.deserialize(value) for key, value in item.items()}


class TemplateRepository:
    def __init__(self, client: DynamoDBClient, table_name: str, *, page_size: int = 100):
        if not table_name or not 1 <= page_size <= 1000:
            raise ValueError("A table name and page size from 1 to 1000 are required.")
        self.client = client
        self.table_name = table_name
        self.page_size = page_size

    def _query(self, template_id: str, prefix: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        cursor: dict[str, Any] = {}
        while True:
            request: QueryInputTypeDef = {
                "TableName": self.table_name,
                "KeyConditionExpression": "PK = :pk AND begins_with(SK, :prefix)",
                "ExpressionAttributeValues": encode(
                    {":pk": f"TEMPLATE#{template_id}", ":prefix": prefix}
                ),
                "ConsistentRead": True,
                "Limit": self.page_size,
            }
            if cursor:
                request["ExclusiveStartKey"] = cursor
            response = self.client.query(**request)
            items.extend(decode(item) for item in response.get("Items", []))
            cursor = response.get("LastEvaluatedKey", {})
            if not cursor:
                return items

    def get_version(self, template_id: str, version: int) -> Template:
        identifier(template_id)
        if type(version) is not int or version < 1:
            raise ValueError("Version must be positive.")
        response = self.client.get_item(
            TableName=self.table_name,
            Key=encode({"PK": f"TEMPLATE#{template_id}", "SK": f"VERSION#{version}"}),
            ConsistentRead=True,
        )
        if "Item" not in response:
            raise TemplateNotFound("Template version not found.")
        metadata = decode(response["Item"])
        rows = self._query(template_id, f"VERSION#{version}#CHECK#")
        if len(rows) != metadata.get("checkCount") or not rows:
            raise TemplateConflict("Stored check definitions are incomplete.")
        template = Template(
            template_id=metadata["templateId"],
            version=int(metadata["version"]),
            case_type=metadata["caseType"],
            required_documents=tuple(metadata["requiredDocuments"]),
            checks=tuple(
                sorted(
                    (
                        Check(
                            row["checkId"],
                            int(row["order"]),
                            row["documentType"],
                            row["required"],
                            row["instructions"],
                        )
                        for row in rows
                    ),
                    key=lambda check: check.order,
                )
            ),
        )
        if (
            template.template_id != template_id
            or template.version != version
            or len(rows) != metadata["checkCount"]
            or self._digest(template) != metadata["contentHash"]
        ):
            raise TemplateConflict("Stored template content is incomplete or inconsistent.")
        return template

    def resolve_active(self, case_type: str) -> Template:
        template_id = CASE_TEMPLATES.get(case_type)
        if template_id is None:
            raise TemplateNotFound("Unsupported case type.")
        versions = [
            int(item["version"])
            for item in self._query(template_id, "VERSION#")
            if item.get("entityType") == "CHECKLIST_TEMPLATE"
            and item.get("status") == "ACTIVE"
            and item.get("caseType") == case_type
        ]
        if not versions:
            raise TemplateNotFound("No active template.")
        return self.get_version(template_id, max(versions))

    @staticmethod
    def _digest(template: Template) -> str:
        data = json.dumps(template.content(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()

    def publish(self, template: Template, *, actor_id: str) -> bool:
        """Return True on creation, False on exact replay; never overwrite."""
        identifier(actor_id)
        if CASE_TEMPLATES.get(template.case_type) != template.template_id:
            raise ValueError("Template does not match the configured case type.")
        try:
            existing = self.get_version(template.template_id, template.version)
        except TemplateNotFound:
            pass
        else:
            if existing.content() == template.content():
                return False
            raise TemplateConflict("Version already exists; publish a new version.")
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        pk = f"TEMPLATE#{template.template_id}"
        items: list[dict[str, Any]] = [
            {
                "PK": pk,
                "SK": f"VERSION#{template.version}",
                "entityType": "CHECKLIST_TEMPLATE",
                "templateId": template.template_id,
                "version": template.version,
                "caseType": template.case_type,
                "status": "ACTIVE",
                "requiredDocuments": list(template.required_documents),
                "createdAt": timestamp,
                "checkCount": len(template.checks),
                "contentHash": self._digest(template),
            }
        ]
        for check in template.checks:
            items.append(
                {
                    "PK": pk,
                    "SK": f"VERSION#{template.version}#CHECK#{check.order}#{check.check_id}",
                    "entityType": "CHECKLIST_CHECK",
                    "checkId": check.check_id,
                    "order": check.order,
                    "documentType": check.document_type,
                    "required": check.required,
                    "instructions": check.instructions,
                }
            )
        audit_id = f"a_{uuid4().hex}"
        items.append(
            {
                "PK": pk,
                "SK": f"AUDIT#{timestamp}#{audit_id}",
                "entityType": "AUDIT",
                "auditId": audit_id,
                "actorId": actor_id,
                "actorType": "OPERATOR",
                "action": "TEMPLATE_VERSION_PUBLISHED",
                "resourceType": "CHECKLIST_TEMPLATE",
                "resourceId": template.template_id,
                "version": template.version,
                "timestamp": timestamp,
                "contentHash": self._digest(template),
            }
        )
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": encode(item),
                            "ConditionExpression": "attribute_not_exists(PK)",
                        }
                    }
                    for item in items
                ]
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "TransactionCanceledException":
                raise
            # A racing identical seed may have committed. Other cancellation causes
            # must remain errors, not be mistaken for successful publication.
            try:
                existing = self.get_version(template.template_id, template.version)
            except TemplateNotFound:
                raise exc from None
            if existing.content() != template.content():
                raise TemplateConflict("Conflicting concurrent publication.") from exc
            return False
        return True
