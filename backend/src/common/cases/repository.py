"""DynamoDB Case creation, queries and scope-bound pagination."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from common.templates.repository import TemplateRepository, decode, encode

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient
    from mypy_boto3_dynamodb.type_defs import QueryInputTypeDef

STATES = frozenset(
    {
        "DRAFT",
        "SUBMITTED",
        "PROCESSING",
        "REVIEW_PENDING",
        "IN_REVIEW",
        "NEEDS_INFORMATION",
        "APPROVED",
        "REJECTED",
        "WORKFLOW_FAILED",
    }
)


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code = status, code


def public(item: dict[str, Any], fields: str) -> dict[str, Any]:
    # Scalar-only whitelist prevents nested internal attributes leaking through.
    return {
        key: item[key]
        for key in fields.split()
        if key in item and not isinstance(item[key], (dict, list, set))
    }


def case_view(item: dict[str, Any]) -> dict[str, Any]:
    result = public(
        item, "caseId caseType requesterId status submissionAttempt version createdAt updatedAt"
    )
    result["checklistTemplate"] = {
        "id": item["checklistTemplateId"],
        "version": int(item["checklistTemplateVersion"]),
    }
    return result


def position_token(position: str, scope: str) -> str:
    data = {"position": position, "scope": hashlib.sha256(scope.encode()).hexdigest()}
    return base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode()).decode()


def read_position(token: str | None, scope: str, pattern: str) -> str | None:
    if token is None:
        return None
    try:
        if len(token) > 2048:
            raise ValueError
        data = json.loads(base64.b64decode(token, altchars=b"-_", validate=True))
        if (
            not isinstance(data, dict)
            or set(data) != {"position", "scope"}
            or data["scope"] != hashlib.sha256(scope.encode()).hexdigest()
            or not isinstance(data["position"], str)
            or not re.fullmatch(pattern, data["position"])
        ):
            raise ValueError
        return str(data["position"])
    except (ValueError, TypeError, UnicodeError) as exc:
        raise ApiError(400, "CURSOR_INVALID", "Invalid cursor for this query.") from exc


class CaseRepository:
    def __init__(self, client: DynamoDBClient, table_name: str):
        self.client, self.table_name = client, table_name

    def create(self, case_type: str, actor: str, correlation_id: str) -> dict[str, Any]:
        template = TemplateRepository(self.client, self.table_name).resolve_active(case_type)
        case_id, event_id, audit_id = (f"{prefix}_{uuid4().hex}" for prefix in ("c", "evt", "a"))
        now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        pk = f"CASE#{case_id}"
        item = {
            "PK": pk,
            "SK": "CASE",
            "entityType": "CASE",
            "caseId": case_id,
            "caseType": case_type,
            "requesterId": actor,
            "status": "DRAFT",
            "checklistTemplateId": template.template_id,
            "checklistTemplateVersion": template.version,
            "submissionAttempt": 0,
            "documentRevision": 0,
            "version": 1,
            "createdAt": now,
            "updatedAt": now,
            "GSI1PK": f"REQUESTER#{actor}",
            "GSI1SK": f"CASE#{now}#{case_id}",
            "GSI2PK": "CASE_STATUS#DRAFT",
            "GSI2SK": f"UPDATED#{now}#{case_id}",
        }
        audit = {
            "PK": pk,
            "SK": f"AUDIT#{now}#{audit_id}",
            "entityType": "AUDIT",
            "auditId": audit_id,
            "caseId": case_id,
            "actorId": actor,
            "actorType": "USER",
            "action": "CASE_CREATED",
            "resourceType": "CASE",
            "resourceId": case_id,
            "previousState": None,
            "newState": "DRAFT",
            "timestamp": now,
            "correlationId": correlation_id,
        }
        detail = {
            "eventId": event_id,
            "eventVersion": "1.0",
            "occurredAt": now,
            "correlationId": correlation_id,
            "caseId": case_id,
            "actor": {"type": "USER", "id": actor},
            "data": {
                "caseType": case_type,
                "requesterId": actor,
                "checklistTemplateId": template.template_id,
                "checklistTemplateVersion": template.version,
            },
        }
        outbox = {
            "PK": pk,
            "SK": f"OUTBOX#{event_id}",
            "entityType": "OUTBOX",
            "eventId": event_id,
            "eventType": "CaseCreated",
            "eventVersion": "1.0",
            "source": "docflow.case",
            "correlationId": correlation_id,
            "caseId": case_id,
            "status": "PENDING",
            "detail": detail,
            "createdAt": now,
        }
        # No pending-outbox TTL: unpublished events must not disappear.
        self.client.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": self.table_name,
                        "Item": encode(row),
                        "ConditionExpression": "attribute_not_exists(PK)",
                    }
                }
                for row in (item, audit, outbox)
            ]
        )
        view = case_view(item)
        return {
            key: view[key]
            for key in ("caseId", "caseType", "status", "checklistTemplate", "createdAt")
        }

    def get(self, case_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"c_[A-Za-z0-9_-]{1,100}", case_id):
            raise ApiError(400, "CASE_ID_INVALID", "Invalid Case ID.")
        response = self.client.get_item(
            TableName=self.table_name,
            Key=encode({"PK": f"CASE#{case_id}", "SK": "CASE"}),
            ConsistentRead=True,
        )
        if "Item" not in response:
            raise ApiError(404, "CASE_NOT_FOUND", "Case not found.")
        return decode(response["Item"])

    def related(self, case_id: str, prefix: str) -> list[dict[str, Any]]:
        request: QueryInputTypeDef = {
            "TableName": self.table_name,
            "KeyConditionExpression": "PK = :pk AND begins_with(SK, :prefix)",
            "ExpressionAttributeValues": encode({":pk": f"CASE#{case_id}", ":prefix": prefix}),
            "ConsistentRead": True,
        }
        items: list[dict[str, Any]] = []
        while True:
            response = self.client.query(**request)
            items.extend(decode(row) for row in response.get("Items", []))
            if not response.get("LastEvaluatedKey"):
                return items
            request["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    def authorize(self, item: dict[str, Any], actor: str, groups: set[str]) -> None:
        if "admin" in groups or ("requester" in groups and item["requesterId"] == actor):
            return
        if "reviewer" in groups and any(
            task.get("reviewerId") == actor for task in self.related(item["caseId"], "TASK#")
        ):
            return
        raise ApiError(404, "CASE_NOT_FOUND", "Case not found.")

    def detail(self, item: dict[str, Any]) -> dict[str, Any]:
        documents = [
            public(
                row,
                "documentId caseId documentType fileName fileSize mimeType status "
                "validationStatus scanStatus documentVersion createdAt updatedAt",
            )
            for row in self.related(item["caseId"], "DOC#")
            if row.get("status") != "DELETED"
        ]
        tasks = self.related(item["caseId"], "TASK#")
        current = (
            max(tasks, key=lambda task: (int(task.get("attempt", 0)), task["SK"]))
            if tasks
            else None
        )
        review = (
            public(
                current, "taskId caseId attempt status reviewerId priority dueAt decision createdAt"
            )
            if current
            else None
        )
        requested = [
            public(row, "documentType reasonCode message")
            for row in item.get("requestedInformation", [])
            if isinstance(row, dict)
        ]
        return {
            "case": case_view(item),
            "documents": documents,
            "review": {"currentTask": review},
            "requestedInformation": requested,
        }

    def list_cases(
        self, actor: str, owner: str, status: str | None, limit: int, cursor: str | None
    ) -> dict[str, Any]:
        all_owners = owner == "all"
        index = "GSI2" if all_owners else "GSI1"
        pk = f"CASE_STATUS#{status}" if all_owners else f"REQUESTER#{actor}"
        prefix = "UPDATED#" if all_owners else "CASE#"
        scope = json.dumps([actor, owner, status])
        pattern = r"[0-9T:.Z-]{20,32}#c_[A-Za-z0-9_-]{1,100}"
        position = read_position(cursor, scope, pattern)
        request: QueryInputTypeDef = {
            "TableName": self.table_name,
            "IndexName": index,
            "KeyConditionExpression": f"{index}PK = :pk AND begins_with({index}SK, :prefix)",
            "ExpressionAttributeValues": encode({":pk": pk, ":prefix": prefix}),
            "ScanIndexForward": False,
            "Limit": limit,
        }
        if status and not all_owners:
            request["FilterExpression"] = "#state = :state"
            request["ExpressionAttributeNames"] = {"#state": "status"}
            request["ExpressionAttributeValues"] = encode(
                {":pk": pk, ":prefix": prefix, ":state": status}
            )
        if position:
            request["ExclusiveStartKey"] = encode(
                {
                    "PK": f"CASE#{position.split('#')[1]}",
                    "SK": "CASE",
                    f"{index}PK": pk,
                    f"{index}SK": prefix + position,
                }
            )
        response = self.client.query(**request)
        last = decode(response.get("LastEvaluatedKey", {}))
        return {
            "items": [case_view(decode(row)) for row in response.get("Items", [])],
            "nextCursor": position_token(last[f"{index}SK"][len(prefix) :], scope)
            if last
            else None,
        }

    def activity(self, case_id: str, actor: str, limit: int, cursor: str | None) -> dict[str, Any]:
        scope = json.dumps(["activity", actor, case_id])
        position = read_position(cursor, scope, r"[0-9T:.Z-]{20,32}#a_[A-Za-z0-9_-]{1,100}")
        request: QueryInputTypeDef = {
            "TableName": self.table_name,
            "ConsistentRead": True,
            "Limit": limit,
            "KeyConditionExpression": "PK = :pk AND begins_with(SK, :prefix)",
            "ExpressionAttributeValues": encode({":pk": f"CASE#{case_id}", ":prefix": "AUDIT#"}),
            "ScanIndexForward": False,
        }
        if position:
            request["ExclusiveStartKey"] = encode(
                {"PK": f"CASE#{case_id}", "SK": f"AUDIT#{position}"}
            )
        response = self.client.query(**request)
        last = decode(response.get("LastEvaluatedKey", {}))
        return {
            "items": [
                public(decode(row), "action actorType timestamp")
                for row in response.get("Items", [])
            ],
            "nextCursor": position_token(last["SK"][6:], scope) if last else None,
        }
