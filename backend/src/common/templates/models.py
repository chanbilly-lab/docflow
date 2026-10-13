"""Validated immutable definitions, independent of AWS."""

import re
from dataclasses import asdict, dataclass


def identifier(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", value):
        raise ValueError("Identifiers must contain only letters, digits, underscore or hyphen.")


@dataclass(frozen=True)
class Check:
    check_id: str
    order: int
    document_type: str
    required: bool
    instructions: str

    def __post_init__(self) -> None:
        identifier(self.check_id)
        identifier(self.document_type)
        if type(self.order) is not int or not 1 <= self.order <= 9999:
            raise ValueError("Check order must be an integer from 1 to 9999.")
        if type(self.required) is not bool:
            raise ValueError("Required must be boolean.")
        if (
            not isinstance(self.instructions, str)
            or not 1 <= len(self.instructions.strip()) <= 2000
        ):
            raise ValueError("Reviewer instructions must contain 1-2000 characters.")


@dataclass(frozen=True)
class Template:
    template_id: str
    version: int
    case_type: str
    required_documents: tuple[str, ...]
    checks: tuple[Check, ...]

    def __post_init__(self) -> None:
        identifier(self.template_id)
        identifier(self.case_type)
        if type(self.version) is not int or self.version < 1:
            raise ValueError("Version must be a positive integer.")
        if (
            not isinstance(self.required_documents, tuple)
            or not 1 <= len(self.required_documents) <= 50
        ):
            raise ValueError("Required documents must be a tuple of 1-50 types.")
        for document in self.required_documents:
            identifier(document)
        if len(set(self.required_documents)) != len(self.required_documents):
            raise ValueError("Duplicate document types.")
        if not isinstance(self.checks, tuple) or not 1 <= len(self.checks) <= 98:
            raise ValueError("A template requires 1-98 checks for a single transaction.")
        if not all(isinstance(check, Check) for check in self.checks):
            raise ValueError("Invalid check definition.")
        if len({check.check_id for check in self.checks}) != len(self.checks):
            raise ValueError("Duplicate check identifiers.")
        if len({check.order for check in self.checks}) != len(self.checks):
            raise ValueError("Duplicate check order.")
        if any(check.document_type not in self.required_documents for check in self.checks):
            raise ValueError("Check references an unknown document type.")

    def content(self) -> dict[str, object]:
        return {
            "templateId": self.template_id,
            "version": self.version,
            "caseType": self.case_type,
            "requiredDocuments": list(self.required_documents),
            "checks": [asdict(check) for check in sorted(self.checks, key=lambda c: c.order)],
        }
