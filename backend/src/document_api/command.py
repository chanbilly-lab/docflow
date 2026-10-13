"""Metadata-only upload authorization; file bytes go directly to private S3."""

from __future__ import annotations

import base64
import json
import os
import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Protocol
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from case_api.api import principal
from common.cases.documents import revision_write
from common.cases.repository import ApiError, CaseRepository
from common.logging import observed
from common.templates.repository import (
    TemplateConflict,
    TemplateNotFound,
    TemplateRepository,
    encode,
)

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef

from document_api.deletion import delete_document

EXPIRY_SECONDS = 600
MIME_LIMITS = {"application/pdf": 15_000_000, "image/jpeg": 10_000_000, "image/png": 10_000_000}
ROUTE = "POST /api/v1/cases/{caseId}/documents/upload-url"
DELETE_ROUTE = "DELETE /api/v1/cases/{caseId}/documents/{documentId}"


class Presigner(Protocol):
    def generate_presigned_url(
        self, ClientMethod: str, Params: dict[str, Any], ExpiresIn: int, HttpMethod: str
    ) -> str: ...


def payload(event: dict[str, Any]) -> dict[str, Any]:
    try:
        body = event.get("body")
        if not isinstance(body, str) or len(body) > 8192:
            raise ValueError
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body, validate=True).decode()
        data = json.loads(body)
        if not isinstance(data, dict) or set(data) != {
            "documentType",
            "fileName",
            "fileSize",
            "mimeType",
        }:
            raise ValueError
        if not isinstance(data["documentType"], str) or not re.fullmatch(
            r"[A-Z0-9_]{1,100}", data["documentType"]
        ):
            raise ValueError
        name = data["fileName"]
        if (
            not isinstance(name, str)
            or not name.strip()
            or len(name) > 255
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
        ):
            raise ValueError
        size = data["fileSize"]
        if type(size) is not int or size < 1:
            raise ValueError
        mime = data["mimeType"]
        if not isinstance(mime, str) or mime not in MIME_LIMITS:
            raise ApiError(415, "MIME_TYPE_NOT_ALLOWED", "Use PDF, JPEG or PNG.")
        if size > MIME_LIMITS[mime]:
            raise ApiError(413, "FILE_TOO_LARGE", "File exceeds the MIME type size limit.")
        return data
    except (ValueError, TypeError, UnicodeError) as exc:
        raise ApiError(400, "UPLOAD_INPUT_INVALID", "Supply valid document metadata only.") from exc


def reserve(
    repo: CaseRepository,
    case_id: str,
    actor: str,
    groups: set[str],
    data: dict[str, Any],
    correlation: str,
) -> dict[str, Any]:
    case = repo.get(case_id)
    if "admin" not in groups and case["requesterId"] != actor:
        raise ApiError(404, "CASE_NOT_FOUND", "Case not found.")
    if case["status"] not in {"DRAFT", "NEEDS_INFORMATION"}:
        raise ApiError(409, "CASE_INVALID_STATE", "Case does not allow uploads.")
    template = TemplateRepository(repo.client, repo.table_name).get_version(
        case["checklistTemplateId"], int(case["checklistTemplateVersion"])
    )
    if data["documentType"] not in template.required_documents:
        raise ApiError(
            422, "DOCUMENT_TYPE_NOT_ALLOWED", "Document type is not in the Case template."
        )
    document_id, audit_id = f"d_{uuid4().hex}", f"a_{uuid4().hex}"
    now = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    pk = case["PK"]
    document = {
        "PK": pk,
        "SK": f"DOC#{document_id}",
        "entityType": "DOCUMENT",
        "caseId": case_id,
        "documentId": document_id,
        **data,
        "s3Key": f"cases/{case_id}/documents/{document_id}/v1/source",
        "status": "UPLOADING",
        "validationStatus": "PENDING",
        "scanStatus": "NOT_IMPLEMENTED",
        "documentVersion": 1,
        "correlationId": correlation,
        "createdAt": now,
        "updatedAt": now,
    }
    audit = {
        "PK": pk,
        "SK": f"AUDIT#{now}#{audit_id}",
        "entityType": "AUDIT",
        "auditId": audit_id,
        "caseId": case_id,
        "actorId": actor,
        "actorType": "USER",
        "action": "DOCUMENT_UPLOAD_REQUESTED",
        "resourceType": "DOCUMENT",
        "resourceId": document_id,
        "previousState": None,
        "newState": "UPLOADING",
        "timestamp": now,
        "correlationId": correlation,
    }
    writes: list[TransactWriteItemTypeDef] = [
        {
            "Put": {
                "TableName": repo.table_name,
                "Item": encode(row),
                "ConditionExpression": "attribute_not_exists(PK)",
            }
        }
        for row in (document, audit)
    ]
    try:
        repo.client.transact_write_items(
            TransactItems=[
                revision_write(repo.table_name, case, pk),
                *writes,
            ]
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "TransactionCanceledException" and any(
            reason.get("Code") == "ConditionalCheckFailed"
            for reason in exc.response.get("CancellationReasons", [])
        ):
            raise ApiError(
                409, "UPLOAD_CONFLICT", "Case changed; refresh before retrying."
            ) from exc
        raise
    return document


def handle(
    event: dict[str, Any],
    repository: CaseRepository | None = None,
    signer: Presigner | None = None,
    bucket: str | None = None,
) -> dict[str, Any]:
    supplied = next(
        (v for k, v in (event.get("headers") or {}).items() if k.lower() == "x-correlation-id"), ""
    )
    correlation = (
        supplied
        if isinstance(supplied, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", supplied)
        else f"corr_{uuid4().hex}"
    )
    try:
        actor, groups = principal(event)
        if event.get("routeKey") not in {ROUTE, DELETE_ROUTE}:
            raise ApiError(404, "ROUTE_NOT_FOUND", "Route not found.")
        if not groups & {"requester", "admin"}:
            raise ApiError(403, "FORBIDDEN", "Document modification is not permitted.")
        if event.get("queryStringParameters"):
            raise ApiError(400, "UPLOAD_INPUT_INVALID", "Query parameters are not supported.")
        repo = repository or CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"])
        if event.get("routeKey") == DELETE_ROUTE:
            if event.get("body") not in (None, ""):
                raise ApiError(400, "DELETE_INPUT_INVALID", "Delete does not accept a body.")
            paths = event.get("pathParameters") or {}
            delete_document(
                repo,
                paths.get("caseId", ""),
                paths.get("documentId", ""),
                actor,
                groups,
                correlation,
            )
            return {
                "statusCode": 204,
                "headers": {
                    "cache-control": "no-store",
                    "x-correlation-id": correlation,
                },
                "body": "",
            }
        data = payload(event)
        destination = bucket or os.environ["DOCUMENT_BUCKET"]
        s3 = signer or boto3.client(
            "s3",
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "virtual"},
                request_checksum_calculation="when_required",
            ),
        )
        document = reserve(
            repo,
            (event.get("pathParameters") or {}).get("caseId", ""),
            actor,
            groups,
            data,
            correlation,
        )
        # Persist first. If signing fails, leave auditable UPLOADING metadata, never a usable URL.
        expires = datetime.now(UTC) + timedelta(seconds=EXPIRY_SECONDS)
        url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": destination,
                "Key": document["s3Key"],
                "ContentType": data["mimeType"],
                "ContentLength": data["fileSize"],
                "IfNoneMatch": "*",
            },
            ExpiresIn=EXPIRY_SECONDS,
            HttpMethod="PUT",
        )
        result: dict[str, Any] = {
            "documentId": document["documentId"],
            "upload": {
                "method": "PUT",
                "url": url,
                "expiresAt": expires.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "requiredHeaders": {"Content-Type": data["mimeType"], "If-None-Match": "*"},
            },
        }
        status = 201
    except ApiError as exc:
        status, result = (
            exc.status,
            {"error": {"code": exc.code, "message": str(exc), "correlationId": correlation}},
        )
    except (ClientError, BotoCoreError, TemplateNotFound, TemplateConflict, KeyError):
        status, result = (
            503,
            {
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Service temporarily unavailable.",
                    "correlationId": correlation,
                }
            },
        )
    return {
        "statusCode": status,
        "headers": {
            "content-type": "application/json",
            "cache-control": "no-store",
            "x-correlation-id": correlation,
        },
        "body": json.dumps(result),
    }


@observed("document-command-handler")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    return handle(event)
