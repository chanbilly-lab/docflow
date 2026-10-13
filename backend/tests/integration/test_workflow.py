"""Real persistence/workers plus a deterministic Standard-service double and ASL runner."""

import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import boto3
import pytest
from botocore.exceptions import ClientError
from botocore.stub import Stubber
from test_submission import KEY, put_case, ready, rows

from case_api.api import handle
from case_api.command import handler
from common.cases.repository import ApiError, CaseRepository
from common.cases.submission import submit
from common.cases.workflow import WorkflowStarter, canonical, recover_stream
from common.cases.workflow_state import fail, validate
from common.reviews.creation import create_review
from common.templates.repository import encode

MACHINE = "arn:aws:states:us-east-1:123456789012:stateMachine:docflow-dev-case-review-workflow"
ROOT = Path(__file__).resolve().parents[3]


def accepted(repo: CaseRepository) -> tuple[str, dict[str, Any]]:
    case_id = ready(repo)
    submit(repo, case_id, "alice", {"requester"}, "submit", KEY, "test")
    case = repo.get(case_id)
    return case_id, {
        "submission": case["workflowInput"],
        "executionArn": MACHINE.replace(":stateMachine:", ":execution:")
        + ":"
        + case["workflowExecutionName"],
    }


class Standard:
    def __init__(self) -> None:
        self.executions: dict[str, dict[str, Any]] = {}
        self.calls: list[dict[str, Any]] = []
        self.closed = False
        self.lose_response = False

    def start_execution(self, **request: Any) -> dict[str, Any]:
        self.calls.append(request)
        arn = (
            request["stateMachineArn"].replace(":stateMachine:", ":execution:")
            + ":"
            + request["name"]
        )
        if arn in self.executions and (
            self.closed or self.executions[arn]["input"] != request["input"]
        ):
            raise ClientError({"Error": {"Code": "ExecutionAlreadyExists"}}, "StartExecution")
        self.executions[arn] = {**request, "executionArn": arn}
        if self.lose_response:
            raise ClientError({"Error": {"Code": "InternalServerError"}}, "StartExecution")
        return {"executionArn": arn}

    def describe_execution(self, **request: Any) -> dict[str, Any]:
        return self.executions[request["executionArn"]]


def run_asl(repo: CaseRepository, event: dict[str, Any], *, outage: bool = False) -> list[str]:
    """Execute the checked-in foundation ASL subset, including Retry/Catch and Choice."""
    definition = json.loads((ROOT / "infra/modules/workflow/definition.asl.json").read_text())
    state = definition["StartAt"]
    original, data = copy.deepcopy(event["submission"]), copy.deepcopy(event["submission"])
    visited: list[str] = []
    for _ in range(10):
        visited.append(state)
        node = definition["States"][state]
        if node["Type"] in {"Succeed", "Fail"}:
            return visited
        if node["Type"] == "Choice":
            assert node["Choices"][0]["Variable"] == "$.validation.valid"
            state = node["Choices"][0]["Next"] if data["validation"]["valid"] else node["Default"]
            continue
        if node["Resource"].endswith(".waitForTaskToken"):
            assert node["Parameters"]["Payload"]["submission.$"] == "$$.Execution.Input"
            assert node["Parameters"]["Payload"]["taskToken.$"] == "$$.Task.Token"
            create_review(
                repo,
                {
                    **event,
                    "taskToken": str(uuid4()),
                    "enteredTime": datetime.now(UTC).isoformat(),
                    "retryCount": 0,
                },
            )
            return visited  # Service remains WAITING, no callback is fabricated.
        assert node["Resource"] == "arn:aws:states:::lambda:invoke"
        payload = node["Parameters"]["Payload"]
        assert payload["executionArn.$"] == "$$.Execution.Id"
        submission = original if payload["submission.$"] == "$$.Execution.Input" else data
        request = {"submission": submission, "executionArn": event["executionArn"]}
        for attempt in range(node["Retry"][0]["MaxAttempts"] + 1):
            try:
                if node["Parameters"]["FunctionName"] == "${validate_arn}":
                    if outage:
                        raise RuntimeError("private failure detail")
                    output = validate(repo, request)
                else:
                    output = fail(repo, request)
                if node["ResultPath"] == "$.validation":
                    assert node["ResultSelector"] == {"valid.$": "$.Payload.valid"}
                    data["validation"] = {"valid": output["valid"]}
                state = node["Next"]
                break
            except Exception:
                if attempt < node["Retry"][0]["MaxAttempts"]:
                    continue
                catch = node.get("Catch")
                if not catch:
                    raise
                assert catch[0]["ErrorEquals"] == ["States.ALL"]
                data["failure"] = {"Error": "RuntimeError", "Cause": "private failure detail"}
                state = catch[0]["Next"]
    raise AssertionError("Workflow did not terminate")


def test_standard_start_and_validation(repo: CaseRepository) -> None:
    case_id, event = accepted(repo)
    service = Standard()
    starter = WorkflowStarter(repo, service, MACHINE)
    assert starter.start(case_id, 1) == event["executionArn"]
    assert validate(repo, event)["valid"]
    before = rows(repo)
    assert validate(repo, event)["valid"]
    assert rows(repo) == before
    assert run_asl(repo, event) == ["ValidateCase", "ValidationChoice", "CreateReviewTaskAndWait"]
    assert starter.start(case_id, 1) == event["executionArn"]
    assert len(service.calls) == 1
    assert repo.get(case_id)["status"] == "REVIEW_PENDING"
    assert repo.get(case_id)["version"] == 4
    assert len([r for r in rows(repo) if r.get("action") == "CASE_PROCESSING"]) == 1


@pytest.mark.parametrize("closed", [False, True])
def test_crash_after_accepted_start_before_ack(repo: CaseRepository, closed: bool) -> None:
    case_id, event = accepted(repo)
    service = Standard()
    starter = WorkflowStarter(repo, service, MACHINE)
    with patch.object(
        repo.client,
        "update_item",
        side_effect=ClientError({"Error": {"Code": "InternalServerError"}}, "UpdateItem"),
    ):
        with pytest.raises(ClientError):
            starter.start(case_id, 1)
    # Worker may complete before command acknowledgement.
    run_asl(repo, event)
    service.closed = closed
    assert starter.start(case_id, 1) == event["executionArn"]
    assert len(service.executions) == 1 and service.calls[0] == service.calls[1]
    assert repo.get(case_id)["status"] == "REVIEW_PENDING"


def test_lost_start_response(repo: CaseRepository) -> None:
    case_id, event = accepted(repo)
    service = Standard()
    service.lose_response = True
    starter = WorkflowStarter(repo, service, MACHINE)
    with pytest.raises(ClientError):
        starter.start(case_id, 1)
    service.lose_response = False
    assert starter.start(case_id, 1) == event["executionArn"]
    assert len(service.executions) == 1


@pytest.mark.parametrize("field", ["input", "name", "stateMachineArn", "executionArn"])
def test_collision_fails_closed(repo: CaseRepository, field: str) -> None:
    case_id, _ = accepted(repo)
    service = Standard()
    starter = WorkflowStarter(repo, service, MACHINE)
    with patch.object(repo.client, "update_item", side_effect=RuntimeError):
        with pytest.raises(RuntimeError):
            starter.start(case_id, 1)
    service.closed = True
    next(iter(service.executions.values()))[field] = "mismatch"
    with pytest.raises(ApiError):
        starter.start(case_id, 1)
    assert repo.get(case_id)["workflowStartStatus"] == "PENDING"


def test_sdk_request_shape(repo: CaseRepository) -> None:
    case_id, event = accepted(repo)
    client = boto3.client(
        "stepfunctions",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    with Stubber(client) as stub:
        stub.add_response(
            "start_execution",
            {"executionArn": event["executionArn"], "startDate": datetime.now(UTC)},
            {
                "stateMachineArn": MACHINE,
                "name": repo.get(case_id)["workflowExecutionName"],
                "input": canonical(event["submission"]),
            },
        )
        assert WorkflowStarter(repo, client, MACHINE).start(case_id, 1) == event["executionArn"]
        stub.assert_no_pending_responses()


@pytest.mark.parametrize(
    "mutation",
    ["attempt", "revision", "template", "missing", "invalid", "processing", "execution", "state"],
)
def test_defensive_validation(repo: CaseRepository, mutation: str) -> None:
    case_id, event = accepted(repo)
    if mutation == "attempt":
        event["submission"] = {**event["submission"], "attempt": 2}
    elif mutation == "revision":
        put_case(repo, case_id, documentRevision=99)
    elif mutation == "template":
        put_case(repo, case_id, checklistTemplateVersion=2)
    elif mutation in {"missing", "invalid", "processing"}:
        doc = repo.related(case_id, "DOC#")[0]
        doc["status"] = {"missing": "DELETED", "invalid": "INVALID", "processing": "VALIDATING"}[
            mutation
        ]
        repo.client.put_item(TableName=repo.table_name, Item=encode(doc))
    elif mutation == "execution":
        event["executionArn"] += "wrong"
    else:
        put_case(repo, case_id, status="APPROVED")
    before = rows(repo)
    assert validate(repo, event) == {"valid": False}
    assert rows(repo) == before


@pytest.mark.parametrize("outage", [False, True])
def test_asl_failure_never_rejects(repo: CaseRepository, outage: bool) -> None:
    case_id, event = accepted(repo)
    if not outage:
        put_case(repo, case_id, documentRevision=99)
    visited = run_asl(repo, event, outage=outage)
    assert visited[-2:] == ["MarkWorkflowFailed", "Failed"]
    case = repo.get(case_id)
    assert case["status"] == "WORKFLOW_FAILED" and case["submissionAttempt"] == 1
    assert "private" not in canonical(rows(repo))
    before = rows(repo)
    assert fail(repo, event) == {"recorded": False}
    assert rows(repo) == before
    assert len([r for r in before if r.get("eventType") == "CaseWorkflowFailed"]) == 1


def test_stale_execution_and_receipt_cannot_change_next_attempt(repo: CaseRepository) -> None:
    case_id, old = accepted(repo)
    put_case(repo, case_id, status="NEEDS_INFORMATION")
    submit(repo, case_id, "alice", {"requester"}, "resubmit", str(uuid4()), "next")
    before = rows(repo)
    assert validate(repo, old) == {"valid": False}
    assert fail(repo, old) == {"recorded": False}
    service = Standard()
    assert WorkflowStarter(repo, service, MACHINE).start(case_id, 1) is None
    assert rows(repo) == before and service.calls == []


@pytest.mark.parametrize("worker", ["validate", "fail"])
def test_worker_transaction_race_rollback(repo: CaseRepository, worker: str) -> None:
    case_id, event = accepted(repo)
    original = repo.client.transact_write_items

    def race(**kwargs: Any) -> Any:
        put_case(repo, case_id, version=99, submissionAttempt=2)
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        with pytest.raises(ClientError):
            (validate if worker == "validate" else fail)(repo, event)
    assert not any(
        r.get("action") in {"CASE_PROCESSING", "CASE_WORKFLOW_FAILED"} for r in rows(repo)
    )
    assert repo.get(case_id)["status"] == "SUBMITTED"


def test_stream_retry_checkpoint_and_current_reads(repo: CaseRepository) -> None:
    case_id, _ = accepted(repo)
    row = repo.get(case_id)
    event = {
        "Records": [
            {
                "eventSource": "aws:dynamodb",
                "dynamodb": {
                    "SequenceNumber": "123",
                    "NewImage": encode(row),
                },
            }
        ]
    }
    service = Standard()
    starter = WorkflowStarter(repo, service, MACHINE)
    service.lose_response = True
    assert recover_stream(event, starter) == {"batchItemFailures": [{"itemIdentifier": "123"}]}
    service.lose_response = False
    assert recover_stream(event, starter) == {"batchItemFailures": []}
    assert recover_stream(event, starter) == {"batchItemFailures": []}
    assert len(service.calls) == 2 and len(service.executions) == 1


def test_old_intent_does_not_reuse_90_day_name(repo: CaseRepository) -> None:
    case_id, _ = accepted(repo)
    put_case(
        repo, case_id, workflowSubmittedAt=(datetime.now(UTC) - timedelta(days=86)).isoformat()
    )
    service = Standard()
    with pytest.raises(ApiError, match="Operator recovery"):
        WorkflowStarter(repo, service, MACHINE).start(case_id, 1)
    assert service.calls == []


def test_http_receipt_recovery(repo: CaseRepository) -> None:
    case_id, event = accepted(repo)
    request = {
        "routeKey": "POST /api/v1/cases/{caseId}/submit",
        "pathParameters": {"caseId": case_id},
        "body": "{}",
        "headers": {"idempotency-key": KEY},
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "alice",
                        "token_use": "access",
                        "cognito:groups": ["requester"],
                    }
                }
            }
        },
    }
    service = Standard()
    starter = WorkflowStarter(repo, service, MACHINE)
    service.lose_response = True
    assert handle(request, "command", repo, starter)["statusCode"] == 503
    service.lose_response = False
    result = handle(request, "command", repo, starter)
    assert result["statusCode"] == 202
    assert json.loads(result["body"])["workflowExecutionId"] == event["executionArn"]
    assert len(service.executions) == 1


def test_iam_operator_recovery_handler(repo: CaseRepository) -> None:
    case_id, event = accepted(repo)
    starter = WorkflowStarter(repo, Standard(), MACHINE)
    with (
        patch.dict("os.environ", {"TABLE_NAME": repo.table_name, "WORKFLOW_ARN": MACHINE}),
        patch("case_api.command.configured", return_value=starter),
        patch("case_api.command.boto3.client", return_value=repo.client),
    ):
        assert handler(
            {"operation": "recoverWorkflowStart", "caseId": case_id, "attempt": 1}, None
        ) == {"workflowExecutionId": event["executionArn"]}


def test_http_cannot_invoke_operator_recovery(repo: CaseRepository) -> None:
    result = handler(
        {
            "requestContext": {},
            "operation": "recoverWorkflowStart",
            "caseId": "c_private",
            "attempt": 1,
        },
        None,
    )
    assert result["statusCode"] == 401


@pytest.mark.parametrize("race", ["ack", "next_attempt"])
def test_start_ack_race_preserves_latest_case(repo: CaseRepository, race: str) -> None:
    case_id, event = accepted(repo)
    service = Standard()
    starter = WorkflowStarter(repo, service, MACHINE)
    original = repo.client.update_item

    def update(**kwargs: Any) -> Any:
        if race == "ack":
            put_case(
                repo,
                case_id,
                workflowStartStatus="STARTED",
                workflowExecutionId=event["executionArn"],
                status="PROCESSING",
                version=3,
            )
        else:
            put_case(repo, case_id, submissionAttempt=2, status="NEEDS_INFORMATION")
        return original(**kwargs)

    with patch.object(repo.client, "update_item", side_effect=update):
        assert starter.start(case_id, 1) == (event["executionArn"] if race == "ack" else None)
    assert repo.get(case_id)["status"] == ("PROCESSING" if race == "ack" else "NEEDS_INFORMATION")


def test_failure_persistence_outage_remains_failed(repo: CaseRepository) -> None:
    case_id, event = accepted(repo)
    with patch.object(
        repo.client,
        "transact_write_items",
        side_effect=ClientError({"Error": {"Code": "InternalServerError"}}, "TransactWriteItems"),
    ):
        with pytest.raises(ClientError):
            run_asl(repo, event, outage=True)
    assert repo.get(case_id)["status"] == "SUBMITTED"
    assert not any(r.get("eventType") == "CaseWorkflowFailed" for r in rows(repo))
    assert fail(repo, event) == {"recorded": True}
    assert repo.get(case_id)["status"] == "WORKFLOW_FAILED"


def test_validation_revision_race_cannot_enter_processing(repo: CaseRepository) -> None:
    case_id, event = accepted(repo)
    original = repo.client.transact_write_items

    def update(**kwargs: Any) -> Any:
        put_case(repo, case_id, documentRevision=999)
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=update):
        with pytest.raises(ClientError):
            validate(repo, event)
    assert repo.get(case_id)["status"] == "SUBMITTED"
    assert not any(r.get("action") == "CASE_PROCESSING" for r in rows(repo))


def test_closed_execution_sdk_describe_contract(repo: CaseRepository) -> None:
    case_id, event = accepted(repo)
    client = boto3.client(
        "stepfunctions",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    name = repo.get(case_id)["workflowExecutionName"]
    with Stubber(client) as stub:
        stub.add_client_error(
            "start_execution",
            service_error_code="ExecutionAlreadyExists",
            expected_params={
                "stateMachineArn": MACHINE,
                "name": name,
                "input": canonical(event["submission"]),
            },
        )
        stub.add_response(
            "describe_execution",
            {
                "executionArn": event["executionArn"],
                "stateMachineArn": MACHINE,
                "name": name,
                "status": "SUCCEEDED",
                "startDate": datetime.now(UTC),
                "input": canonical(event["submission"]),
            },
            {"executionArn": event["executionArn"]},
        )
        assert WorkflowStarter(repo, client, MACHINE).start(case_id, 1) == event["executionArn"]
        stub.assert_no_pending_responses()
