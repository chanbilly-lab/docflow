"""Validate template constraints before any storage calls."""

from dataclasses import FrozenInstanceError, replace

import pytest

from common.templates.models import Check
from common.templates.seed import SUPPLIER_ONBOARDING as SEED


@pytest.mark.parametrize("version", [0, -1, True])
def test_rejects_invalid_version(version: int) -> None:
    with pytest.raises(ValueError):
        replace(SEED, version=version)


def test_rejects_duplicate_checks_and_documents() -> None:
    with pytest.raises(ValueError):
        replace(SEED, checks=(SEED.checks[0], SEED.checks[0]))
    with pytest.raises(ValueError):
        replace(SEED, required_documents=("DIRECTOR_ID", "DIRECTOR_ID"))


def test_rejects_unknown_document_and_unsafe_identifier() -> None:
    with pytest.raises(ValueError):
        replace(SEED, checks=(Check("test", 1, "UNKNOWN", True, "Review"),))
    with pytest.raises(ValueError):
        replace(SEED, template_id="unsafe#id")


def test_rejects_missing_instructions_and_excessive_transaction() -> None:
    with pytest.raises(ValueError):
        replace(SEED.checks[0], instructions=" ")
    with pytest.raises(ValueError):
        replace(
            SEED,
            checks=tuple(
                Check(f"check-{n}", n, "DIRECTOR_ID", True, "Review") for n in range(1, 100)
            ),
        )


def test_definitions_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        SEED.version = 2  # type: ignore[misc]


def test_seed_includes_required_and_optional_checks() -> None:
    assert set(SEED.required_documents) == {
        "COMPANY_REGISTRATION",
        "DIRECTOR_ID",
        "BANK_INFORMATION",
        "ADDRESS_PROOF",
    }
    assert any(check.required for check in SEED.checks)
    assert any(not check.required for check in SEED.checks)
