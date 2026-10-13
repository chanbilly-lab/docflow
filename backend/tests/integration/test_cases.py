"""Local boto3/Moto integration of the Case HTTP boundary and atomic persistence."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import UUID

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from case_api.api import handle
from case_api.command import handler as command_handler
from case_api.query import handler as query_handler
from common.cases.repository import CaseRepository
from common.templates.repository import TemplateRepository, decode, encode
from common.templates.seed import SUPPLIER_ONBOARDING as SEED

ROOT = Path(__file__).resolve().parents[3]
API = json.loads((ROOT / "docs/api/openapi.yaml").read_text())
EVENT = json.loads((ROOT / "docs/events/case-created.schema.json").read_text())


def event(route: str, *, actor: str = "alice", groups: Any = None, **kwargs: Any) -> dict[str, Any]:
    return {
        "routeKey": route,
        "headers": {"x-correlation-id": "test-correlation"},
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": actor,
                        "token_use": "access",
                        "cognito:groups": groups if groups is not None else ["requester"],
                    }
                }
            }
        },
        **kwargs,
    }


def request(repo: CaseRepository, route: str, **kwargs: Any) -> tuple[int, dict[str, Any]]:
    response = handle(
        event(route, **kwargs), "command" if route.startswith("POST") else "query", repo
    )
    assert response["headers"]["cache-control"] == "no-store"
    return response["statusCode"], json.loads(response["body"])


def create(repo: CaseRepository, actor: str = "alice") -> dict[str, Any]:
    status, body = request(
        repo,
        "POST /api/v1/cases",
        actor=actor,
        body=json.dumps({"caseType": "SUPPLIER_ONBOARDING"}),
    )
    assert status == 201
    validate(body, "CreateCaseResponse")
    return body


def validate(body: dict[str, Any], schema: str) -> None:
    Draft202012Validator(
        {"$ref": f"#/components/schemas/{schema}", "components": API["components"]}
    ).validate(body)


def partition(repo: CaseRepository, case_id: str) -> list[dict[str, Any]]:
    response = repo.client.query(
        TableName=repo.table_name,
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues=encode({":pk": f"CASE#{case_id}"}),
    )
    return [decode(row) for row in response["Items"]]


def test_create_keys_audit_event_and_template_binding(repo: CaseRepository) -> None:
    case = create(repo)
    stored = repo.get(case["caseId"])
    assert stored["PK"] == f"CASE#{case['caseId']}" and stored["SK"] == "CASE"
    assert stored["GSI1PK"] == "REQUESTER#alice"
    assert stored["GSI1SK"] == f"CASE#{stored['createdAt']}#{case['caseId']}"
    assert stored["GSI2PK"] == "CASE_STATUS#DRAFT"
    assert stored["GSI2SK"] == f"UPDATED#{stored['updatedAt']}#{case['caseId']}"
    assert stored["submissionAttempt"] == 0 and stored["version"] == 1
    rows = partition(repo, case["caseId"])
    assert len(rows) == 3
    audit = next(row for row in rows if row["entityType"] == "AUDIT")
    assert audit["action"] == "CASE_CREATED" and audit["correlationId"] == "test-correlation"
    outbox = next(row for row in rows if row["entityType"] == "OUTBOX")
    assert outbox["status"] == "PENDING" and "expiresAtEpoch" not in outbox
    assert outbox["eventType"] == "CaseCreated" and outbox["source"] == "docflow.case"
    Draft202012Validator(EVENT, format_checker=FormatChecker()).validate(
        json.loads(json.dumps(outbox["detail"], default=int))
    )
    TemplateRepository(repo.client, repo.table_name).publish(
        replace(SEED, version=2), actor_id="seed"
    )
    assert create(repo)["checklistTemplate"]["version"] == 2
    assert repo.get(case["caseId"])["checklistTemplateVersion"] == 1


def test_atomic_failure_does_not_leave_case_or_audit(repo: CaseRepository) -> None:
    ids = [UUID(int=n) for n in (1, 2, 3)]
    case_id = f"c_{ids[0].hex}"
    repo.client.put_item(
        TableName=repo.table_name,
        Item=encode(
            {
                "PK": f"CASE#{case_id}",
                "SK": f"OUTBOX#evt_{ids[1].hex}",
                "sentinel": "preserve",
            }
        ),
    )
    with patch("common.cases.repository.uuid4", side_effect=ids):
        status, body = request(
            repo, "POST /api/v1/cases", body=json.dumps({"caseType": SEED.case_type})
        )
    assert status == 503
    validate(body, "Error")
    rows = partition(repo, case_id)
    assert len(rows) == 1 and rows[0]["sentinel"] == "preserve"


def test_requester_pagination_and_cursor_scope(repo: CaseRepository) -> None:
    own = {create(repo)["caseId"] for _ in range(3)}
    create(repo, "bob")
    seen: set[str] = set()
    cursor = None
    first_cursor = None
    while True:
        query = {"limit": "1", **({"cursor": cursor} if cursor else {})}
        status, body = request(repo, "GET /api/v1/cases", queryStringParameters=query)
        assert status == 200
        validate(body, "CaseList")
        assert len(body["items"]) <= 1
        seen.update(item["caseId"] for item in body["items"])
        cursor = body["nextCursor"]
        first_cursor = first_cursor or cursor
        if cursor is None:
            break
    assert seen == own
    status, _ = request(
        repo, "GET /api/v1/cases", actor="bob", queryStringParameters={"cursor": first_cursor}
    )
    assert status == 400


def test_empty_filtered_page_keeps_continuation_and_admin_index(repo: CaseRepository) -> None:
    older = create(repo)
    newer = create(repo)
    row = repo.get(newer["caseId"])
    row["status"], row["GSI2PK"] = "REVIEW_PENDING", "CASE_STATUS#REVIEW_PENDING"
    repo.client.put_item(TableName=repo.table_name, Item=encode(row))
    _, page = request(
        repo, "GET /api/v1/cases", queryStringParameters={"status": "DRAFT", "limit": "1"}
    )
    assert page["items"] == [] and page["nextCursor"]
    _, page2 = request(
        repo,
        "GET /api/v1/cases",
        queryStringParameters={"status": "DRAFT", "limit": "1", "cursor": page["nextCursor"]},
    )
    assert page2["items"][0]["caseId"] == older["caseId"]
    status, admin = request(
        repo,
        "GET /api/v1/cases",
        actor="admin",
        groups=["admin"],
        queryStringParameters={"owner": "all", "status": "REVIEW_PENDING"},
    )
    assert status == 200 and admin["items"][0]["caseId"] == newer["caseId"]


def test_detail_and_activity_hide_nested_internal_fields(repo: CaseRepository) -> None:
    case = create(repo)
    pk = f"CASE#{case['caseId']}"
    row = repo.get(case["caseId"])
    row["workflowTaskToken"] = "secret-sentinel"
    row["requestedInformation"] = [
        {
            "documentType": "ADDRESS_PROOF",
            "message": "Please upload",
            "reasonCode": "MISSING",
            "workflowTaskToken": "secret-sentinel",
        }
    ]
    repo.client.put_item(TableName=repo.table_name, Item=encode(row))
    related_items: list[dict[str, Any]] = [
        {
            "PK": pk,
            "SK": "DOC#d_test",
            "documentId": "d_test",
            "documentType": "DIRECTOR_ID",
            "s3Key": "secret-sentinel",
            "metadata": {"token": "secret-sentinel"},
        },
        {
            "PK": pk,
            "SK": "TASK#t_test",
            "taskId": "t_test",
            "attempt": 1,
            "reviewerId": "reviewer",
            "workflowTaskToken": "secret-sentinel",
            "callbackState": {"token": "secret-sentinel"},
        },
    ]
    for item in related_items:
        repo.client.put_item(TableName=repo.table_name, Item=encode(item))
    status, detail = request(
        repo, "GET /api/v1/cases/{caseId}", pathParameters={"caseId": case["caseId"]}
    )
    assert status == 200
    validate(detail, "CaseDetail")
    assert detail["documents"][0]["documentId"] == "d_test"
    assert detail["review"]["currentTask"]["taskId"] == "t_test"
    assert "secret-sentinel" not in json.dumps(detail)
    assert "PK" not in json.dumps(detail)
    status, activity = request(
        repo, "GET /api/v1/cases/{caseId}/activity", pathParameters={"caseId": case["caseId"]}
    )
    assert status == 200
    validate(activity, "ActivityPage")
    assert set(activity["items"][0]) == {"action", "actorType", "timestamp"}
    status, _ = request(
        repo,
        "GET /api/v1/cases/{caseId}",
        actor="reviewer",
        groups=["reviewer"],
        pathParameters={"caseId": case["caseId"]},
    )
    assert status == 200


@pytest.mark.parametrize(
    "route", ["GET /api/v1/cases/{caseId}", "GET /api/v1/cases/{caseId}/activity"]
)
def test_other_requester_cannot_read(repo: CaseRepository, route: str) -> None:
    case = create(repo)
    status, body = request(repo, route, actor="bob", pathParameters={"caseId": case["caseId"]})
    assert status == 404
    validate(body, "Error")


@pytest.mark.parametrize(
    "body",
    [
        "null",
        "[]",
        "{}",
        '{"caseType":[]}',
        '{"caseType":"UNKNOWN"}',
        '{"caseType":"SUPPLIER_ONBOARDING","requesterId":"bob"}',
    ],
)
def test_invalid_create_inputs(repo: CaseRepository, body: str) -> None:
    status, result = request(repo, "POST /api/v1/cases", body=body)
    assert status == 400
    validate(result, "Error")


@pytest.mark.parametrize(
    "query",
    [
        {"limit": "0"},
        {"limit": "101"},
        {"status": "UNKNOWN"},
        {"cursor": "bad"},
        {"owner": "all"},
        {"owner": "bob"},
        {"unexpected": "value"},
    ],
)
def test_invalid_or_forbidden_list_inputs(repo: CaseRepository, query: dict[str, str]) -> None:
    status, result = request(repo, "GET /api/v1/cases", queryStringParameters=query)
    assert status in {400, 403}
    validate(result, "Error")


def test_untrusted_headers_and_role_restrictions(repo: CaseRepository) -> None:
    response = handle(
        {"routeKey": "GET /api/v1/cases", "headers": {"authorization": "Bearer forged"}},
        "query",
        repo,
    )
    assert response["statusCode"] == 401
    status, _ = request(
        repo,
        "POST /api/v1/cases",
        groups=["reviewer"],
        body=json.dumps({"caseType": SEED.case_type}),
    )
    assert status == 403
    status, _ = request(repo, "GET /api/v1/cases", groups=[])
    assert status == 403


def test_real_entry_points_use_environment_and_preserve_health(repo: CaseRepository) -> None:
    with (
        patch("case_api.api.boto3.client", return_value=repo.client),
        patch.dict("os.environ", {"TABLE_NAME": repo.table_name}),
    ):
        response = command_handler(
            event("POST /api/v1/cases", body=json.dumps({"caseType": SEED.case_type})), None
        )
        assert response["statusCode"] == 201
        assert query_handler(event("GET /api/v1/cases"), None)["statusCode"] == 200
        assert query_handler(event("GET /api/v1/health"), None)["statusCode"] == 200


def test_activity_pagination_is_case_scoped(repo: CaseRepository) -> None:
    case = create(repo)
    for number in (1, 2):
        repo.client.put_item(
            TableName=repo.table_name,
            Item=encode(
                {
                    "PK": f"CASE#{case['caseId']}",
                    "SK": f"AUDIT#2026-09-16T00:00:00.00000{number}Z#a_extra{number}",
                    "action": "CASE_CREATED",
                    "actorType": "USER",
                    "timestamp": f"2026-09-16T00:00:00.00000{number}Z",
                    "private": "secret-sentinel",
                }
            ),
        )
    cursor = None
    first_cursor = None
    count = 0
    while True:
        query = {"limit": "1", **({"cursor": cursor} if cursor else {})}
        status, body = request(
            repo,
            "GET /api/v1/cases/{caseId}/activity",
            pathParameters={"caseId": case["caseId"]},
            queryStringParameters=query,
        )
        assert status == 200
        validate(body, "ActivityPage")
        count += len(body["items"])
        assert "secret-sentinel" not in json.dumps(body)
        cursor = body["nextCursor"]
        first_cursor = first_cursor or cursor
        if cursor is None:
            break
    assert count == 3
    another = create(repo)
    status, _ = request(
        repo,
        "GET /api/v1/cases/{caseId}/activity",
        pathParameters={"caseId": another["caseId"]},
        queryStringParameters={"cursor": first_cursor},
    )
    assert status == 400


def test_missing_template_creates_no_case(repo: CaseRepository) -> None:
    repo.client.delete_item(
        TableName=repo.table_name,
        Key=encode({"PK": "TEMPLATE#supplier-onboarding", "SK": "VERSION#1"}),
    )
    status, body = request(
        repo, "POST /api/v1/cases", body=json.dumps({"caseType": SEED.case_type})
    )
    assert status == 503 and body["error"]["code"] == "TEMPLATE_UNAVAILABLE"
    assert request(repo, "GET /api/v1/cases")[1]["items"] == []


def test_schema_definitions_are_valid() -> None:
    Draft202012Validator.check_schema(EVENT)
    for schema in API["components"]["schemas"].values():
        Draft202012Validator.check_schema(schema)


# TASK-006: exercise authorization through the real HTTP boundary and repository.
READ_ROUTES = ("GET /api/v1/cases/{caseId}", "GET /api/v1/cases/{caseId}/activity")


def assign(repo: CaseRepository, case_id: str, reviewer: str | None) -> None:
    repo.client.put_item(
        TableName=repo.table_name,
        Item=encode(
            {
                "PK": f"CASE#{case_id}",
                "SK": "TASK#t_assignment",
                "taskId": "t_assignment",
                "attempt": 1,
                "reviewerId": reviewer,
                "internalComments": "private-review-note",
                "workflowTaskToken": "private-workflow-placeholder",
            }
        ),
    )


@pytest.mark.parametrize("route", READ_ROUTES)
@pytest.mark.parametrize(
    "actor,groups,expected",
    [
        ("alice", ["requester"], 200),
        ("bob", ["requester"], 404),
        ("assigned", ["reviewer"], 200),
        ("unassigned", ["reviewer"], 404),
        ("alice", ["reviewer"], 404),
        ("assigned", ["requester"], 404),
        ("operator", ["admin"], 200),
        ("bob", ["requester", "reviewer"], 404),
        ("assigned", ["requester", "reviewer"], 200),
        ("operator", ["reviewer", "admin"], 200),
    ],
)
def test_read_authorization_matrix(
    repo: CaseRepository, route: str, actor: str, groups: list[str], expected: int
) -> None:
    case_id = create(repo)["caseId"]
    assign(repo, case_id, "assigned")
    # Assignment on another partition cannot authorize this Case.
    other = create(repo, "bob")["caseId"]
    assign(repo, other, "unassigned")
    status, body = request(
        repo, route, actor=actor, groups=groups, pathParameters={"caseId": case_id}
    )
    assert status == expected
    validate(
        body,
        "Error"
        if expected == 404
        else ("ActivityPage" if route.endswith("/activity") else "CaseDetail"),
    )
    assert "private-review-note" not in json.dumps(body)
    assert "private-workflow-placeholder" not in json.dumps(body)
    if expected == 404:
        missing = request(
            repo,
            route,
            actor=actor,
            groups=groups,
            pathParameters={"caseId": "c_missing"},
        )
        assert (status, body) == missing


@pytest.mark.parametrize("route", READ_ROUTES)
def test_assignment_is_checked_on_each_request(repo: CaseRepository, route: str) -> None:
    case_id = create(repo)["caseId"]
    options = {"actor": "reviewer", "groups": ["reviewer"], "pathParameters": {"caseId": case_id}}
    assert request(repo, route, **options)[0] == 404
    assign(repo, case_id, "reviewer")
    assert request(repo, route, **options)[0] == 200
    assign(repo, case_id, None)
    assert request(repo, route, **options)[0] == 404
    assign(repo, case_id, "replacement")
    assert request(repo, route, **options)[0] == 404


@pytest.mark.parametrize(
    "groups,expected",
    [
        (["requester"], 201),
        (["admin"], 201),
        (["reviewer"], 403),
        (["requester", "reviewer"], 201),
        ([], 403),
        (["superadmin"], 403),
    ],
)
def test_create_role_matrix_and_denied_writes(
    repo: CaseRepository, groups: list[str], expected: int
) -> None:
    before = repo.client.scan(TableName=repo.table_name)["Items"]
    status, body = request(
        repo,
        "POST /api/v1/cases",
        actor="caller",
        groups=groups,
        headers={"x-user-id": "victim", "x-role": "admin"},
        body=json.dumps({"caseType": SEED.case_type}),
    )
    assert status == expected
    if expected == 201:
        rows = partition(repo, body["caseId"])
        case = repo.get(body["caseId"])
        assert case["requesterId"] == "caller"
        assert case["GSI1PK"] == "REQUESTER#caller"
        assert next(r for r in rows if r["entityType"] == "AUDIT")["actorId"] == "caller"
        fact = next(r for r in rows if r["entityType"] == "OUTBOX")["detail"]
        assert fact["actor"]["id"] == fact["data"]["requesterId"] == "caller"
    else:
        validate(body, "Error")
        assert body["error"]["code"] == "FORBIDDEN"
        assert repo.client.scan(TableName=repo.table_name)["Items"] == before


@pytest.mark.parametrize(
    "groups,owner,expected",
    [
        (["requester"], "mine", 200),
        (["requester"], "all", 403),
        (["reviewer"], "mine", 403),
        (["reviewer"], "all", 403),
        (["admin"], "mine", 200),
        (["admin"], "all", 200),
    ],
)
def test_list_role_matrix(
    repo: CaseRepository, groups: list[str], owner: str, expected: int
) -> None:
    own = create(repo, "caller")["caseId"]
    other = create(repo, "victim")["caseId"]
    status, body = request(
        repo,
        "GET /api/v1/cases",
        actor="caller",
        groups=groups,
        queryStringParameters={"owner": owner, "status": "DRAFT"},
    )
    assert status == expected
    if expected == 200:
        assert {row["caseId"] for row in body["items"]} == (
            {own, other} if owner == "all" else {own}
        )
        validate(body, "CaseList")
    else:
        assert body["error"]["code"] == "FORBIDDEN"


@pytest.mark.parametrize("route", READ_ROUTES)
def test_identity_headers_and_query_overrides_cannot_grant_access(
    repo: CaseRepository, route: str
) -> None:
    case_id = create(repo, "victim")["caseId"]
    spoofed = {
        "Authorization": "Bearer not-a-real-token",
        "x-user-id": "victim",
        "x-role": "admin",
        "cognito:groups": "admin",
    }
    status, _ = request(
        repo, route, actor="attacker", headers=spoofed, pathParameters={"caseId": case_id}
    )
    assert status == 404
    status, _ = request(
        repo,
        route,
        actor="attacker",
        pathParameters={"caseId": case_id},
        queryStringParameters={"requesterId": "victim", "role": "admin"},
    )
    assert status == 400


@pytest.mark.parametrize(
    "claims,expected",
    [
        ({}, 401),
        ({"sub": "caller", "token_use": "id", "cognito:groups": ["admin"]}, 401),
        ({"sub": "", "token_use": "access", "cognito:groups": ["admin"]}, 401),
        ({"sub": "caller", "token_use": "access"}, 403),
        ({"sub": "caller", "token_use": "access", "cognito:groups": "superadmin"}, 403),
        ({"sub": "caller", "token_use": "access", "cognito:groups": {"admin": True}}, 403),
        ({"sub": "caller", "token_use": "access", "cognito:groups": ["admin", 1]}, 403),
    ],
)
def test_untrusted_or_insufficient_claims_do_not_reach_storage(
    claims: dict[str, Any], expected: int
) -> None:
    incoming = event("POST /api/v1/cases", body=json.dumps({"caseType": SEED.case_type}))
    incoming["requestContext"]["authorizer"]["jwt"]["claims"] = claims
    incoming["headers"]["x-role"] = "admin"
    with patch("case_api.api.boto3.client") as client:
        response = handle(incoming, "command")
        client.assert_not_called()
    assert response["statusCode"] == expected
    validate(json.loads(response["body"]), "Error")


@pytest.mark.parametrize(
    "groups", ["requester", '["requester","reviewer"]', "[requester reviewer]"]
)
def test_supported_authorizer_group_strings(repo: CaseRepository, groups: str) -> None:
    own = create(repo)["caseId"]
    create(repo, "bob")
    status, body = request(repo, "GET /api/v1/cases", groups=groups)
    assert status == 200 and [row["caseId"] for row in body["items"]] == [own]
    assert (
        request(
            repo,
            "GET /api/v1/cases",
            groups=groups,
            queryStringParameters={"owner": "all", "status": "DRAFT"},
        )[0]
        == 403
    )


def test_forged_cursor_cannot_select_another_requester_partition(repo: CaseRepository) -> None:
    import base64
    import hashlib

    own = {create(repo)["caseId"] for _ in range(2)}
    victim = create(repo, "victim")["caseId"]
    # Recompute the public fingerprint: cursor integrity is not the auth boundary.
    foreign = repo.get(victim)
    cursor = base64.urlsafe_b64encode(
        json.dumps(
            {
                "position": f"{foreign['createdAt']}#{victim}",
                "scope": hashlib.sha256(json.dumps(["alice", "mine", None]).encode()).hexdigest(),
            }
        ).encode()
    ).decode()
    with patch.object(repo.client, "query", wraps=repo.client.query) as query:
        status, body = request(repo, "GET /api/v1/cases", queryStringParameters={"cursor": cursor})
    assert status == 200
    assert {row["caseId"] for row in body["items"]} <= own
    args = query.call_args.kwargs
    assert decode(args["ExpressionAttributeValues"])[":pk"] == "REQUESTER#alice"
    assert decode(args["ExclusiveStartKey"])["GSI1PK"] == "REQUESTER#alice"


@pytest.mark.parametrize("route", READ_ROUTES)
def test_denied_reads_do_not_load_detail_or_activity(repo: CaseRepository, route: str) -> None:
    case_id = create(repo)["caseId"]
    with (
        patch.object(repo, "detail", wraps=repo.detail) as detail,
        patch.object(repo, "activity", wraps=repo.activity) as activity,
    ):
        status, _ = request(repo, route, actor="bob", pathParameters={"caseId": case_id})
        assert status == 404
        detail.assert_not_called()
        activity.assert_not_called()
