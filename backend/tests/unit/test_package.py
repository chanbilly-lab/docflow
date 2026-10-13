"""Verify the installed shared package is discoverable without AWS dependencies."""

from importlib import import_module
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "name", ["auth", "logging", "errors", "ids", "dynamodb", "events", "idempotency"]
)
def test_shared_package_imports(name: str) -> None:
    module = import_module(f"common.{name}")
    assert module.__file__ is not None
    assert Path(module.__file__).is_file()
    assert module.__package__ == f"common.{name}"
