"""Keep the local health response consistent with the published API contract."""

import json
from pathlib import Path

from case_api.health import handler


def test_health_response_matches_openapi_contract() -> None:
    root = Path(__file__).resolve().parents[3]
    contract = json.loads((root / "docs/api/openapi.yaml").read_text(encoding="utf-8"))
    operation = contract["paths"]["/api/v1/health"]["get"]
    assert operation["security"] == [{"cognitoAccessToken": []}]
    response = handler(
        {
            "requestContext": {
                "authorizer": {"jwt": {"claims": {"sub": "test-user", "token_use": "access"}}}
            }
        },
        None,
    )
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    body = json.loads(response["body"])
    assert set(body) == set(schema["required"])
    for key, value in body.items():
        assert value in schema["properties"][key]["enum"]
    assert response["headers"]["cache-control"] == "no-store"
