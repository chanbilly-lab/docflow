"""SQS document validation with leased claims and atomic business effects."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any
from uuid import uuid4

import boto3

from common.cases.documents import revision_write
from common.cases.repository import CaseRepository
from common.logging import emit, observed
from common.templates.repository import decode, encode
from document_api.command import MIME_LIMITS

CONSUMER = "document-processor"
LEASE_SECONDS = 120
RETENTION_SECONDS = 30 * 86400
EXTENSIONS = {"application/pdf": {".pdf"}, "image/jpeg": {".jpg", ".jpeg"}, "image/png": {".png"}}


class RetryProcessing(Exception):
    """A record must remain in SQS for retry."""


def parse(body: str, bucket: str) -> dict[str, Any]:
    event = json.loads(body)
    if event["source"] != "aws.s3" or event["detail-type"] != "Object Created":
        raise ValueError("Unexpected event")
    detail = event["detail"]
    obj = detail["object"]
    key = obj["key"]
    match = re.fullmatch(
        r"cases/(c_[A-Za-z0-9_-]{1,100})/documents/(d_[A-Za-z0-9_-]{1,100})/v([1-9][0-9]*)/source",
        key,
    )
    etag = obj["etag"]
    version = obj.get("version-id")
    if (
        detail["bucket"]["name"] != bucket
        or not match
        or not isinstance(etag, str)
        or not etag
        or len(etag) > 128
        or (version is not None and (not isinstance(version, str) or not version))
        or type(obj["size"]) is not int
        or obj["size"] < 0
    ):
        raise ValueError("Invalid source identity")
    identity = hashlib.sha256(
        json.dumps([bucket, key, version or etag], separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "bucket": bucket,
        "key": key,
        "etag": etag,
        "version": version,
        "size": obj["size"],
        "caseId": match[1],
        "documentId": match[2],
        "documentVersion": int(match[3]),
        "identity": identity,
    }


def timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


class Processor:
    def __init__(self, repo: CaseRepository, s3: Any, bucket: str):
        self.repo, self.s3, self.bucket = repo, s3, bucket

    def read(self, key: dict[str, str]) -> dict[str, Any]:
        found = self.repo.client.get_item(
            TableName=self.repo.table_name, Key=encode(key), ConsistentRead=True
        )
        return decode(found["Item"]) if "Item" in found else {}

    def put(
        self,
        row: dict[str, Any],
        condition: str = "attribute_not_exists(PK)",
        values: dict[str, Any] | None = None,
    ) -> Any:
        result: dict[str, Any] = {
            "TableName": self.repo.table_name,
            "Item": encode(row),
            "ConditionExpression": condition,
        }
        if values:
            result["ExpressionAttributeValues"] = encode(values)
        return {"Put": result}

    def audit(self, doc: dict[str, Any], state: str, identity: str, now: str) -> dict[str, Any]:
        audit_id = "a_" + uuid4().hex
        return {
            "PK": doc["PK"],
            "SK": f"AUDIT#{now}#{audit_id}",
            "entityType": "AUDIT",
            "auditId": audit_id,
            "caseId": doc["caseId"],
            "actorType": "SYSTEM",
            "actorId": CONSUMER,
            "action": "DOCUMENT_" + state,
            "resourceType": "DOCUMENT",
            "resourceId": doc["documentId"],
            "previousState": doc["status"],
            "newState": state,
            "timestamp": now,
            "correlationId": doc.get("correlationId", "corr_" + identity),
        }

    def transition(
        self,
        doc: dict[str, Any],
        state: str,
        identity: str,
        extras: dict[str, Any],
        writes: list[Any],
    ) -> dict[str, Any]:
        now = timestamp()
        updated = {**doc, **extras, "status": state, "updatedAt": now}
        change = self.put(
            updated,
            "updatedAt = :updated AND documentVersion = :version AND #s = :previous",
            {
                ":updated": doc["updatedAt"],
                ":version": doc["documentVersion"],
                ":previous": doc["status"],
            },
        )
        change["Put"]["ExpressionAttributeNames"] = {"#s": "status"}
        self.repo.client.transact_write_items(
            TransactItems=[
                revision_write(self.repo.table_name, None, doc["PK"]),
                change,
                self.put(self.audit(doc, state, identity, now)),
                *writes,
            ]
        )
        return updated

    def validate(
        self, doc: dict[str, Any], source: dict[str, Any], head: dict[str, Any]
    ) -> tuple[list[str], str | None]:
        errors = []
        mime = str(doc.get("mimeType", ""))
        size = head["ContentLength"]
        if mime not in MIME_LIMITS or head.get("ContentType") != mime:
            errors.append("MIME_MISMATCH")
        if size != doc.get("fileSize") or size < 1 or size > MIME_LIMITS.get(mime, 0):
            errors.append("SIZE_INVALID")
        if PurePosixPath(doc.get("fileName", "")).suffix.lower() not in EXTENSIONS.get(mime, set()):
            errors.append("EXTENSION_MISMATCH")
        if not doc.get("documentType") or not doc.get("fileName"):
            errors.append("METADATA_MISSING")
        if errors:
            return errors, None
        args = self.object_args(source)
        result = self.s3.get_object(**args, IfMatch='"' + source["etag"] + '"')
        stream = result["Body"]
        digest, length, prefix = hashlib.sha256(), 0, b""
        try:
            while chunk := stream.read(65536):
                length += len(chunk)
                if length > size or length > MIME_LIMITS[mime]:
                    return ["SIZE_INVALID"], None
                prefix = (prefix + chunk)[:8]
                digest.update(chunk)
        finally:
            stream.close()
        if length != size:
            raise RetryProcessing("Incomplete source read")
        signatures = {
            "application/pdf": b"%PDF-",
            "image/jpeg": b"\xff\xd8\xff",
            "image/png": b"\x89PNG\r\n\x1a\n",
        }
        if not prefix.startswith(signatures[mime]):
            errors.append("CONTENT_SIGNATURE_MISMATCH")
        return errors, digest.hexdigest()

    def object_args(self, source: dict[str, Any]) -> dict[str, Any]:
        args = {"Bucket": self.bucket, "Key": source["key"]}
        if source["version"]:
            args["VersionId"] = source["version"]
        return args

    def process(self, body: str) -> None:
        source = parse(body, self.bucket)
        identity = source["identity"]
        key = {"PK": "IDEMPOTENCY#" + CONSUMER, "SK": "EVENT#" + identity}
        prior = self.read(key)
        if prior.get("status") == "COMPLETED":
            return
        now = int(time.time())
        owner = uuid4().hex
        claim = {
            **key,
            "entityType": "IDEMPOTENCY",
            "status": "IN_PROGRESS",
            "owner": owner,
            "leaseUntil": now + LEASE_SECONDS,
        }
        if prior and prior.get("leaseUntil", now + 1) >= now:
            raise RetryProcessing("Processing lease busy")
        condition = (
            "attribute_not_exists(PK)" if not prior else "leaseUntil < :now AND #s = :progress"
        )
        write = self.put(
            claim, condition, None if not prior else {":now": now, ":progress": "IN_PROGRESS"}
        )
        if prior:
            write["Put"]["ExpressionAttributeNames"] = {"#s": "status"}
        self.repo.client.transact_write_items(TransactItems=[write])
        doc_key = {"PK": "CASE#" + source["caseId"], "SK": "DOC#" + source["documentId"]}
        doc = self.read(doc_key)
        if not doc:
            raise RetryProcessing("Missing reservation")
        completion = {
            **key,
            "entityType": "IDEMPOTENCY",
            "status": "COMPLETED",
            "processedAt": timestamp(),
            "expiresAtEpoch": now + RETENTION_SECONDS,
        }
        finish = self.put(
            completion,
            "#owner = :owner AND leaseUntil > :now",
            {":owner": owner, ":now": int(time.time())},
        )
        finish["Put"]["ExpressionAttributeNames"] = {"#owner": "owner"}
        if doc["status"] == "DELETED" or (
            doc["status"] in {"VALID", "INVALID"} and doc.get("processingIdentity") == identity
        ):
            self.repo.client.transact_write_items(TransactItems=[finish])
            return
        if (
            doc.get("s3Key") != source["key"]
            or doc.get("documentVersion") != source["documentVersion"]
            or doc.get("caseId") != source["caseId"]
            or doc.get("documentId") != source["documentId"]
        ):
            raise RetryProcessing("Reservation identity mismatch")
        if doc["status"] not in {"UPLOADING", "UPLOADED", "VALIDATING"}:
            raise RetryProcessing("Unexpected document state")
        if doc.get("processingIdentity", identity) != identity:
            raise RetryProcessing("Conflicting source identity")
        head = self.s3.head_object(**self.object_args(source), IfMatch='"' + source["etag"] + '"')
        if head["ETag"].strip('"') != source["etag"] or head["ContentLength"] != source["size"]:
            raise RetryProcessing("Source identity changed")
        # Every persisted transition is audited; retries resume without repeating transitions.
        for state in ("UPLOADED", "VALIDATING"):
            if doc["status"] == ("UPLOADING" if state == "UPLOADED" else "UPLOADED"):
                guard = {
                    "ConditionCheck": {
                        "TableName": self.repo.table_name,
                        "Key": encode(key),
                        "ConditionExpression": "#owner = :owner AND leaseUntil > :now",
                        "ExpressionAttributeNames": {"#owner": "owner"},
                        "ExpressionAttributeValues": encode(
                            {":owner": owner, ":now": int(time.time())}
                        ),
                    }
                }
                doc = self.transition(
                    doc, state, identity, {"processingIdentity": identity}, [guard]
                )
        errors, checksum = self.validate(doc, source, head)
        state = "INVALID" if errors else "VALID"
        event_id = "evt_" + identity
        at = timestamp()
        data = {
            "documentId": doc["documentId"],
            "documentVersion": int(doc["documentVersion"]),
            "validationStatus": state,
            "validationErrors": errors,
            "sha256": checksum,
        }
        detail = {
            "eventId": event_id,
            "eventVersion": "1.0",
            "occurredAt": at,
            "correlationId": doc.get("correlationId", "corr_" + identity),
            "caseId": doc["caseId"],
            "actor": {"type": "SYSTEM", "id": CONSUMER},
            "data": data,
        }
        outbox = {
            "PK": doc["PK"],
            "SK": "OUTBOX#" + event_id,
            "entityType": "OUTBOX",
            "eventId": event_id,
            "eventType": "DocumentValidated" if not errors else "DocumentValidationFailed",
            "eventVersion": "1.0",
            "source": "docflow.document",
            "status": "PENDING",
            "correlationId": detail["correlationId"],
            "caseId": doc["caseId"],
            "detail": detail,
            "createdAt": at,
        }
        # Recompute lease time immediately before the final transaction.
        finish["Put"]["ExpressionAttributeValues"] = encode(
            {":owner": owner, ":now": int(time.time())}
        )
        self.transition(
            doc,
            state,
            identity,
            {**data, "processingIdentity": identity},
            [self.put(outbox), finish],
        )

        emit("document-processor", "DocumentCompleted", fields=detail)


def handle(event: dict[str, Any], processor: Processor) -> dict[str, Any]:
    failures = []
    for record in event["Records"]:
        identifier = record["messageId"]
        try:
            processor.process(record["body"])
        except Exception:
            # Never include event bodies, filenames, S3 keys or exception text in logs.
            emit(
                "document-processor",
                "DocumentRetry",
                level="ERROR",
                metrics={"DocumentProcessingFailures": 1},
            )
            failures.append({"itemIdentifier": identifier})
    return {"batchItemFailures": failures}


@observed("document-processor")
def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    return handle(
        event,
        Processor(
            CaseRepository(boto3.client("dynamodb"), os.environ["TABLE_NAME"]),
            boto3.client("s3"),
            os.environ["DOCUMENT_BUCKET"],
        ),
    )
