"""Review persistence, retry boundaries, authorization and public contracts."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from jsonschema import Draft202012Validator
from test_submission import put_case, rows
from test_workflow import accepted

from common.cases.repository import CaseRepository
from common.cases.workflow_state import fail, validate
from common.reviews.creation import create_review
from common.reviews.query import get_task
from common.templates.models import Check
from common.templates.repository import TemplateRepository, encode
from common.templates.seed import SUPPLIER_ONBOARDING as SEED
from review_api.query import handle
from workflow_create_review_task.handler import handler

ROOT = Path(__file__).resolve().parents[3]


def prepared(repo: CaseRepository) -> tuple[str, dict[str, Any]]:
    case_id, event = accepted(repo)
    assert validate(repo, event)["valid"]
    return case_id, {
        **event,
        "taskToken": str(uuid4()),
        "enteredTime": datetime.now(UTC).isoformat(),
        "retryCount": 0,
    }


def request(
    repo: CaseRepository,
    task: str | None = None,
    *,
    actor: str = "bob",
    groups: list[str] | None = None,
    **params: str,
) -> dict[str, Any]:
    return handle(
        {
            "routeKey": "GET /api/v1/reviews" + ("/{taskId}" if task else ""),
            "pathParameters": {"taskId": task},
            "queryStringParameters": params,
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
        },
        repo,
    )


def body(result: dict[str, Any]) -> dict[str, Any]:
    assert result["statusCode"] == 200
    assert result["headers"]["cache-control"] == "no-store"
    data: dict[str, Any] = json.loads(result["body"])
    return data


def assign(repo: CaseRepository, identifier: str, actor: str, state: str = "IN_PROGRESS") -> None:
    task = get_task(repo, identifier)
    task.update(
        reviewerId=actor,
        status=state,
        GSI1PK="REVIEWER#" + actor,
        GSI1SK=f"TASK#{state}#DUE#{task['dueAt']}#{identifier}",
    )
    repo.client.put_item(TableName=repo.table_name, Item=encode(task))


def test_publish_atomic_public_contract(repo: CaseRepository) -> None:
    case_id, event = prepared(repo)
    identifier = create_review(repo, event)["taskId"]
    task = get_task(repo, identifier)
    assert identifier == f"t_{case_id}_1"
    assert repo.get(case_id)["status"] == "REVIEW_PENDING"
    assert task["workflowTaskToken"] == event["taskToken"]
    assert datetime.fromisoformat(task["dueAt"]) == (
        datetime.fromisoformat(repo.get(case_id)["workflowSubmittedAt"]) + timedelta(hours=48)
    )
    data = body(request(repo, identifier))
    assert len(data["checks"]) == len(SEED.checks)
    assert len(data["documents"]) == len(SEED.required_documents)
    assert all(c["result"] == "NOT_REVIEWED" and c["comment"] is None for c in data["checks"])
    assert [c["instructions"] for c in data["checks"]] == [c.instructions for c in SEED.checks]
    assert body(request(repo))["items"] == [data["task"]]
    api = json.loads((ROOT / "docs/api/openapi.yaml").read_text())
    for schema, value in [("ReviewDetail", data), ("ReviewQueue", body(request(repo)))]:
        Draft202012Validator(
            {"$ref": "#/components/schemas/" + schema, "components": api["components"]}
        ).validate(value)
    exposed = json.dumps(data) + json.dumps(body(request(repo)))
    for private in [
        event["taskToken"],
        "workflowTaskToken",
        "callbackGeneration",
        "workflowExecutionArn",
        "s3Key",
        '"PK"',
        '"SK"',
    ]:
        assert private not in exposed
    facts = [r for r in rows(repo) if r.get("eventType") == "CaseReadyForReview"]
    assert len(facts) == 1
    assert event["taskToken"] not in str(facts)
    assert len([r for r in rows(repo) if r.get("action") == "CASE_READY_FOR_REVIEW"]) == 1


def test_duplicate_and_token_rotation_preserve_findings(repo: CaseRepository) -> None:
    case_id, event = prepared(repo)
    identifier = create_review(repo, event)["taskId"]
    check = repo.related(case_id, "CHECK#")[0]
    check.update(result="PASS", comment="Reviewed", updatedBy="bob")
    repo.client.put_item(TableName=repo.table_name, Item=encode(check))
    before = rows(repo)
    assert create_review(repo, event) == {"taskId": identifier}
    assert rows(repo) == before
    newer = {**event, "taskToken": str(uuid4()), "retryCount": 1}
    create_review(repo, newer)
    create_review(repo, event)
    assert get_task(repo, identifier)["workflowTaskToken"] == newer["taskToken"]
    assert repo.related(case_id, "CHECK#")[0] == check
    assert len([r for r in rows(repo) if r.get("eventType") == "CaseReadyForReview"]) == 1
    assert len([r for r in rows(repo) if r.get("action") == "REVIEW_CALLBACK_REFRESHED"]) == 1
    with pytest.raises(ValueError, match="generation conflict"):
        create_review(repo, {**newer, "taskToken": str(uuid4())})


def test_new_entry_time_with_reset_retry_rotates(repo: CaseRepository) -> None:
    _, event = prepared(repo)
    identifier = create_review(repo, {**event, "retryCount": 3})["taskId"]
    newer = {
        **event,
        "enteredTime": (
            datetime.fromisoformat(event["enteredTime"]) + timedelta(minutes=1)
        ).isoformat(),
        "taskToken": str(uuid4()),
    }
    create_review(repo, newer)
    assert get_task(repo, identifier)["workflowTaskToken"] == newer["taskToken"]


def test_preparation_crash_is_invisible_and_retryable(repo: CaseRepository) -> None:
    case_id, event = prepared(repo)
    original = repo.client.transact_write_items
    calls = 0

    def crash(**kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("outage")
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=crash):
        with pytest.raises(RuntimeError):
            create_review(repo, event)
    assert repo.get(case_id)["status"] == "PROCESSING"
    assert len(repo.related(case_id, "CHECK#")) == len(SEED.checks)
    assert repo.related(case_id, "TASK#") == []
    assert body(request(repo))["items"] == []
    assert request(repo, f"t_{case_id}_1")["statusCode"] == 404
    create_review(repo, event)
    assert len(body(request(repo))["items"]) == 1


def test_final_publish_race_rolls_back(repo: CaseRepository) -> None:
    case_id, event = prepared(repo)
    original = repo.client.transact_write_items

    def race(**kwargs: Any) -> Any:
        if "Update" in kwargs["TransactItems"][0]:
            put_case(repo, case_id, version=99)
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=race):
        with pytest.raises(ClientError):
            create_review(repo, event)
    assert repo.related(case_id, "TASK#") == []
    assert not any(r.get("eventType") == "CaseReadyForReview" for r in rows(repo))
    assert repo.get(case_id)["status"] == "PROCESSING"
    create_review(repo, event)
    assert repo.get(case_id)["status"] == "REVIEW_PENDING"


def test_maximum_98_checks_and_bound_version(repo: CaseRepository) -> None:
    checks = tuple(
        Check(f"check_{i}", i, SEED.required_documents[0], True, "Inspect") for i in range(1, 99)
    )
    TemplateRepository(repo.client, repo.table_name).publish(
        replace(SEED, version=2, checks=checks), actor_id="seed"
    )
    case_id, event = prepared(repo)
    TemplateRepository(repo.client, repo.table_name).publish(
        replace(SEED, version=3), actor_id="seed"
    )
    with patch.object(
        repo.client, "transact_write_items", wraps=repo.client.transact_write_items
    ) as writes:
        create_review(repo, event)
    assert [len(c.kwargs["TransactItems"]) for c in writes.call_args_list] == [99, 4]
    assert len(repo.related(case_id, "CHECK#")) == 98
    assert repo.get(case_id)["checklistTemplateVersion"] == 2


@pytest.mark.parametrize("change", ["attempt", "execution", "revision", "state", "token", "retry"])
def test_invalid_creation_fails_closed(repo: CaseRepository, change: str) -> None:
    case_id, event = prepared(repo)
    if change == "attempt":
        event["submission"] = {**event["submission"], "attempt": 2}
    elif change == "execution":
        event["executionArn"] += "wrong"
    elif change == "revision":
        put_case(repo, case_id, documentRevision=99)
    elif change == "state":
        put_case(repo, case_id, status="APPROVED")
    elif change == "token":
        event["taskToken"] = ""
    else:
        event["retryCount"] = True
    before = rows(repo)
    with pytest.raises(ValueError):
        create_review(repo, event)
    assert rows(repo) == before


def test_reviewer_authorization_and_assignment(repo: CaseRepository) -> None:
    _, event = prepared(repo)
    identifier = create_review(repo, event)["taskId"]
    assert request(repo, identifier, groups=["requester"])["statusCode"] == 403
    assert request(repo, groups=["requester"])["statusCode"] == 403
    assert handle({}, repo)["statusCode"] == 401
    assert request(repo, identifier, groups=["admin"])["statusCode"] == 200
    assign(repo, identifier, "bob")
    assert body(request(repo))["items"] == []
    assert len(body(request(repo, scope="mine", status="IN_PROGRESS"))["items"]) == 1
    assert body(request(repo, actor="carol", scope="mine"))["items"] == []
    assert request(repo, identifier, actor="carol")["statusCode"] == 404
    assert request(repo, identifier)["statusCode"] == 200
    assert request(repo, identifier, actor="carol", groups=["admin"])["statusCode"] == 200


def test_pagination_is_scope_bound_without_scans(repo: CaseRepository) -> None:
    _, event = prepared(repo)
    create_review(repo, event)
    # A second genuine submission requires a different idempotency key.
    with patch("test_workflow.KEY", str(uuid4())):
        _, second = prepared(repo)
    create_review(repo, second)
    with patch.object(repo.client, "scan", side_effect=AssertionError("No scan")):
        first = body(request(repo, limit="1"))
        assert len(first["items"]) == 1 and first["nextCursor"]
        last = body(request(repo, limit="1", cursor=first["nextCursor"]))
        assert len(last["items"]) == 1
        assert last["items"][0]["taskId"] != first["items"][0]["taskId"]
        assert request(repo, actor="carol", cursor=first["nextCursor"])["statusCode"] == 400
        assert request(repo, scope="mine", cursor=first["nextCursor"])["statusCode"] == 400


@pytest.mark.parametrize(
    "params",
    [
        {"scope": "all"},
        {"status": "APPROVED"},
        {"status": "IN_PROGRESS"},
        {"limit": "0"},
        {"limit": "101"},
        {"cursor": "bad"},
        {"extra": "x"},
    ],
)
def test_invalid_queue_query(repo: CaseRepository, params: dict[str, Any]) -> None:
    assert request(repo, **params)["statusCode"] == 400


def test_stale_index_owner_and_failed_case_hidden(repo: CaseRepository) -> None:
    _, event = prepared(repo)
    identifier = create_review(repo, event)["taskId"]
    stale = get_task(repo, identifier)
    assign(repo, identifier, "carol")
    original = repo.client.query

    def query(**kwargs: Any) -> Any:
        if kwargs.get("IndexName") == "GSI1":
            return {"Items": [encode(stale)]}
        return original(**kwargs)

    with patch.object(repo.client, "query", side_effect=query):
        assert body(request(repo))["items"] == []
        assert body(request(repo, scope="mine"))["items"] == []
    assert fail(repo, event) == {"recorded": True}
    assert body(request(repo, actor="carol", scope="mine"))["items"] == []


def test_callback_timeout_hides_available_task(repo: CaseRepository) -> None:
    case_id, event = prepared(repo)
    identifier = create_review(repo, event)["taskId"]
    assert fail(repo, event) == {"recorded": True}
    assert repo.get(case_id)["status"] == "WORKFLOW_FAILED"
    assert body(request(repo))["items"] == []
    assert request(repo, identifier)["statusCode"] == 404
    assert fail(repo, event) == {"recorded": False}


def test_worker_sanitizes_private_errors(repo: CaseRepository) -> None:
    _, event = prepared(repo)
    with (
        patch.dict("os.environ", {"TABLE_NAME": repo.table_name}),
        patch(
            "workflow_create_review_task.handler.create_review",
            side_effect=RuntimeError(event["taskToken"]),
        ),
    ):
        with pytest.raises(RuntimeError, match="^Review task creation failed$") as exc:
            handler(event, None)
    assert event["taskToken"] not in str(exc.value)


def test_concurrent_creation_has_one_publication(repo: CaseRepository) -> None:
    case_id, event = prepared(repo)
    original = repo.client.transact_write_items
    raced = False

    def interleave(**kwargs: Any) -> Any:
        nonlocal raced
        if not raced:
            raced = True
            create_review(repo, event)
        return original(**kwargs)

    with patch.object(repo.client, "transact_write_items", side_effect=interleave):
        with pytest.raises(ClientError):
            create_review(repo, event)
    create_review(repo, event)
    assert len(repo.related(case_id, "TASK#")) == 1
    assert len(repo.related(case_id, "CHECK#")) == len(SEED.checks)
    assert len([r for r in rows(repo) if r.get("eventType") == "CaseReadyForReview"]) == 1


def test_completed_assigned_history_remains_queryable(repo: CaseRepository) -> None:
    case_id, event = prepared(repo)
    identifier = create_review(repo, event)["taskId"]
    assign(repo, identifier, "bob", "COMPLETED")
    put_case(repo, case_id, status="APPROVED")
    assert len(body(request(repo, scope="mine", status="COMPLETED"))["items"]) == 1
    assert request(repo, identifier)["statusCode"] == 200
    assert request(repo, identifier, actor="carol")["statusCode"] == 404


def test_case_endpoint_does_not_grant_available_review_access(repo: CaseRepository) -> None:
    from case_api.api import handle as cases

    case_id, event = prepared(repo)
    create_review(repo, event)
    response = cases(
        {
            "routeKey": "GET /api/v1/cases/{caseId}",
            "pathParameters": {"caseId": case_id},
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "sub": "bob",
                            "token_use": "access",
                            "cognito:groups": ["reviewer"],
                        }
                    }
                }
            },
        },
        "query",
        repo,
    )
    assert response["statusCode"] == 404
