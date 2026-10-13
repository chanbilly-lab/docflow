"""Atomic, audited document soft deletion; never delete the S3 source."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from botocore.exceptions import ClientError

from common.cases.documents import revision_write
from common.cases.repository import ApiError, CaseRepository
from common.templates.repository import decode, encode

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef


def delete_document(
    repo: CaseRepository,
    case_id: str,
    document_id: str,
    actor: str,
    groups: set[str],
    correlation: str,
) -> None:
    case = repo.get(case_id)
    if "admin" not in groups and case["requesterId"] != actor:
        raise ApiError(404, "CASE_NOT_FOUND", "Case not found.")
    if case["status"] not in {"DRAFT", "NEEDS_INFORMATION"}:
        raise ApiError(409, "CASE_INVALID_STATE", "Case does not allow document deletion.")
    if not re.fullmatch(r"d_[A-Za-z0-9_-]{1,100}", document_id):
        raise ApiError(400, "DOCUMENT_ID_INVALID", "Invalid document ID.")
    key = {"PK": case["PK"], "SK": f"DOC#{document_id}"}
    found = repo.client.get_item(TableName=repo.table_name, Key=encode(key), ConsistentRead=True)
    if "Item" not in found:
        raise ApiError(404, "DOCUMENT_NOT_FOUND", "Document not found.")
    document = decode(found["Item"])
    if document["status"] not in {
        "REGISTERED",
        "UPLOADING",
        "UPLOADED",
        "VALIDATING",
        "VALID",
        "INVALID",
        "DELETED",
    }:
        raise ApiError(409, "DOCUMENT_INVALID_STATE", "Document does not allow deletion.")
    now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    checks: list[TransactWriteItemTypeDef] = [
        {
            "ConditionCheck": {
                "TableName": repo.table_name,
                "Key": encode({"PK": case["PK"], "SK": "CASE"}),
                "ConditionExpression": (
                    "#state = :state AND #version = :version AND requesterId = :owner"
                ),
                "ExpressionAttributeNames": {"#state": "status", "#version": "version"},
                "ExpressionAttributeValues": encode(
                    {
                        ":state": case["status"],
                        ":version": case["version"],
                        ":owner": case["requesterId"],
                    }
                ),
            }
        }
    ]
    # A retry still checks current ownership/Case state atomically, but creates no audit.
    if document["status"] == "DELETED":
        checks.append(
            {
                "ConditionCheck": {
                    "TableName": repo.table_name,
                    "Key": encode(key),
                    "ConditionExpression": "#state = :deleted",
                    "ExpressionAttributeNames": {"#state": "status"},
                    "ExpressionAttributeValues": encode({":deleted": "DELETED"}),
                }
            }
        )
    else:
        checks[0] = revision_write(repo.table_name, case, case["PK"])
        audit_id = f"a_{uuid4().hex}"
        checks.extend(
            [
                {
                    "Update": {
                        "TableName": repo.table_name,
                        "Key": encode(key),
                        "UpdateExpression": (
                            "SET #state = :deleted, updatedAt = :now, "
                            "deletedAt = :now, deletedBy = :actor"
                        ),
                        "ConditionExpression": (
                            "#state = :previous AND updatedAt = :updated "
                            "AND documentVersion = :version"
                        ),
                        "ExpressionAttributeNames": {"#state": "status"},
                        "ExpressionAttributeValues": encode(
                            {
                                ":deleted": "DELETED",
                                ":now": now,
                                ":actor": actor,
                                ":previous": document["status"],
                                ":updated": document["updatedAt"],
                                ":version": document["documentVersion"],
                            }
                        ),
                    }
                },
                {
                    "Put": {
                        "TableName": repo.table_name,
                        "ConditionExpression": "attribute_not_exists(PK)",
                        "Item": encode(
                            {
                                "PK": case["PK"],
                                "SK": f"AUDIT#{now}#{audit_id}",
                                "entityType": "AUDIT",
                                "auditId": audit_id,
                                "caseId": case_id,
                                "actorId": actor,
                                "actorType": "USER",
                                "action": "DOCUMENT_DELETED",
                                "resourceType": "DOCUMENT",
                                "resourceId": document_id,
                                "previousState": document["status"],
                                "newState": "DELETED",
                                "timestamp": now,
                                "correlationId": correlation,
                            }
                        ),
                    }
                },
            ]
        )
    try:
        repo.client.transact_write_items(TransactItems=checks)
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "TransactionCanceledException" and any(
            reason.get("Code") == "ConditionalCheckFailed"
            for reason in exc.response.get("CancellationReasons", [])
        ):
            raise ApiError(
                409, "DOCUMENT_CONFLICT", "Case or document changed; refresh and retry."
            ) from exc
        raise
