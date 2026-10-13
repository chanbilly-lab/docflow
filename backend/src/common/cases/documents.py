"""Case document revision fence, committed with each audited document mutation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from common.templates.repository import encode

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef


def revision_write(table: str, case: dict[str, Any] | None, pk: str) -> TransactWriteItemTypeDef:
    values: dict[str, Any] = {":one": 1}
    condition = "attribute_exists(PK)"
    names = {}
    if case is not None:
        condition += " AND #s = :state AND #v = :version AND requesterId = :owner"
        names = {"#s": "status", "#v": "version"}
        values.update(
            {
                ":state": case["status"],
                ":version": case["version"],
                ":owner": case["requesterId"],
            }
        )
    result: TransactWriteItemTypeDef = {
        "Update": {
            "TableName": table,
            "Key": encode({"PK": pk, "SK": "CASE"}),
            "UpdateExpression": "ADD documentRevision :one",
            "ConditionExpression": condition,
            "ExpressionAttributeValues": encode(values),
        }
    }
    if names:
        result["Update"]["ExpressionAttributeNames"] = names
    return result
