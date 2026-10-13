"""Exercise trusted authorizer context and response confidentiality."""

import json
from typing import Any

import pytest

from case_api.health import handler


def test_authenticated_health() -> None:
    event = {
        "headers": {"x-correlation-id": "test-123", "authorization": "secret-token"},
        "requestContext": {
            "authorizer": {"jwt": {"claims": {"sub": "user", "token_use": "access"}}}
        },
    }
    response = handler(event, None)
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"status": "ok", "service": "docflow"}
    assert response["headers"]["x-correlation-id"] == "test-123"
    assert "secret-token" not in json.dumps(response)


@pytest.mark.parametrize(
    "claims",
    [{}, {"sub": "user", "token_use": "id"}, {"sub": "", "token_use": "access"}],
)
def test_rejects_missing_or_wrong_claims(claims: dict[str, Any]) -> None:
    response = handler({"requestContext": {"authorizer": {"jwt": {"claims": claims}}}}, None)
    assert response["statusCode"] == 401
    assert json.loads(response["body"])["error"]["code"] == "UNAUTHORIZED"


def test_raw_bearer_is_not_trusted() -> None:
    response = handler({"headers": {"authorization": "Bearer forged"}}, None)
    assert response["statusCode"] == 401


def test_unsafe_correlation_id_is_replaced() -> None:
    response = handler({"headers": {"x-correlation-id": "bad\r\nheader"}}, None)
    assert response["headers"]["x-correlation-id"].startswith("corr_")
