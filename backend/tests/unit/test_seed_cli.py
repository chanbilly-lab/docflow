"""Ensure the operator command defaults to preview and cannot target AWS."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def test_preview() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/seed_templates.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["templateId"] == "supplier-onboarding"
    assert payload["version"] == 1


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://dynamodb.us-east-1.amazonaws.com",
        "http://example.com:8000",
        "http://127.0.0.1:8000@evil.example",
    ],
)
def test_rejects_nonlocal_endpoint(endpoint: str) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/seed_templates.py"), "--endpoint-url", endpoint],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "Only an explicit HTTP loopback endpoint" in result.stderr
