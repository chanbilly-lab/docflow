"""Production telemetry and recovery over Moto; no cloud writes."""

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from test_document_processor import setup as documents
from test_outbox_publisher import setup as outbox

from common.cases.repository import CaseRepository
from common.logging import REQUEST, emit, observed
from common.templates.repository import decode, encode
from operations_monitor.handler import snapshot


def lines(capsys: Any) -> list[dict[str, Any]]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines()]


def test_log_allowlist_and_context_reset(capsys: Any) -> None:
    @observed("test-service")
    def invoke(event: dict[str, Any], context: object) -> dict[str, Any]:
        emit("test-service", "Inside", fields=event, metrics={"CasesCreated": 1, "caseId": 42})
        return {"statusCode": 503, "headers": {"x-correlation-id": "corr_request"}}

    invoke(
        {"caseId": "c_safe", "taskToken": "secret", "correlationId": "bad\nsecret"},
        SimpleNamespace(aws_request_id="request_1"),
    )
    logs = lines(capsys)
    assert logs[0]["requestId"] == "request_1" and logs[0]["correlationId"] is None
    assert logs[0]["_aws"]["CloudWatchMetrics"][0]["Dimensions"] == [["service"]]
    assert logs[0]["caseId"] == "c_safe" and "secret" not in json.dumps(logs)
    assert logs[1]["level"] == "ERROR" and logs[1]["correlationId"] == "corr_request"
    assert REQUEST.get() is None
    invoke({}, object())
    assert lines(capsys)[0]["requestId"] is None


def test_exception_logging_never_contains_exception(capsys: Any) -> None:
    @observed("test-service")
    def invoke(event: dict[str, Any], context: object) -> None:
        raise ValueError("token=private")

    with pytest.raises(ValueError):
        invoke({"body": "secret"}, object())
    assert "private" not in json.dumps(lines(capsys))
    assert REQUEST.get() is None


def test_document_upload_correlation_reaches_audit_and_outbox(
    repo: CaseRepository, capsys: Any
) -> None:
    processor, document, body = documents(repo)
    processor.process(body)
    rows = repo.related(document["caseId"], "OUTBOX#") + repo.related(document["caseId"], "AUDIT#")
    facts = [row for row in rows if row.get("eventType") == "DocumentValidated"]
    assert len(facts) == 1 and facts[0]["detail"]["correlationId"] == "test"
    audits = [row for row in rows if row.get("actorId") == "document-processor"]
    assert audits and all(row["correlationId"] == "test" for row in audits)
    assert lines(capsys)[0]["correlationId"] == "test"


def test_snapshot_paginated_read_only_and_zero(repo: CaseRepository) -> None:
    now = datetime(2026, 9, 23, 12, tzinfo=UTC)
    for i in range(105):
        row = {
            "PK": f"CASE#c_{i}",
            "SK": "META",
            "entityType": "REVIEW_TASK",
            "status": "PENDING" if i < 3 else "COMPLETED",
            "workflowTaskToken": "never-project-this",
        }
        repo.client.put_item(TableName=repo.table_name, Item=encode(row))
    for row in [
        {
            "PK": "CASE#c_o",
            "SK": "OUTBOX#evt_o",
            "entityType": "OUTBOX",
            "status": "PENDING",
            "createdAt": "2026-09-23T11:00:00Z",
        },
        {
            "PK": "CASE#c_p",
            "SK": "META",
            "entityType": "CASE",
            "workflowStartStatus": "PENDING",
            "updatedAt": "2026-09-23T11:30:00Z",
        },
    ]:
        repo.client.put_item(TableName=repo.table_name, Item=encode(row))
    before = repo.client.scan(TableName=repo.table_name)["Items"]
    with patch.object(repo.client, "scan", wraps=repo.client.scan) as scan:
        result = snapshot(repo.client, repo.table_name, now=now)
    assert scan.call_count >= 2
    assert result == {
        "ReviewTasksPending": 3,
        "OutboxPendingAgeSeconds": 3600,
        "WorkflowStartPendingAgeSeconds": 1800,
        "MonitorSuccess": 1,
    }
    assert repo.client.scan(TableName=repo.table_name)["Items"] == before
    assert snapshot(repo.client, repo.table_name, now=now)["MonitorSuccess"] == 1


def test_snapshot_limit_fails_without_false_healthy_metrics(
    repo: CaseRepository, capsys: Any
) -> None:
    with pytest.raises(RuntimeError, match="page limit"):
        snapshot(repo.client, repo.table_name, page_limit=0)
    assert lines(capsys) == []


def test_empty_snapshot_emits_zero_gauges(repo: CaseRepository) -> None:
    assert snapshot(repo.client, repo.table_name) == {
        "ReviewTasksPending": 0,
        "OutboxPendingAgeSeconds": 0,
        "WorkflowStartPendingAgeSeconds": 0,
        "MonitorSuccess": 1,
    }


def test_controlled_outbox_recovery_is_single_fact_and_idempotent(
    repo: CaseRepository, monkeypatch: Any, capsys: Any
) -> None:
    from outbox_publisher.handler import handler

    publisher, row = outbox(repo)
    monkeypatch.setenv("TABLE_NAME", repo.table_name)
    monkeypatch.setenv("DOMAIN_BUS_ARN", publisher.bus_arn)
    event = {"operation": "recoverOutbox", "caseId": row["caseId"], "eventId": row["eventId"]}
    with patch(
        "outbox_publisher.handler.boto3.client",
        side_effect=lambda service: repo.client if service == "dynamodb" else publisher.events,
    ):
        with patch.object(
            publisher.events, "put_events", wraps=publisher.events.put_events
        ) as send:
            assert handler(event, object()) == {"status": "DISPATCHED"}
            assert handler(event, object()) == {"status": "DISPATCHED"}
            assert send.call_count == 1
        with pytest.raises(ValueError):
            handler({**event, "eventId": "invalid"}, object())
    stored = decode(
        repo.client.get_item(
            TableName=repo.table_name, Key=encode({"PK": row["PK"], "SK": row["SK"]})
        )["Item"]
    )
    assert stored["status"] == "DISPATCHED"
    metrics = [entry for entry in lines(capsys) if "CasesCreated" in entry]
    assert len(metrics) == 1


@pytest.mark.parametrize(
    ("kind", "metric"),
    [
        ("CaseCreated", "CasesCreated"),
        ("CaseSubmitted", "CasesSubmitted"),
        ("CaseResubmitted", "CasesSubmitted"),
        ("CaseApproved", "CasesApproved"),
        ("CaseRejected", "CasesRejected"),
        ("AdditionalInformationRequested", "CasesNeedsInformation"),
        ("DocumentValidated", "DocumentsProcessed"),
        ("DocumentValidationFailed", "DocumentValidationFailures"),
        ("CaseReadyForReview", "ReviewTasksCreated"),
        ("CaseWorkflowFailed", "WorkflowFailures"),
    ],
)
def test_committed_fact_metrics(repo: CaseRepository, capsys: Any, kind: str, metric: str) -> None:
    import boto3
    from test_domain_events import make_fact

    from outbox_publisher.handler import Publisher

    fact = make_fact(repo, kind)
    producer_logs = lines(capsys)
    if kind in {"CaseApproved", "CaseRejected", "AdditionalInformationRequested"}:
        duration = [
            row["ReviewDurationSeconds"] for row in producer_logs if "ReviewDurationSeconds" in row
        ]
        assert len(duration) == 1 and duration[0] >= 0
    events = boto3.client("events", region_name="us-east-1")
    bus = events.create_event_bus(Name="metrics-domain")["EventBusArn"]
    publisher = Publisher(repo, events, bus)
    publisher.publish(fact)
    publisher.publish(fact)
    logs = lines(capsys)
    assert len(logs) == 1 and logs[0][metric] == 1
    assert logs[0]["correlationId"] == fact["correlationId"]


def test_workflow_context_and_partial_failure(capsys: Any) -> None:
    @observed("workflow-test")
    def invoke(event: dict[str, Any], context: object) -> dict[str, Any]:
        return {"batchItemFailures": [{"itemIdentifier": "1"}]}

    invoke(
        {
            "submission": {"correlationId": "corr_original", "caseId": "c_original"},
            "taskToken": "secret",
            "requestId": "spoof",
        },
        SimpleNamespace(aws_request_id="real_id"),
    )
    row = lines(capsys)[0]
    assert row["requestId"] == "real_id" and row["correlationId"] == "corr_original"
    assert row["caseId"] == "c_original" and row["level"] == "ERROR"
    assert "secret" not in json.dumps(row)


def test_monitor_failure_does_not_emit_healthy_snapshot(monkeypatch: Any, capsys: Any) -> None:
    from operations_monitor.handler import handler

    monkeypatch.setenv("TABLE_NAME", "test")
    with patch("operations_monitor.handler.boto3.client") as client:
        client.return_value.scan.side_effect = RuntimeError("private")
        with pytest.raises(RuntimeError):
            handler({}, object())
    logs = lines(capsys)
    assert len(logs) == 1 and "MonitorSuccess" not in logs[0]
    assert "private" not in json.dumps(logs)
