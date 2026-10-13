"""Upload contract, authorization, atomic reservation and real SDK signing tests."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import boto3
import pytest
from botocore.config import Config
from botocore.exceptions import ClientError

from common.cases.repository import CaseRepository
from common.templates.repository import TemplateRepository, decode, encode
from common.templates.seed import SUPPLIER_ONBOARDING as SEED
from document_api.command import MIME_LIMITS, ROUTE, handle, handler

META = {
    "documentType": "COMPANY_REGISTRATION",
    "fileName": "../../registration.pdf",
    "fileSize": 12,
    "mimeType": "application/pdf",
}


def incoming(
    case_id: str,
    actor: str = "alice",
    groups: list[str] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "routeKey": ROUTE,
        "headers": {"x-correlation-id": "upload-test"},
        "pathParameters": {"caseId": case_id},
        "body": json.dumps(META if data is None else data),
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": actor,
                        "token_use": "access",
                        "cognito:groups": ["requester"] if groups is None else groups,
                    }
                }
            }
        },
    }


def case(repo: CaseRepository) -> str:
    return str(repo.create(SEED.case_type, "alice", "test")["caseId"])


def rows(repo: CaseRepository, case_id: str) -> list[dict[str, Any]]:
    result = repo.client.query(
        TableName=repo.table_name,
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues=encode({":pk": f"CASE#{case_id}"}),
    )
    return [decode(row) for row in result["Items"]]


def sdk() -> Any:
    return boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
            request_checksum_calculation="when_required",
        ),
    )


def call(repo: CaseRepository, request: dict[str, Any]) -> dict[str, Any]:
    return handle(request, repo, sdk(), "docflow-test-documents")


def test_upload_reserves_metadata_before_signing_and_direct_s3_put(repo: CaseRepository) -> None:
    case_id = case(repo)
    s3 = sdk()
    s3.create_bucket(Bucket="docflow-test-documents")
    observed: list[str] = []
    original = s3.generate_presigned_url

    def sign(*args: Any, **kwargs: Any) -> str:
        stored = rows(repo, case_id)
        assert len([r for r in stored if r["entityType"] == "DOCUMENT"]) == 1
        assert len([r for r in stored if r.get("action") == "DOCUMENT_UPLOAD_REQUESTED"]) == 1
        observed.append("persisted")
        return str(original(*args, **kwargs))

    with patch.object(s3, "generate_presigned_url", side_effect=sign):
        response = handle(incoming(case_id), repo, s3, "docflow-test-documents")
    assert response["statusCode"] == 201 and observed == ["persisted"]
    body = json.loads(response["body"])
    from pathlib import Path

    from jsonschema import Draft202012Validator

    api = json.loads((Path(__file__).resolve().parents[3] / "docs/api/openapi.yaml").read_text())
    Draft202012Validator(
        {"$ref": "#/components/schemas/UploadResponse", "components": api["components"]}
    ).validate(body)
    assert response["headers"]["cache-control"] == "no-store"
    document = next(r for r in rows(repo, case_id) if r["entityType"] == "DOCUMENT")
    key = f"cases/{case_id}/documents/{body['documentId']}/v1/source"
    assert document["s3Key"] == key and document["fileName"] == META["fileName"]
    assert document["SK"] == f"DOC#{body['documentId']}"
    assert document["status"] == "UPLOADING"
    assert document["validationStatus"] == "PENDING"
    assert document["scanStatus"] == "NOT_IMPLEMENTED"
    url = urlparse(body["upload"]["url"])
    query = parse_qs(url.query)
    assert url.scheme == "https" and url.path == "/" + key
    assert query["X-Amz-Expires"] == ["600"]
    signed_at = datetime.strptime(query["X-Amz-Date"][0], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    advertised = datetime.fromisoformat(body["upload"]["expiresAt"].replace("Z", "+00:00"))
    assert abs((advertised - signed_at - timedelta(seconds=600)).total_seconds()) <= 2
    assert {"content-length", "content-type", "if-none-match", "host"} <= set(
        query["X-Amz-SignedHeaders"][0].split(";")
    )
    assert body["upload"]["requiredHeaders"] == {
        "Content-Type": "application/pdf",
        "If-None-Match": "*",
    }
    assert s3.list_objects_v2(Bucket="docflow-test-documents")["KeyCount"] == 0
    # A separate S3 operation carries bytes; no document content entered the API.
    s3.put_object(
        Bucket="docflow-test-documents",
        Key=key,
        Body=b"%PDF-example",
        ContentType="application/pdf",
        IfNoneMatch="*",
    )
    with pytest.raises(ClientError) as duplicate:
        s3.put_object(
            Bucket="docflow-test-documents", Key=key, Body=b"replacement", IfNoneMatch="*"
        )
    assert duplicate.value.response["Error"]["Code"] == "PreconditionFailed"
    assert s3.get_object(Bucket="docflow-test-documents", Key=key)["Body"].read() == b"%PDF-example"
    assert "X-Amz-" not in json.dumps(rows(repo, case_id), default=int)


@pytest.mark.parametrize(
    "actor,groups,expected",
    [
        ("alice", ["requester"], 201),
        ("bob", ["requester"], 404),
        ("alice", ["reviewer"], 403),
        ("bob", ["admin"], 201),
        ("alice", ["requester", "reviewer"], 201),
        ("alice", [], 403),
    ],
)
def test_upload_roles(repo: CaseRepository, actor: str, groups: list[str], expected: int) -> None:
    case_id = case(repo)
    before = rows(repo, case_id)
    response = call(repo, incoming(case_id, actor, groups))
    assert response["statusCode"] == expected
    if expected != 201:
        assert rows(repo, case_id) == before
        assert "upload" not in json.loads(response["body"])
    else:
        audit = next(
            r for r in rows(repo, case_id) if r.get("action") == "DOCUMENT_UPLOAD_REQUESTED"
        )
        assert audit["actorId"] == actor


@pytest.mark.parametrize(
    "status,expected",
    [
        ("DRAFT", 201),
        ("NEEDS_INFORMATION", 201),
        ("SUBMITTED", 409),
        ("PROCESSING", 409),
        ("REVIEW_PENDING", 409),
        ("IN_REVIEW", 409),
        ("APPROVED", 409),
        ("REJECTED", 409),
        ("WORKFLOW_FAILED", 409),
    ],
)
def test_upload_state_gate(repo: CaseRepository, status: str, expected: int) -> None:
    case_id = case(repo)
    row = repo.get(case_id)
    row["status"] = status
    repo.client.put_item(TableName=repo.table_name, Item=encode(row))
    before = rows(repo, case_id)
    s3 = sdk()
    with patch.object(s3, "generate_presigned_url", wraps=s3.generate_presigned_url) as sign:
        response = handle(incoming(case_id), repo, s3, "bucket")
        assert response["statusCode"] == expected
        if expected != 201:
            sign.assert_not_called()
            assert rows(repo, case_id) == before
        else:
            sign.assert_called_once()


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("documentType", "UNKNOWN", 422),
        ("fileSize", 0, 400),
        ("fileSize", True, 400),
        ("fileSize", 1.5, 400),
        ("fileSize", 15_000_001, 413),
        ("mimeType", "text/html", 415),
        ("fileName", "", 400),
        ("fileName", "a" * 256, 400),
        ("fileName", "bad\nname", 400),
        ("fileName", " " * 256 + "a", 400),
        ("s3Key", "victim", 400),
        ("requesterId", "bob", 400),
        ("bytes", "file-content", 400),
        ("documentId", "chosen", 400),
    ],
)
def test_invalid_metadata_has_no_effect(
    repo: CaseRepository, field: str, value: Any, expected: int
) -> None:
    case_id = case(repo)
    before = rows(repo, case_id)
    response = call(repo, incoming(case_id, data={**META, field: value}))
    assert response["statusCode"] == expected
    assert rows(repo, case_id) == before


@pytest.mark.parametrize("mime", list(MIME_LIMITS))
def test_size_boundary_and_mime_binding(repo: CaseRepository, mime: str) -> None:
    case_id = case(repo)
    data = {**META, "mimeType": mime, "fileSize": MIME_LIMITS[mime]}
    response = call(repo, incoming(case_id, data=data))
    assert response["statusCode"] == 201
    assert json.loads(response["body"])["upload"]["requiredHeaders"]["Content-Type"] == mime
    assert (
        call(repo, incoming(case_id, data={**data, "fileSize": MIME_LIMITS[mime] + 1}))[
            "statusCode"
        ]
        == 413
    )


def test_bound_historical_template_controls_document_types(repo: CaseRepository) -> None:
    case_id = case(repo)
    TemplateRepository(repo.client, repo.table_name).publish(
        replace(SEED, version=2, required_documents=(*SEED.required_documents, "EXTRA")),
        actor_id="seed",
    )
    assert (
        call(repo, incoming(case_id, data={**META, "documentType": "EXTRA"}))["statusCode"] == 422
    )
    new = case(repo)
    assert call(repo, incoming(new, data={**META, "documentType": "EXTRA"}))["statusCode"] == 201


@pytest.mark.parametrize("change", ["status", "owner", "version"])
def test_case_change_race_rolls_back_document_and_audit(repo: CaseRepository, change: str) -> None:
    case_id = case(repo)
    transact = repo.client.transact_write_items

    def race(**kwargs: Any) -> Any:
        item = repo.get(case_id)
        if change == "status":
            item["status"] = "SUBMITTED"
        elif change == "owner":
            item["requesterId"] = "bob"
        else:
            item["version"] = 2
        repo.client.put_item(TableName=repo.table_name, Item=encode(item))
        return transact(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        response = call(repo, incoming(case_id))
    assert response["statusCode"] == 409
    assert json.loads(response["body"])["error"]["code"] == "UPLOAD_CONFLICT"
    assert len(rows(repo, case_id)) == 3


def test_failed_signing_leaves_audited_reservation_without_url(repo: CaseRepository) -> None:
    case_id = case(repo)
    signer = sdk()
    with patch.object(
        signer,
        "generate_presigned_url",
        side_effect=ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "private-detail"}}, "PutObject"
        ),
    ):
        response = handle(incoming(case_id), repo, signer, "bucket")
    assert response["statusCode"] == 503
    assert "private-detail" not in response["body"] and "url" not in response["body"]
    assert len(rows(repo, case_id)) == 5


def test_entrypoint_and_missing_auth(repo: CaseRepository) -> None:
    case_id = case(repo)
    s3 = sdk()

    def client(service: str, **kwargs: Any) -> Any:
        return repo.client if service == "dynamodb" else s3

    with (
        patch("document_api.command.boto3.client", side_effect=client),
        patch.dict("os.environ", {"TABLE_NAME": repo.table_name, "DOCUMENT_BUCKET": "bucket"}),
    ):
        assert handler(incoming(case_id), None)["statusCode"] == 201
    forged = incoming(case_id)
    del forged["requestContext"]
    forged["headers"]["authorization"] = "Bearer fabricated"
    with patch("document_api.command.boto3.client") as factory:
        assert handler(forged, None)["statusCode"] == 401
        factory.assert_not_called()


# TASK-008: persisted metadata lifecycle and audited, concurrency-safe soft deletion.
def deletion(
    case_id: str, document_id: str, actor: str = "alice", groups: list[str] | None = None
) -> dict[str, Any]:
    event = incoming(case_id, actor, groups)
    event["routeKey"] = "DELETE /api/v1/cases/{caseId}/documents/{documentId}"
    event["pathParameters"]["documentId"] = document_id
    del event["body"]
    return event


def uploaded_metadata(repo: CaseRepository) -> tuple[str, str]:
    case_id = case(repo)
    response = call(repo, incoming(case_id))
    assert response["statusCode"] == 201
    return case_id, str(json.loads(response["body"])["documentId"])


def document_row(repo: CaseRepository, case_id: str, document_id: str) -> dict[str, Any]:
    return next(r for r in rows(repo, case_id) if r.get("documentId") == document_id)


def delete_audits(repo: CaseRepository, case_id: str) -> list[dict[str, Any]]:
    return [r for r in rows(repo, case_id) if r.get("action") == "DOCUMENT_DELETED"]


def test_soft_delete_retains_history_hides_document_and_preserves_s3(repo: CaseRepository) -> None:
    case_id, document_id = uploaded_metadata(repo)
    before = document_row(repo, case_id, document_id)
    s3 = sdk()
    s3.create_bucket(Bucket="docflow-test-documents")
    s3.put_object(
        Bucket="docflow-test-documents", Key=before["s3Key"], Body=b"original", IfNoneMatch="*"
    )
    # The real delete entry point requires no bucket, signing client or object permissions.
    with (
        patch("document_api.command.boto3.client", return_value=repo.client) as factory,
        patch.dict("os.environ", {"TABLE_NAME": repo.table_name}),
    ):
        response = handler(deletion(case_id, document_id), None)
        factory.assert_called_once_with("dynamodb")
    assert response["statusCode"] == 204 and response["body"] == ""
    assert response["headers"]["cache-control"] == "no-store"
    after = document_row(repo, case_id, document_id)
    assert after["status"] == "DELETED"
    assert after["deletedBy"] == "alice" and after["deletedAt"] == after["updatedAt"]
    for field in (
        "fileName",
        "fileSize",
        "mimeType",
        "s3Key",
        "documentType",
        "documentVersion",
        "createdAt",
        "validationStatus",
        "scanStatus",
    ):
        assert after[field] == before[field]
    assert repo.detail(repo.get(case_id))["documents"] == []
    assert (
        s3.get_object(Bucket="docflow-test-documents", Key=before["s3Key"])["Body"].read()
        == b"original"
    )
    audit = delete_audits(repo, case_id)
    assert len(audit) == 1 and audit[0]["previousState"] == "UPLOADING"
    assert audit[0]["newState"] == "DELETED" and audit[0]["resourceId"] == document_id
    assert audit[0]["actorId"] == "alice" and audit[0]["correlationId"] == "upload-test"
    assert call(repo, deletion(case_id, document_id))["statusCode"] == 204
    assert document_row(repo, case_id, document_id) == after
    assert len(delete_audits(repo, case_id)) == 1
    replacement = json.loads(call(repo, incoming(case_id))["body"])["documentId"]
    assert replacement != document_id
    assert document_row(repo, case_id, replacement)["s3Key"] != before["s3Key"]
    assert [d["documentId"] for d in repo.detail(repo.get(case_id))["documents"]] == [replacement]
    assert document_row(repo, case_id, document_id) == after


@pytest.mark.parametrize(
    "actor,groups,expected",
    [
        ("alice", ["requester"], 204),
        ("other", ["requester"], 404),
        ("alice", ["reviewer"], 403),
        ("admin", ["admin"], 204),
        ("alice", [], 403),
    ],
)
def test_delete_authorization(
    repo: CaseRepository, actor: str, groups: list[str], expected: int
) -> None:
    case_id, document_id = uploaded_metadata(repo)
    before = rows(repo, case_id)
    response = call(repo, deletion(case_id, document_id, actor, groups))
    assert response["statusCode"] == expected
    if expected == 204:
        assert delete_audits(repo, case_id)[0]["actorId"] == actor
    else:
        assert rows(repo, case_id) == before


@pytest.mark.parametrize(
    "state",
    [
        "SUBMITTED",
        "PROCESSING",
        "REVIEW_PENDING",
        "IN_REVIEW",
        "APPROVED",
        "REJECTED",
        "WORKFLOW_FAILED",
    ],
)
def test_immutable_case_rejects_delete_even_for_admin(repo: CaseRepository, state: str) -> None:
    case_id, document_id = uploaded_metadata(repo)
    row = repo.get(case_id)
    row["status"] = state
    repo.client.put_item(TableName=repo.table_name, Item=encode(row))
    before = rows(repo, case_id)
    for actor, groups in [("alice", ["requester"]), ("admin", ["admin"])]:
        response = call(repo, deletion(case_id, document_id, actor, groups))
        assert response["statusCode"] == 409
        assert json.loads(response["body"])["error"]["code"] == "CASE_INVALID_STATE"
    assert rows(repo, case_id) == before


@pytest.mark.parametrize(
    "state", ["REGISTERED", "UPLOADING", "UPLOADED", "VALIDATING", "VALID", "INVALID"]
)
def test_needs_information_can_delete_existing_metadata(repo: CaseRepository, state: str) -> None:
    case_id, document_id = uploaded_metadata(repo)
    c = repo.get(case_id)
    c["status"] = "NEEDS_INFORMATION"
    repo.client.put_item(TableName=repo.table_name, Item=encode(c))
    doc = document_row(repo, case_id, document_id)
    doc["status"] = state
    repo.client.put_item(TableName=repo.table_name, Item=encode(doc))
    assert call(repo, deletion(case_id, document_id))["statusCode"] == 204
    assert delete_audits(repo, case_id)[0]["previousState"] == state


@pytest.mark.parametrize(
    "change", ["case_status", "owner", "case_version", "doc_status", "doc_version", "doc_updated"]
)
def test_delete_races_leave_no_partial_audit(repo: CaseRepository, change: str) -> None:
    case_id, document_id = uploaded_metadata(repo)
    original = repo.client.transact_write_items

    def race(**kwargs: Any) -> Any:
        if change.startswith("doc_"):
            row = document_row(repo, case_id, document_id)
            field, value = {
                "doc_status": ("status", "VALIDATING"),
                "doc_version": ("documentVersion", 2),
                "doc_updated": ("updatedAt", "2026-09-16T23:59:59Z"),
            }[change]
        else:
            row = repo.get(case_id)
            field, value = {
                "case_status": ("status", "SUBMITTED"),
                "owner": ("requesterId", "other"),
                "case_version": ("version", 2),
            }[change]
        row[field] = value
        repo.client.put_item(TableName=repo.table_name, Item=encode(row))
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        response = call(repo, deletion(case_id, document_id))
    assert response["statusCode"] == 409
    assert json.loads(response["body"])["error"]["code"] == "DOCUMENT_CONFLICT"
    assert document_row(repo, case_id, document_id)["status"] != "DELETED"
    assert not delete_audits(repo, case_id)


def test_concurrent_deletes_have_one_audit_and_retry_is_noop(repo: CaseRepository) -> None:
    case_id, document_id = uploaded_metadata(repo)
    original = repo.client.transact_write_items

    def race(**kwargs: Any) -> Any:
        with patch.object(repo.client, "transact_write_items", side_effect=original):
            assert call(repo, deletion(case_id, document_id))["statusCode"] == 204
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        assert call(repo, deletion(case_id, document_id))["statusCode"] == 409
    assert call(repo, deletion(case_id, document_id))["statusCode"] == 204
    assert len(delete_audits(repo, case_id)) == 1
    row = repo.get(case_id)
    row["status"] = "SUBMITTED"
    repo.client.put_item(TableName=repo.table_name, Item=encode(row))
    assert call(repo, deletion(case_id, document_id))["statusCode"] == 409


def test_document_id_is_scoped_to_case_and_invalid_delete_input_is_rejected(
    repo: CaseRepository,
) -> None:
    case_id, document_id = uploaded_metadata(repo)
    other = case(repo)
    before = rows(repo, case_id)
    for wrong_id, expected in [("d_missing", 404), ("../source", 400)]:
        assert call(repo, deletion(case_id, wrong_id))["statusCode"] == expected
    assert call(repo, deletion(other, document_id))["statusCode"] == 404
    event = deletion(case_id, document_id)
    event["body"] = json.dumps({"force": True})
    assert call(repo, event)["statusCode"] == 400
    event = deletion(case_id, document_id)
    event["queryStringParameters"] = {"force": "true"}
    assert call(repo, event)["statusCode"] == 400
    assert rows(repo, case_id) == before


def test_deleted_document_remains_deleted_after_late_upload(repo: CaseRepository) -> None:
    case_id, document_id = uploaded_metadata(repo)
    doc = document_row(repo, case_id, document_id)
    assert call(repo, deletion(case_id, document_id))["statusCode"] == 204
    s3 = sdk()
    s3.create_bucket(Bucket="docflow-test-documents")
    s3.put_object(Bucket="docflow-test-documents", Key=doc["s3Key"], Body=b"late", IfNoneMatch="*")
    assert document_row(repo, case_id, document_id)["status"] == "DELETED"
    assert repo.detail(repo.get(case_id))["documents"] == []
    # No event processor exists yet; TASK-010 must preserve this terminal tombstone.
