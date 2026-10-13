"""First supplier-onboarding definition; contains no customer data."""

from common.templates.models import Check, Template

SUPPLIER_ONBOARDING = Template(
    template_id="supplier-onboarding",
    version=1,
    case_type="SUPPLIER_ONBOARDING",
    required_documents=("COMPANY_REGISTRATION", "DIRECTOR_ID", "BANK_INFORMATION", "ADDRESS_PROOF"),
    checks=(
        Check(
            "company-registration-readable",
            1,
            "COMPANY_REGISTRATION",
            True,
            "Confirm the registration document is readable and identifies the company.",
        ),
        Check(
            "director-id-readable",
            2,
            "DIRECTOR_ID",
            True,
            "Confirm the director identification is readable and consistent with the submission.",
        ),
        Check(
            "bank-information-complete",
            3,
            "BANK_INFORMATION",
            True,
            "Confirm the bank document identifies the beneficiary and account details.",
        ),
        Check(
            "address-proof-consistent",
            4,
            "ADDRESS_PROOF",
            True,
            "Confirm the address proof is readable and matches the submitted company address.",
        ),
        Check(
            "company-registration-notes",
            5,
            "COMPANY_REGISTRATION",
            False,
            "Record any additional registration observations when relevant.",
        ),
    ),
)
