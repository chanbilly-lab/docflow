"""Submission acceptance and deterministic transaction interleavings against Moto."""

import base64
import json
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from jsonschema import Draft202012Validator

from case_api.api import handle
from common.cases.repository import ApiError, CaseRepository
from common.cases.submission import submit
from common.templates.repository import TemplateRepository, decode, encode
from common.templates.seed import SUPPLIER_ONBOARDING as SEED
from document_api.command import reserve
from document_api.deletion import delete_document

ROOT = Path(__file__).resolve().parents[3]
KEY = "b1fdd8e0-3e47-4c57-8af8-125d980e0090"


def ready(repo: CaseRepository) -> str:
    case_id = repo.create(SEED.case_type, "alice", "test")["caseId"]
    for kind in SEED.required_documents:
        doc = reservation(repo, case_id, kind)
        # Explicit validated fixture; real processor-to-submission coverage is in domain tests.
        doc.update(status="VALID", validationStatus="VALID")
        repo.client.put_item(TableName=repo.table_name, Item=encode(doc))
    return str(case_id)


def reservation(
    repo: CaseRepository, case_id: str, kind: str = "COMPANY_REGISTRATION"
) -> dict[str, Any]:
    return reserve(
        repo,
        case_id,
        "alice",
        {"requester"},
        {
            "documentType": kind,
            "fileName": "fixture.pdf",
            "fileSize": 10,
            "mimeType": "application/pdf",
        },
        "test",
    )


def send(
    repo: CaseRepository, case_id: str, op: str = "submit", **changes: Any
) -> tuple[int, dict[str, Any]]:
    event = {
        "routeKey": "POST /api/v1/cases/{caseId}/" + op,
        "pathParameters": {"caseId": case_id},
        "body": "{}",
        "headers": {"Idempotency-Key": KEY, "x-correlation-id": "test"},
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "alice",
                        "cognito:groups": ["requester"],
                        "token_use": "access",
                    }
                }
            }
        },
        **changes,
    }
    result = handle(event, "command", repo)
    assert result["headers"]["cache-control"] == "no-store"
    return result["statusCode"], json.loads(result["body"])


def rows(repo: CaseRepository) -> list[dict[str, Any]]:
    return [decode(r) for r in repo.client.scan(TableName=repo.table_name)["Items"]]


def put_case(repo: CaseRepository, case_id: str, **changes: Any) -> None:
    repo.client.put_item(TableName=repo.table_name, Item=encode({**repo.get(case_id), **changes}))


def test_success_replay_history_and_contract(repo: CaseRepository) -> None:
    case_id = ready(repo)
    status, response = send(repo, case_id)
    assert status == 202
    api = json.loads((ROOT / "docs/api/openapi.yaml").read_text())
    Draft202012Validator(api["components"]["schemas"]["SubmissionResponse"]).validate(response)
    assert response == {
        "caseId": case_id,
        "status": "SUBMITTED",
        "attempt": 1,
        "workflowExecutionId": None,
    }
    stored = repo.get(case_id)
    assert stored["version"] == 2 and stored["documentRevision"] == 4
    assert stored["GSI2PK"] == "CASE_STATUS#SUBMITTED"
    assert stored["workflowStartStatus"] == "PENDING"
    assert len(stored["workflowExecutionName"]) <= 80
    assert stored["workflowInput"]["attempt"] == 1
    before = rows(repo)
    assert send(repo, case_id) == (202, response)
    assert rows(repo) == before
    put_case(repo, case_id, status="NEEDS_INFORMATION")
    assert send(repo, case_id) == (202, response)
    assert send(repo, case_id, "resubmit")[1]["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    code, second = send(repo, case_id, "resubmit", headers={"Idempotency-Key": str(uuid4())})
    assert code == 202 and second["attempt"] == 2
    assert repo.get(case_id)["workflowExecutionName"] != stored["workflowExecutionName"]
    assert (
        len([r for r in rows(repo) if r.get("action") in {"CASE_SUBMITTED", "CASE_RESUBMITTED"}])
        == 2
    )
    assert {r["eventType"] for r in rows(repo) if r.get("source") == "docflow.case"} == {
        "CaseCreated",
        "CaseSubmitted",
        "CaseResubmitted",
    }
    assert all(
        "expiresAtEpoch" not in r
        for r in rows(repo)
        if r.get("entityType") in {"IDEMPOTENCY", "OUTBOX"}
    )


@pytest.mark.parametrize(
    "state,validation,code",
    [
        ("DELETED", "VALID", "REQUIRED_DOCUMENT_MISSING"),
        ("UPLOADING", "PENDING", "DOCUMENT_NOT_READY"),
        ("UPLOADED", "PENDING", "DOCUMENT_NOT_READY"),
        ("VALIDATING", "PENDING", "DOCUMENT_NOT_READY"),
        ("REGISTERED", "PENDING", "DOCUMENT_NOT_READY"),
        ("INVALID", "INVALID", "DOCUMENT_INVALID"),
        ("VALID", "INVALID", "DOCUMENT_INVALID"),
        ("VALID", "PENDING", "DOCUMENT_NOT_READY"),
    ],
)
def test_document_gates_no_side_effects(
    repo: CaseRepository, state: str, validation: str, code: str
) -> None:
    case_id = ready(repo)
    doc = repo.related(case_id, "DOC#")[0]
    doc.update(status=state, validationStatus=validation)
    repo.client.put_item(TableName=repo.table_name, Item=encode(doc))
    before = rows(repo)
    status, response = send(repo, case_id)
    assert status == 422 and response["error"]["code"] == code
    assert rows(repo) == before


def test_missing_empty_and_duplicate_invalid(repo: CaseRepository) -> None:
    case_id = repo.create(SEED.case_type, "alice", "test")["caseId"]
    assert send(repo, case_id)[1]["error"]["code"] == "REQUIRED_DOCUMENT_MISSING"
    case_id = ready(repo)
    doc = reservation(repo, case_id)
    assert send(repo, case_id)[1]["error"]["code"] == "DOCUMENT_NOT_READY"
    delete_document(repo, case_id, doc["documentId"], "alice", {"requester"}, "test")
    assert send(repo, case_id)[0] == 202


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
        "NEEDS_INFORMATION",
    ],
)
def test_submit_state_gate(repo: CaseRepository, state: str) -> None:
    case_id = ready(repo)
    put_case(repo, case_id, status=state)
    assert send(repo, case_id)[1]["error"]["code"] == "CASE_INVALID_STATE"


def test_resubmit_requires_information_state(repo: CaseRepository) -> None:
    assert send(repo, ready(repo), "resubmit")[1]["error"]["code"] == "CASE_INVALID_STATE"


@pytest.mark.parametrize(
    "actor,groups,status",
    [
        ("alice", ["reviewer"], 403),
        ("bob", ["requester"], 404),
        ("bob", ["reviewer"], 403),
        ("bob", ["admin"], 202),
    ],
)
def test_roles(repo: CaseRepository, actor: str, groups: list[str], status: int) -> None:
    case_id = ready(repo)
    claims = {"sub": actor, "cognito:groups": groups, "token_use": "access"}
    assert (
        send(repo, case_id, requestContext={"authorizer": {"jwt": {"claims": claims}}})[0] == status
    )


@pytest.mark.parametrize(
    "body", ["", "null", "[]", '{"attempt":3}', '{"status":"SUBMITTED"}', "{", "x" * 4097]
)
def test_input_rejection(repo: CaseRepository, body: str) -> None:
    assert send(repo, ready(repo), body=body)[0] == 400


@pytest.mark.parametrize("key", ["", "not-uuid", KEY.replace("-", ""), KEY + "x"])
def test_key_rejection(repo: CaseRepository, key: str) -> None:
    assert send(repo, ready(repo), headers={"Idempotency-Key": key})[0] == 400


def test_base64_and_uuid_normalization(repo: CaseRepository) -> None:
    case_id = ready(repo)
    first = send(repo, case_id, body=base64.b64encode(b"{}").decode(), isBase64Encoded=True)
    assert first[0] == 202
    assert send(repo, case_id, headers={"IDEMPOTENCY-KEY": KEY.upper()}) == first


def test_bound_template_and_paginated_documents(repo: CaseRepository) -> None:
    case_id = ready(repo)
    TemplateRepository(repo.client, repo.table_name).publish(
        replace(SEED, version=2, required_documents=(*SEED.required_documents, "EXTRA")),
        actor_id="seed",
    )
    original = repo.client.query

    def paged(**kwargs: Any) -> Any:
        return original(**{**kwargs, "Limit": 1})

    with patch.object(repo.client, "query", side_effect=paged):
        assert send(repo, case_id)[0] == 202
    assert repo.get(case_id)["workflowInput"]["checklistTemplateVersion"] == 1


@pytest.mark.parametrize("race", ["upload", "delete", "version", "owner", "attempt", "revision"])
def test_changes_between_validation_and_commit_rollback(repo: CaseRepository, race: str) -> None:
    case_id = ready(repo)
    original = repo.client.transact_write_items
    raced = False

    def write(**kwargs: Any) -> Any:
        nonlocal raced
        if not raced:
            raced = True
            if race == "upload":
                reservation(repo, case_id)
            elif race == "delete":
                doc = repo.related(case_id, "DOC#")[0]
                delete_document(repo, case_id, doc["documentId"], "alice", {"requester"}, "test")
            else:
                change: dict[str, dict[str, Any]] = {
                    "version": {"version": 2},
                    "owner": {"requesterId": "bob"},
                    "attempt": {"submissionAttempt": 2},
                    "revision": {"documentRevision": 99},
                }
                put_case(repo, case_id, **change[race])
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=write):
        status, response = send(repo, case_id)
    assert status == 409 and response["error"]["code"] == "SUBMISSION_CONFLICT"
    assert not any(r.get("action") == "CASE_SUBMITTED" for r in rows(repo))
    assert not any(r.get("PK") == "IDEMPOTENCY#case-submission" for r in rows(repo))


@pytest.mark.parametrize("operation", ["submit", "resubmit"])
@pytest.mark.parametrize("same_key", [True, False])
def test_competing_submissions_have_one_attempt(
    repo: CaseRepository, same_key: bool, operation: str
) -> None:
    case_id = ready(repo)
    if operation == "resubmit":
        put_case(repo, case_id, status="NEEDS_INFORMATION", submissionAttempt=1)
    original = repo.client.transact_write_items
    competed = False
    winner: dict[str, Any] = {}

    def write(**kwargs: Any) -> Any:
        nonlocal competed, winner
        if not competed:
            competed = True
            winner = submit(
                repo,
                case_id,
                "alice",
                {"requester"},
                operation,
                KEY if same_key else str(uuid4()),
                "winner",
            )
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=write):
        status, response = send(repo, case_id, operation)
    assert status == (202 if same_key else 409)
    if same_key:
        assert response == winner
    assert repo.get(case_id)["submissionAttempt"] == (1 if operation == "submit" else 2)
    assert (
        len(
            [
                r
                for r in rows(repo)
                if r.get("action")
                == ("CASE_SUBMITTED" if operation == "submit" else "CASE_RESUBMITTED")
            ]
        )
        == 1
    )


def test_uncertain_response_retries_receipt(repo: CaseRepository) -> None:
    case_id = ready(repo)
    original = repo.client.transact_write_items

    def write(**kwargs: Any) -> Any:
        original(**kwargs)
        raise ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "private"}}, "TransactWriteItems"
        )

    with patch.object(repo.client, "transact_write_items", side_effect=write):
        status, response = send(repo, case_id)
    assert status == 503 and "private" not in json.dumps(response)
    assert send(repo, case_id)[0] == 202
    assert repo.get(case_id)["submissionAttempt"] == 1


def test_revision_lifecycle_and_legacy_case(repo: CaseRepository) -> None:
    case_id = ready(repo)
    case = repo.get(case_id)
    del case["documentRevision"]
    repo.client.put_item(TableName=repo.table_name, Item=encode(case))
    doc = reservation(repo, case_id)
    assert repo.get(case_id)["documentRevision"] == 1
    delete_document(repo, case_id, doc["documentId"], "alice", {"requester"}, "test")
    assert repo.get(case_id)["documentRevision"] == 2
    delete_document(repo, case_id, doc["documentId"], "alice", {"requester"}, "test")
    assert repo.get(case_id)["documentRevision"] == 2
    assert send(repo, case_id)[0] == 202
    with pytest.raises(ApiError, match="does not allow"):
        reservation(repo, case_id)


def test_receipt_cannot_bypass_current_owner(repo: CaseRepository) -> None:
    case_id = ready(repo)
    assert send(repo, case_id)[0] == 202
    put_case(repo, case_id, requesterId="bob")
    assert send(repo, case_id)[0] == 404


def test_idempotency_key_scoped_to_case(repo: CaseRepository) -> None:
    assert send(repo, ready(repo))[0] == 202
    assert send(repo, ready(repo))[0] == 202


def test_legacy_zero_revision_submission(repo: CaseRepository) -> None:
    case_id = ready(repo)
    case = repo.get(case_id)
    del case["documentRevision"]
    repo.client.put_item(TableName=repo.table_name, Item=encode(case))
    assert send(repo, case_id)[0] == 202
