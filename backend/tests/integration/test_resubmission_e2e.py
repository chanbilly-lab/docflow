"""Local requester-to-reviewer journeys using production handlers and Moto storage."""

import copy
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import boto3
import pytest
from test_domain_events import validator
from test_review_commands import send
from test_review_decisions import INFO
from test_review_decisions import request as decide
from test_workflow import MACHINE, Standard, run_asl

from case_api.api import handle as case_http
from common.cases.repository import CaseRepository
from common.cases.workflow import WorkflowStarter
from common.cases.workflow_state import fail
from common.reviews.creation import create_review
from common.reviews.finalization import finalize
from common.reviews.query import detail, get_task
from common.templates.seed import SUPPLIER_ONBOARDING as SEED
from document_api.command import DELETE_ROUTE, ROUTE
from document_api.command import handle as document_http
from document_processor.handler import Processor
from document_processor.handler import handle as process_batch
from outbox_publisher.handler import Publisher

ROOT = Path(__file__).resolve().parents[3]
BUCKET = "resubmission-documents"


def http(route: str, case: str = "", body: Any = None, key: str = "") -> dict[str, Any]:
    return {
        "routeKey": route,
        "pathParameters": {"caseId": case},
        "body": json.dumps({} if body is None else body),
        "headers": {"idempotency-key": key, "x-correlation-id": "resubmit-e2e"},
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


def upload(
    repo: CaseRepository, s3: Any, case: str, kind: str, content: bytes
) -> tuple[dict[str, Any], dict[str, Any]]:
    response = document_http(
        http(
            ROUTE,
            case,
            {
                "documentType": kind,
                "fileName": "evidence.pdf",
                "fileSize": len(content),
                "mimeType": "application/pdf",
            },
        ),
        repo,
        s3,
        BUCKET,
    )
    assert response["statusCode"] == 201
    identifier = json.loads(response["body"])["documentId"]
    document = next(d for d in repo.related(case, "DOC#") if d["documentId"] == identifier)
    stored = s3.put_object(
        Bucket=BUCKET,
        Key=document["s3Key"],
        Body=content,
        ContentType="application/pdf",
        IfNoneMatch="*",
    )
    message = {
        "Records": [
            {
                "messageId": str(uuid4()),
                "body": json.dumps(
                    {
                        "source": "aws.s3",
                        "detail-type": "Object Created",
                        "detail": {
                            "bucket": {"name": BUCKET},
                            "object": {
                                "key": document["s3Key"],
                                "etag": stored["ETag"].strip('"'),
                                "size": len(content),
                            },
                        },
                    }
                ),
            }
        ]
    }
    return document, message


def submit_http(
    repo: CaseRepository, starter: WorkflowStarter, case: str, operation: str, key: str
) -> dict[str, Any]:
    return case_http(
        http("POST /api/v1/cases/{caseId}/" + operation, case, key=key), "command", repo, starter
    )


def review(repo: CaseRepository, case: str) -> tuple[str, dict[str, Any]]:
    row = repo.get(case)
    event = {
        "submission": copy.deepcopy(row["workflowInput"]),
        "executionArn": row["workflowExecutionId"],
    }
    assert run_asl(repo, event) == ["ValidateCase", "ValidationChoice", "CreateReviewTaskAndWait"]
    task = repo.detail(repo.get(case))["review"]["currentTask"]["taskId"]
    checks = repo.related(case, f"CHECK#{task}#")
    assert all(c["result"] == "NOT_REVIEWED" for c in checks)
    assert send(repo, task, "claim")[0] == 200
    assert send(repo, task, "start")[0] == 200
    for check in checks:
        assert (
            send(
                repo,
                task,
                "check",
                check=check["checkId"],
                payload={"result": "PASS", "comment": "Attempt-specific finding"},
            )[0]
            == 200
        )
    assert repo.get(case)["status"] == "IN_REVIEW"
    return task, event


class Callback:
    """Minimal callback service double; production finalizer consumes saved output."""

    def __init__(self, repo: CaseRepository, task: str, event: dict[str, Any]):
        self.repo, self.task, self.event = repo, task, event
        self.calls = 0

    def send_task_success(self, **kwargs: Any) -> None:
        self.calls += 1
        assert kwargs["taskToken"] == get_task(self.repo, self.task)["workflowTaskToken"]
        output = json.loads(kwargs["output"])
        states = json.loads((ROOT / "infra/modules/workflow/definition.asl.json").read_text())[
            "States"
        ]
        branch = next(
            c["Next"]
            for c in states["DecisionChoice"]["Choices"]
            if c["StringEquals"] == output["decision"]
        )
        assert states[branch]["Parameters"]["FunctionName"] == "${finalize_arn}"
        assert states[branch]["Parameters"]["Payload"]["submission.$"] == "$$.Execution.Input"
        finalize(self.repo, {**self.event, "decision": output})


@pytest.mark.parametrize("replacement", [True, False], ids=["replace", "add"])
def test_information_request_to_second_review_approval(
    repo: CaseRepository, replacement: bool
) -> None:
    args: dict[str, Any] = {
        "region_name": "us-east-1",
        "aws_access_key_id": "testing",
        "aws_secret_access_key": "testing",
    }
    s3 = boto3.client("s3", **args)
    s3.create_bucket(Bucket=BUCKET)
    processor = Processor(repo, s3, BUCKET)
    created = case_http(
        http("POST /api/v1/cases", body={"caseType": SEED.case_type}), "command", repo
    )
    assert created["statusCode"] == 201
    case = json.loads(created["body"])["caseId"]
    originals = {}
    for kind in SEED.required_documents:
        doc, message = upload(repo, s3, case, kind, b"%PDF-1.7\noriginal")
        assert process_batch(message, processor) == {"batchItemFailures": []}
        originals[kind] = (doc, message)
    service = Standard()
    starter = WorkflowStarter(repo, service, MACHINE)
    initial_key = str(uuid4())
    assert submit_http(repo, starter, case, "submit", initial_key)["statusCode"] == 202
    first, first_event = review(repo, case)
    callback = Callback(repo, first, first_event)
    decision_key = str(uuid4())
    assert decide(repo, first, callback, decision_key, INFO)[0] == 202
    assert repo.get(case)["status"] == "NEEDS_INFORMATION"
    exposed = case_http(http("GET /api/v1/cases/{caseId}", case), "query", repo)
    assert exposed["statusCode"] == 200
    assert json.loads(exposed["body"])["requestedInformation"] == INFO["requestedItems"]
    old_task = copy.deepcopy(get_task(repo, first))
    old_checks = copy.deepcopy(repo.related(case, f"CHECK#{first}#"))
    old_audits = {a["SK"]: a for a in repo.related(case, "AUDIT#")}
    # Historical submit retry cannot create another attempt from NEEDS_INFORMATION.
    assert (
        json.loads(submit_http(repo, starter, case, "submit", initial_key)["body"])["attempt"] == 1
    )
    assert repo.get(case)["submissionAttempt"] == 1

    old_doc, old_message = originals["ADDRESS_PROOF"]
    if replacement:
        deletion = http(DELETE_ROUTE, case)
        deletion["body"] = ""
        deletion["pathParameters"]["documentId"] = old_doc["documentId"]
        assert document_http(deletion, repo)["statusCode"] == 204
        assert process_batch(old_message, processor) == {"batchItemFailures": []}
        missing = submit_http(repo, starter, case, "resubmit", str(uuid4()))
        assert missing["statusCode"] == 422
    added, message = upload(repo, s3, case, "ADDRESS_PROOF", b"%PDF-1.7\nupdated")
    assert added["documentId"] != old_doc["documentId"] and added["s3Key"] != old_doc["s3Key"]
    second_key = str(uuid4())
    assert submit_http(repo, starter, case, "resubmit", second_key)["statusCode"] == 422
    assert repo.get(case)["submissionAttempt"] == 1
    assert process_batch(message, processor) == {"batchItemFailures": []}
    revision = repo.get(case)["documentRevision"]
    assert process_batch(message, processor) == {"batchItemFailures": []}
    assert repo.get(case)["documentRevision"] == revision
    assert (
        s3.get_object(Bucket=BUCKET, Key=old_doc["s3Key"])["Body"].read() == b"%PDF-1.7\noriginal"
    )
    accepted = submit_http(repo, starter, case, "resubmit", second_key)
    assert accepted["statusCode"] == 202
    second_receipt = json.loads(accepted["body"])
    assert second_receipt["status"] == "SUBMITTED" and second_receipt["attempt"] == 2
    assert second_receipt["workflowExecutionId"] != first_event["executionArn"]
    assert submit_http(repo, starter, case, "resubmit", second_key)["body"] == accepted["body"]
    assert len(service.executions) == 2
    second, second_event = review(repo, case)
    assert second != first
    assert get_task(repo, second)["workflowTaskToken"] != old_task["workflowTaskToken"]
    assert detail(repo, first, "bob", {"reviewer"})["checks"] == [
        {
            k: c[k]
            for k in (
                "checkId",
                "order",
                "documentType",
                "required",
                "instructions",
                "result",
                "comment",
                "updatedBy",
                "updatedAt",
            )
        }
        for c in sorted(old_checks, key=lambda c: c["order"])
    ]
    # Late first-attempt workers and API retries cannot mutate the active attempt.
    before = copy.deepcopy(repo.get(case))
    assert fail(repo, first_event) == {"recorded": False}
    with pytest.raises(ValueError):
        finalize(repo, {**first_event, "decision": old_task["callbackOutput"]})
    with pytest.raises(ValueError):
        create_review(
            repo,
            {
                **first_event,
                "taskToken": str(uuid4()),
                "retryCount": 1,
                "enteredTime": "2026-09-21T00:00:00Z",
            },
        )
    assert decide(repo, first, callback, decision_key, INFO)[0] == 202
    assert callback.calls == 1
    assert (
        send(repo, first, "check", check=old_checks[0]["checkId"], payload={"result": "FAIL"})[0]
        == 409
    )
    assert repo.get(case) == before
    second_callback = Callback(repo, second, second_event)
    approval_key = str(uuid4())
    assert decide(repo, second, second_callback, approval_key)[0] == 202
    assert decide(repo, second, second_callback, approval_key)[0] == 202
    assert second_callback.calls == 1
    assert repo.get(case)["status"] == "APPROVED"
    assert repo.detail(repo.get(case))["requestedInformation"] == []
    assert get_task(repo, first) == old_task
    assert repo.related(case, f"CHECK#{first}#") == old_checks
    assert all(
        a == next(r for r in repo.related(case, "AUDIT#") if r["SK"] == key)
        for key, a in old_audits.items()
    )
    assert repo.detail(repo.get(case))["review"]["currentTask"]["taskId"] == second
    docs = repo.detail(repo.get(case))["documents"]
    assert any(d["documentId"] == old_doc["documentId"] for d in docs) is not replacement
    events = boto3.client("events", **args)
    bus = events.create_event_bus(Name="resubmission-domain")["EventBusArn"]
    publisher = Publisher(repo, events, bus)
    facts = repo.related(case, "OUTBOX#")
    for fact in facts:
        validator().validate(
            {
                "source": fact["source"],
                "detail-type": fact["eventType"],
                "detail": json.loads(json.dumps(fact["detail"], default=int)),
            }
        )
        publisher.publish(fact)
        publisher.publish(fact)
    kinds = [f["eventType"] for f in facts]
    assert (
        kinds.count("CaseResubmitted")
        == kinds.count("AdditionalInformationRequested")
        == kinds.count("CaseApproved")
        == 1
    )
    assert kinds.count("CaseReadyForReview") == kinds.count("ReviewStarted") == 2
    assert all(f["status"] == "DISPATCHED" for f in repo.related(case, "OUTBOX#"))
