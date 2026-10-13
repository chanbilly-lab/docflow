"""Persisted decision, callback uncertainty, race fencing and workflow finalization."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch
from uuid import uuid4

import boto3
import pytest
from botocore.exceptions import ClientError
from botocore.stub import Stubber
from jsonschema import Draft202012Validator
from test_domain_events import validator
from test_review_commands import send, setup
from test_submission import rows

from common.cases.repository import ApiError, CaseRepository
from common.cases.workflow_state import fail
from common.reviews.creation import create_review
from common.reviews.decisions import decide
from common.reviews.finalization import finalize
from common.reviews.query import detail, get_task, queue
from common.templates.repository import encode
from review_api.command import handle

ROOT = Path(__file__).resolve().parents[3]
INFO: dict[str, Any] = {
    "decision": "REQUEST_INFORMATION",
    "reason": "Replacement required",
    "requestedItems": [
        {
            "documentType": "ADDRESS_PROOF",
            "reasonCode": "MISSING",
            "message": "Provide current proof",
        }
    ],
}


def ready(repo: CaseRepository) -> tuple[str, str, str, dict[str, Any]]:
    case, task, check, event = setup(repo)
    assert send(repo, task, "claim")[0] == 200
    assert send(repo, task, "start")[0] == 200
    for row in repo.related(case, "CHECK#"):
        if row["required"]:
            assert (
                send(repo, task, "check", check=row["checkId"], payload={"result": "PASS"})[0]
                == 200
            )
    return case, task, check, event


def request(
    repo: CaseRepository,
    task: str,
    service: Any,
    key: str,
    payload: Any = None,
    actor: str = "bob",
    groups: list[str] | None = None,
) -> tuple[int, dict[str, Any]]:
    event = {
        "routeKey": "POST /api/v1/reviews/{taskId}/decision",
        "pathParameters": {"taskId": task},
        "headers": {"Idempotency-Key": key},
        "body": json.dumps({"decision": "APPROVE"} if payload is None else payload),
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": actor,
                        "token_use": "access",
                        "cognito:groups": groups or ["reviewer"],
                    }
                }
            }
        },
    }
    response = handle(event, repo, service)
    data: dict[str, Any] = json.loads(response["body"])
    api = json.loads((ROOT / "docs/api/openapi.yaml").read_text(encoding="utf-8"))
    schema = "ReviewDecisionResponse" if response["statusCode"] == 202 else "Error"
    Draft202012Validator(
        {"$ref": "#/components/schemas/" + schema, "components": api["components"]}
    ).validate(data)
    assert "workflowTaskToken" not in response["body"]
    return response["statusCode"], data


@pytest.mark.parametrize(
    "payload,state,kind",
    [
        ({"decision": "APPROVE"}, "APPROVED", "CaseApproved"),
        ({"decision": "REJECT", "reason": "Invalid evidence"}, "REJECTED", "CaseRejected"),
        (INFO, "NEEDS_INFORMATION", "AdditionalInformationRequested"),
    ],
)
def test_branches_finalization_and_replay(
    repo: CaseRepository, payload: dict[str, Any], state: str, kind: str
) -> None:
    case, task, check, event = ready(repo)
    service, key = Mock(), str(uuid4())
    assert request(repo, task, service, key, payload)[0] == 202
    stored = get_task(repo, task)
    assert stored["status"] == "COMPLETED" and stored["callbackStatus"] == "DELIVERED"
    assert repo.get(case)["status"] == "IN_REVIEW"
    service.send_task_success.assert_called_once_with(
        taskToken=event["taskToken"], output=json.dumps(stored["callbackOutput"], sort_keys=True)
    )
    assert send(repo, task, "check", check=check, payload={"result": "FAIL"})[0] == 409
    # Follow the actual deployed ASL choice and task input contract.
    asl = json.loads((ROOT / "infra/modules/workflow/definition.asl.json").read_text())
    choice = next(
        c
        for c in asl["States"]["DecisionChoice"]["Choices"]
        if c["StringEquals"] == payload["decision"]
    )
    node = asl["States"][choice["Next"]]
    assert node["Parameters"]["Payload"]["decision.$"] == "$.reviewDecision"
    assert node["Catch"][0]["Next"] == "MarkWorkflowFailed"
    final_event = {**event, "decision": stored["callbackOutput"]}
    assert finalize(repo, final_event) == {"status": state}
    before = rows(repo)
    assert finalize(repo, final_event) == {"status": state}
    assert request(repo, task, service, key, payload)[0] == 202
    assert rows(repo) == before and service.send_task_success.call_count == 1
    facts = [r for r in repo.related(case, "OUTBOX#") if r["eventType"] == kind]
    assert len(facts) == 1
    validator().validate(
        {
            "source": facts[0]["source"],
            "detail-type": kind,
            "detail": json.loads(json.dumps(facts[0]["detail"], default=int)),
        }
    )
    public = json.dumps(detail(repo, task, "bob", {"reviewer"}), default=str)
    assert event["taskToken"] not in public
    assert all(
        k not in public
        for k in ("callbackOutput", "decisionKey", "decisionHash", "workflowExecutionArn")
    )
    assert repo.detail(repo.get(case))["case"]["status"] == state
    assert repo.get(case)["requestedInformation"] == payload.get("requestedItems", [])
    assert len([r for r in repo.related(case, "AUDIT#") if r["action"] == "REVIEW_DECIDED"]) == 1


def error(code: str = "TaskTimedOut") -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": "private callback context"}}, "SendTaskSuccess"
    )


@pytest.mark.parametrize(
    "code", ["TaskTimedOut", "TaskDoesNotExist", "InvalidToken", "ServiceUnavailable"]
)
def test_pending_is_durable_and_closed_token_is_not_delivery_proof(
    repo: CaseRepository, code: str
) -> None:
    case, task, _, event = ready(repo)
    service, key = Mock(), str(uuid4())
    service.send_task_success.side_effect = error(code)
    status, data = request(repo, task, service, key)
    assert status == 503 and data["error"]["code"] == "CALLBACK_PENDING"
    saved = get_task(repo, task)
    assert saved["callbackStatus"] == "PENDING" and saved["decision"] == "APPROVE"
    assert request(repo, task, service, str(uuid4()))[0] == 409
    assert request(repo, task, service, key, {"decision": "REJECT", "reason": "changed"})[0] == 409
    assert request(repo, task, service, key)[0] == 503
    assert get_task(repo, task) == saved
    service.send_task_success.side_effect = None
    assert request(repo, task, service, key)[0] == 202
    assert len([r for r in repo.related(case, "AUDIT#") if r["action"] == "REVIEW_DECIDED"]) == 1
    assert all(
        c.kwargs["output"] == json.dumps(saved["callbackOutput"], sort_keys=True)
        for c in service.send_task_success.call_args_list
    )
    assert event["taskToken"] not in json.dumps(data)


def test_finalizer_proves_delivery_after_lost_sdk_response(repo: CaseRepository) -> None:
    _, task, _, event = ready(repo)
    service, key = Mock(), str(uuid4())

    def accepted(**kwargs: Any) -> None:
        finalize(repo, {**event, "decision": json.loads(kwargs["output"])})
        raise error()

    service.send_task_success.side_effect = accepted
    assert request(repo, task, service, key)[0] == 202
    assert get_task(repo, task)["finalizedAt"]


@pytest.mark.parametrize(
    "mutation", ["different_decision", "same_decision", "check", "failure", "attempt"]
)
def test_transaction_interleavings(repo: CaseRepository, mutation: str) -> None:
    case, task, check, event = ready(repo)
    key, service = str(uuid4()), Mock()
    original, raced = repo.client.transact_write_items, False

    def race(**kwargs: Any) -> Any:
        nonlocal raced
        if not raced:
            raced = True
            if mutation in {"different_decision", "same_decision"}:
                decision = (
                    {"decision": "REJECT", "reason": "First"}
                    if mutation == "different_decision"
                    else None
                )
                assert (
                    request(repo, task, service, str(uuid4()) if decision else key, decision)[0]
                    == 202
                )
            elif mutation == "check":
                assert (
                    send(repo, task, "check", check=check, payload={"result": "NOT_REVIEWED"})[0]
                    == 200
                )
            elif mutation == "failure":
                fail(repo, event)
            else:
                row = repo.get(case)
                repo.client.put_item(
                    TableName=repo.table_name, Item=encode({**row, "submissionAttempt": 2})
                )
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        assert request(repo, task, service, key)[0] == (202 if mutation == "same_decision" else 409)
    audits = [r for r in repo.related(case, "AUDIT#") if r["action"] == "REVIEW_DECIDED"]
    assert len(audits) == (1 if "decision" in mutation else 0)
    if mutation == "different_decision":
        assert get_task(repo, task)["decision"] == "REJECT"


def test_refresh_pending_completed_token_and_failure_cleanup(repo: CaseRepository) -> None:
    case, task, _, event = ready(repo)
    service, key = Mock(), str(uuid4())
    service.send_task_success.side_effect = error()
    assert request(repo, task, service, key)[0] == 503
    original = get_task(repo, task)
    newer = {**event, "retryCount": 1, "taskToken": str(uuid4())}
    create_review(repo, newer)
    create_review(repo, event)
    assert get_task(repo, task)["workflowTaskToken"] == newer["taskToken"]
    assert get_task(repo, task)["callbackOutput"] == original["callbackOutput"]
    assert fail(repo, event)["recorded"]
    assert get_task(repo, task)["decision"] == "APPROVE"
    assert get_task(repo, task)["callbackStatus"] == "FAILED"
    assert request(repo, task, service, key)[0] == 409
    assert queue(repo, "bob", "mine", None, 100, None)["items"] == []
    with pytest.raises(ValueError):
        finalize(repo, {**event, "decision": original["callbackOutput"]})
    assert repo.get(case)["status"] == "WORKFLOW_FAILED"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"decision": []},
        {"decision": "OTHER"},
        {"decision": "APPROVE", "taskToken": "forged"},
        {"decision": "REJECT"},
        {"decision": "REJECT", "reason": " "},
        {"decision": "REJECT", "reason": "x" * 2001},
        {"decision": "REQUEST_INFORMATION", "reason": "x", "requestedItems": []},
        {"decision": "REQUEST_INFORMATION", "reason": "x", "requestedItems": [1]},
        {**INFO, "requestedItems": INFO["requestedItems"] * 2},
    ],
)
def test_invalid_request_does_not_write(repo: CaseRepository, payload: dict[str, Any]) -> None:
    _, task, _, _ = ready(repo)
    before = rows(repo)
    assert request(repo, task, Mock(), str(uuid4()), payload)[0] == 400
    assert rows(repo) == before


@pytest.mark.parametrize(
    "actor,groups", [("alice", ["requester"]), ("carol", ["reviewer"]), ("carol", ["admin"])]
)
def test_assignment_enforced(repo: CaseRepository, actor: str, groups: list[str]) -> None:
    _, task, _, _ = ready(repo)
    before = rows(repo)
    assert request(repo, task, Mock(), str(uuid4()), actor=actor, groups=groups)[0] == 403
    assert rows(repo) == before


def test_required_check_and_key_validation(repo: CaseRepository) -> None:
    _, task, check, _ = ready(repo)
    assert request(repo, task, Mock(), "")[0] == 400
    assert send(repo, task, "check", check=check, payload={"result": "NOT_REVIEWED"})[0] == 200
    assert request(repo, task, Mock(), str(uuid4()))[0] == 422


@pytest.mark.parametrize("tamper", ["decision", "execution", "attempt"])
def test_finalization_rejects_wrong_context(repo: CaseRepository, tamper: str) -> None:
    _, task, _, event = ready(repo)
    assert request(repo, task, Mock(), str(uuid4()))[0] == 202
    final_event = {**event, "decision": get_task(repo, task)["callbackOutput"]}
    if tamper == "decision":
        final_event["decision"] = {**final_event["decision"], "decision": "REJECT"}
    elif tamper == "execution":
        final_event["executionArn"] = "unrelated"
    else:
        final_event["submission"] = {**event["submission"], "attempt": 2}
    before = rows(repo)
    with pytest.raises(ValueError):
        finalize(repo, final_event)
    assert rows(repo) == before


def test_real_sdk_callback_shape(repo: CaseRepository) -> None:
    _, task, _, _ = ready(repo)
    service = boto3.client(
        "stepfunctions",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    with Stubber(service) as stub:
        stub.add_response("send_task_success", {})
        decide(
            repo,
            task,
            "bob",
            {"reviewer"},
            {"decision": "APPROVE"},
            str(uuid4()),
            "sdk-test",
            service,
        )
        stub.assert_no_pending_responses()


def test_finalizer_transaction_failure_has_no_partial_state(repo: CaseRepository) -> None:
    case, task, _, event = ready(repo)
    request(repo, task, Mock(), str(uuid4()))
    before = rows(repo)
    with patch.object(
        repo.client, "transact_write_items", side_effect=error("InternalServerError")
    ):
        with pytest.raises(ClientError):
            finalize(repo, {**event, "decision": get_task(repo, task)["callbackOutput"]})
    assert rows(repo) == before and repo.get(case)["status"] == "IN_REVIEW"


def test_callback_ack_failure_recovers_via_finalizer(repo: CaseRepository) -> None:
    _, task, _, event = ready(repo)
    service, key = Mock(), str(uuid4())
    original = repo.client.transact_write_items
    count = 0

    def fail_ack(**kwargs: Any) -> Any:
        nonlocal count
        count += 1
        if count == 2:
            raise error("InternalServerError")
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=fail_ack):
        assert request(repo, task, service, key)[0] == 503
    assert get_task(repo, task)["callbackStatus"] == "PENDING"
    service.send_task_success.side_effect = error()
    assert request(repo, task, service, key)[0] == 503
    finalize(repo, {**event, "decision": get_task(repo, task)["callbackOutput"]})
    assert request(repo, task, service, key)[0] == 202


@pytest.mark.parametrize("mutation", ["callback_ack", "finalizer", "failure"])
def test_finalizer_races_are_atomic_and_retryable(repo: CaseRepository, mutation: str) -> None:
    case, task, _, event = ready(repo)
    service, key = Mock(), str(uuid4())
    service.send_task_success.side_effect = error()
    request(repo, task, service, key)
    final_event = {**event, "decision": get_task(repo, task)["callbackOutput"]}
    original, raced = repo.client.transact_write_items, False

    def race(**kwargs: Any) -> Any:
        nonlocal raced
        if not raced:
            raced = True
            if mutation == "callback_ack":
                service.send_task_success.side_effect = None
                assert request(repo, task, service, key)[0] == 202
            elif mutation == "finalizer":
                finalize(repo, final_event)
            else:
                fail(repo, event)
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        with pytest.raises(ApiError) as caught:
            finalize(repo, final_event)
        assert caught.value.status == 409
    if mutation == "failure":
        with pytest.raises(ValueError):
            finalize(repo, final_event)
        assert repo.get(case)["status"] == "WORKFLOW_FAILED"
    else:
        assert finalize(repo, final_event)["status"] == "APPROVED"
        assert (
            len([r for r in repo.related(case, "OUTBOX#") if r["eventType"] == "CaseApproved"]) == 1
        )


def test_absent_decision_and_completed_fail_checks_are_supported(repo: CaseRepository) -> None:
    case, task, _, _ = ready(repo)
    row = get_task(repo, task)
    del row["decision"]
    repo.client.put_item(TableName=repo.table_name, Item=encode(row))
    for check in repo.related(case, "CHECK#"):
        if check["required"]:
            assert (
                send(repo, task, "check", check=check["checkId"], payload={"result": "FAIL"})[0]
                == 200
            )
    assert request(repo, task, Mock(), str(uuid4()), actor="bob", groups=["admin"])[0] == 202


def test_unknown_document_type_is_rejected(repo: CaseRepository) -> None:
    _, task, _, _ = ready(repo)
    payload = {**INFO, "requestedItems": [{**INFO["requestedItems"][0], "documentType": "UNKNOWN"}]}
    before = rows(repo)
    assert request(repo, task, Mock(), str(uuid4()), payload)[0] == 422
    assert rows(repo) == before
