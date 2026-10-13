"""Real command transactions under deterministic concurrent interleavings."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from jsonschema import Draft202012Validator
from test_reviews import prepared
from test_reviews import request as query
from test_submission import put_case, rows

from common.cases.repository import CaseRepository
from common.cases.workflow_state import fail
from common.reviews.creation import create_review
from common.reviews.query import get_task
from common.templates.repository import encode
from review_api.command import handle

ROOT = Path(__file__).resolve().parents[3]


def setup(repo: CaseRepository) -> tuple[str, str, str, dict[str, Any]]:
    case_id, event = prepared(repo)
    task = create_review(repo, event)["taskId"]
    check = repo.related(case_id, f"CHECK#{task}#")[0]["checkId"]
    return case_id, task, check, event


def send(
    repo: CaseRepository,
    task: str,
    op: str,
    *,
    actor: str = "bob",
    groups: list[str] | None = None,
    check: str = "",
    payload: Any = None,
    changes: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    event = {
        "routeKey": (
            "PUT /api/v1/reviews/{taskId}/checks/{checkId}"
            if op == "check"
            else "POST /api/v1/reviews/{taskId}/" + op
        ),
        "pathParameters": {"taskId": task, "checkId": check},
        "body": json.dumps(payload if payload is not None else {}),
        "headers": {"x-correlation-id": "command-test"},
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": actor,
                        "token_use": "access",
                        "cognito:groups": groups if groups is not None else ["reviewer"],
                    }
                }
            }
        },
        **(changes or {}),
    }
    result = handle(event, repo)
    assert result["headers"]["cache-control"] == "no-store"
    data: dict[str, Any] = json.loads(result["body"])
    if result["statusCode"] == 200:
        api = json.loads((ROOT / "docs/api/openapi.yaml").read_text(encoding="utf-8"))
        schema = {
            "claim": "ClaimReviewResponse",
            "start": "StartReviewResponse",
            "check": "UpdateCheckResponse",
        }[op]
        Draft202012Validator(
            {"$ref": "#/components/schemas/" + schema, "components": api["components"]}
        ).validate(data)
    return result["statusCode"], data


def test_full_claim_start_findings_and_noop_retries(repo: CaseRepository) -> None:
    case_id, task, check, event = setup(repo)
    before_case = repo.get(case_id)
    assert send(repo, task, "claim")[0] == 200
    claimed = get_task(repo, task)
    assert claimed["GSI1PK"] == "REVIEWER#bob"
    assert claimed["GSI1SK"].startswith("TASK#CLAIMED#DUE#")
    assert repo.get(case_id) == before_case
    before = rows(repo)
    assert send(repo, task, "claim")[0] == 200
    assert rows(repo) == before
    assert json.loads(query(repo)["body"])["items"] == []
    assert len(json.loads(query(repo, scope="mine", status="CLAIMED")["body"])["items"]) == 1
    code, started = send(repo, task, "start")
    assert code == 200
    case = repo.get(case_id)
    assert case["status"] == "IN_REVIEW" and case["version"] == before_case["version"] + 1
    assert case["GSI2PK"] == "CASE_STATUS#IN_REVIEW"
    assert get_task(repo, task)["GSI1SK"].startswith("TASK#IN_PROGRESS#DUE#")
    before = rows(repo)
    assert send(repo, task, "start") == (200, started)
    assert rows(repo) == before
    comment = "Internal reviewer note " + uuid4().hex
    code, updated = send(
        repo, task, "check", check=check, payload={"result": "PASS", "comment": comment}
    )
    assert code == 200
    found = repo.related(case_id, f"CHECK#{task}#")[0]
    assert found["comment"] == comment and found["updatedBy"] == "bob" and found["version"] == 1
    assert get_task(repo, task)["checkRevision"] == 1
    before = rows(repo)
    assert send(
        repo, task, "check", check=check, payload={"result": "PASS", "comment": comment}
    ) == (200, updated)
    assert rows(repo) == before
    facts = [r for r in rows(repo) if r.get("eventType") == "ReviewStarted"]
    assert len(facts) == 1 and facts[0]["source"] == "docflow.review"
    assert facts[0]["detail"]["data"] == {
        "taskId": task,
        "attempt": 1,
        "reviewerId": "bob",
        "startedAt": started["startedAt"],
    }
    assert facts[0]["detail"]["correlationId"] == "command-test"
    audits = repo.related(case_id, "AUDIT#")
    assert len([r for r in audits if r["action"] == "REVIEW_CLAIMED"]) == 1
    assert len([r for r in audits if r["action"] == "REVIEW_STARTED"]) == 1
    assert len([r for r in audits if r["action"] == "CHECK_RESULT_UPDATED"]) == 1
    assert comment not in str(audits) + str(facts) + str(repo.activity(case_id, "alice", 100, None))
    assert event["taskToken"] not in str(started) + str(updated) + str(audits) + str(facts)
    create_review(repo, {**event, "retryCount": 1, "taskToken": str(uuid4())})
    assert repo.related(case_id, f"CHECK#{task}#")[0] == found


def test_two_claimants_have_exactly_one_winner(repo: CaseRepository) -> None:
    case_id, task, _, _ = setup(repo)
    original = repo.client.transact_write_items
    interleaved = False
    other: list[int] = []

    def race(**kwargs: Any) -> Any:
        nonlocal interleaved
        if not interleaved:
            interleaved = True
            other.append(send(repo, task, "claim", actor="carol")[0])
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        code, response = send(repo, task, "claim")
    assert other == [200] and code == 409
    assert response["error"]["code"] == "REVIEW_TASK_ALREADY_CLAIMED"
    assert get_task(repo, task)["reviewerId"] == "carol"
    assert len([r for r in repo.related(case_id, "AUDIT#") if r["action"] == "REVIEW_CLAIMED"]) == 1
    assert send(repo, task, "claim")[0] == 409


@pytest.mark.parametrize("op", ["claim", "start", "check"])
@pytest.mark.parametrize("groups", [["requester"], [], ["unknown"]])
def test_unpermitted_roles_cannot_mutate(repo: CaseRepository, op: str, groups: list[str]) -> None:
    _, task, check, _ = setup(repo)
    before = rows(repo)
    assert (
        send(
            repo,
            task,
            op,
            groups=groups,
            check=check,
            payload={"result": "PASS"} if op == "check" else {},
        )[0]
        == 403
    )
    assert rows(repo) == before


@pytest.mark.parametrize("groups", [["reviewer"], ["admin"], ["requester", "admin"]])
@pytest.mark.parametrize("op", ["start", "check"])
def test_admin_and_reviewer_cannot_bypass_assignee(
    repo: CaseRepository, groups: list[str], op: str
) -> None:
    _, task, check, _ = setup(repo)
    send(repo, task, "claim")
    send(repo, task, "start")
    before = rows(repo)
    code, data = send(
        repo,
        task,
        op,
        actor="carol",
        groups=groups,
        check=check,
        payload={"result": "PASS"} if op == "check" else {},
    )
    assert code == 403 and data["error"]["code"] == "REVIEW_TASK_NOT_ASSIGNED"
    assert rows(repo) == before


def test_admin_can_claim_and_act_as_assignee(repo: CaseRepository) -> None:
    _, task, check, _ = setup(repo)
    for op, payload in [("claim", {}), ("start", {}), ("check", {"result": "FAIL"})]:
        assert send(repo, task, op, groups=["admin"], check=check, payload=payload)[0] == 200


@pytest.mark.parametrize("mutation", ["timeout", "attempt", "completed"])
@pytest.mark.parametrize("op", ["claim", "start", "check"])
def test_inactive_and_stale_reviews_rejected(repo: CaseRepository, mutation: str, op: str) -> None:
    case_id, task, check, event = setup(repo)
    if op != "claim":
        send(repo, task, "claim")
    if op == "check":
        send(repo, task, "start")
    if mutation == "timeout":
        assert fail(repo, event)["recorded"]
    elif mutation == "attempt":
        put_case(repo, case_id, submissionAttempt=2)
    else:
        put_case(repo, case_id, status="APPROVED")
    before = rows(repo)
    assert (
        send(repo, task, op, check=check, payload={"result": "PASS"} if op == "check" else {})[0]
        == 409
    )
    assert rows(repo) == before


@pytest.mark.parametrize("op", ["claim", "start", "check"])
def test_failure_between_read_and_transaction_rolls_back(repo: CaseRepository, op: str) -> None:
    case_id, task, check, event = setup(repo)
    if op != "claim":
        send(repo, task, "claim")
    if op == "check":
        send(repo, task, "start")
    before_tasks = repo.related(case_id, "TASK#")
    before_checks = repo.related(case_id, "CHECK#")
    before_audits = [r for r in repo.related(case_id, "AUDIT#") if r["actorType"] == "USER"]
    original = repo.client.transact_write_items
    raced = False

    def race(**kwargs: Any) -> Any:
        nonlocal raced
        if not raced:
            raced = True
            fail(repo, event)
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        assert (
            send(repo, task, op, check=check, payload={"result": "PASS"} if op == "check" else {})[
                0
            ]
            == 409
        )
    closed = get_task(repo, task)
    assert closed["status"] == "COMPLETED" and closed["callbackStatus"] == "FAILED"
    assert closed["decision"] == before_tasks[0]["decision"]
    assert closed["reviewerId"] == before_tasks[0]["reviewerId"]
    assert repo.related(case_id, "CHECK#") == before_checks
    assert [r for r in repo.related(case_id, "AUDIT#") if r["actorType"] == "USER"] == before_audits


def test_concurrent_check_write_does_not_lose_winner(repo: CaseRepository) -> None:
    case_id, task, check, _ = setup(repo)
    send(repo, task, "claim")
    send(repo, task, "start")
    original = repo.client.transact_write_items
    raced = False

    def race(**kwargs: Any) -> Any:
        nonlocal raced
        if not raced:
            raced = True
            assert send(repo, task, "check", check=check, payload={"result": "FAIL"})[0] == 200
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        assert send(repo, task, "check", check=check, payload={"result": "PASS"})[0] == 409
    assert repo.related(case_id, "CHECK#")[0]["result"] == "FAIL"
    assert get_task(repo, task)["checkRevision"] == 1


def test_concurrent_start_creates_one_fact(repo: CaseRepository) -> None:
    case_id, task, _, _ = setup(repo)
    send(repo, task, "claim")
    original = repo.client.transact_write_items
    raced = False

    def race(**kwargs: Any) -> Any:
        nonlocal raced
        if not raced:
            raced = True
            assert send(repo, task, "start")[0] == 200
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        assert send(repo, task, "start")[0] == 409
    assert send(repo, task, "start")[0] == 200
    assert (
        len([r for r in repo.related(case_id, "OUTBOX#") if r["eventType"] == "ReviewStarted"]) == 1
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"result": "UNKNOWN"},
        {"result": []},
        {"result": True},
        {"result": "PASS", "comment": 1},
        {"result": "PASS", "comment": "x" * 2001},
        {"result": "PASS", "reviewerId": "carol"},
        {"result": "PASS", "taskToken": "forged"},
    ],
)
def test_invalid_check_body_has_no_effect(repo: CaseRepository, payload: dict[str, Any]) -> None:
    _, task, check, _ = setup(repo)
    before = rows(repo)
    assert send(repo, task, "check", check=check, payload=payload)[0] == 400
    assert rows(repo) == before


@pytest.mark.parametrize("result", ["NOT_REVIEWED", "PASS", "FAIL", "NOT_APPLICABLE"])
def test_all_check_results_and_comment_clear(repo: CaseRepository, result: str) -> None:
    case_id, task, check, _ = setup(repo)
    send(repo, task, "claim")
    send(repo, task, "start")
    assert (
        send(repo, task, "check", check=check, payload={"result": result, "comment": "x" * 2000})[0]
        == 200
    )
    assert send(repo, task, "check", check=check, payload={"result": result})[0] == 200
    assert repo.related(case_id, "CHECK#")[0]["comment"] is None
    assert get_task(repo, task)["checkRevision"] == 2


def test_missing_check_cannot_be_upserted_and_unstarted_cannot_update(repo: CaseRepository) -> None:
    case_id, task, check, _ = setup(repo)
    send(repo, task, "claim")
    assert send(repo, task, "check", check=check, payload={"result": "PASS"})[0] == 409
    send(repo, task, "start")
    before = rows(repo)
    assert send(repo, task, "check", check="unknown", payload={"result": "PASS"})[0] == 404
    assert send(repo, task, "check", check="../other", payload={"result": "PASS"})[0] == 400
    assert rows(repo) == before
    assert len(repo.related(case_id, "CHECK#")) == 5


def test_legacy_absent_owner_and_token_preservation(repo: CaseRepository) -> None:
    _, task, _, event = setup(repo)
    row = get_task(repo, task)
    del row["reviewerId"]
    repo.client.put_item(TableName=repo.table_name, Item=encode(row))
    assert send(repo, task, "claim")[0] == 200
    assert send(repo, task, "start")[0] == 200
    assert get_task(repo, task)["workflowTaskToken"] == event["taskToken"]


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({"body": "{"}, 400),
        ({"body": "[]"}, 400),
        ({"body": "x" * 32769}, 400),
        ({"body": "!", "isBase64Encoded": True}, 400),
        ({"body": "e30=", "isBase64Encoded": True}, 200),
        ({"queryStringParameters": {"actor": "carol"}}, 400),
        ({"requestContext": {}}, 401),
    ],
)
def test_http_boundaries(repo: CaseRepository, changes: dict[str, Any], expected: int) -> None:
    _, task, _, _ = setup(repo)
    assert send(repo, task, "claim", changes=changes)[0] == expected


def test_storage_failure_is_sanitized_and_atomic(repo: CaseRepository) -> None:
    _, task, _, event = setup(repo)
    before = rows(repo)
    with patch.object(
        repo.client,
        "transact_write_items",
        side_effect=ClientError(
            {"Error": {"Code": "InternalServerError", "Message": event["taskToken"]}},
            "TransactWriteItems",
        ),
    ):
        code, data = send(repo, task, "claim")
    assert code == 503 and event["taskToken"] not in str(data)
    assert rows(repo) == before
