"""Generic document profile for the initial structured extraction milestone."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentProfile:
    """Reusable profile metadata and extraction guidance."""

    name: str
    instructions: str
    categories: tuple[str, ...] = ()
    domain_hints: str = ""


GENERIC_DOCUMENT_PROFILE = DocumentProfile(
    name="general",
    instructions="Use the general categories and return only source-supported items.",
    categories=(
        "document metadata",
        "facts",
        "entities",
        "dates",
        "organisations",
        "key concepts",
        "events and activities",
        "requirements and obligations",
        "definitions",
        "missing information",
    ),
)


_GENERIC_CATEGORIES = GENERIC_DOCUMENT_PROFILE.categories

DOCUMENT_PROFILES: dict[str, DocumentProfile] = {
    "general": GENERIC_DOCUMENT_PROFILE,
    "cv": DocumentProfile(
        name="cv",
        instructions="For a CV, organize profile-specific items by category.",
        categories=_GENERIC_CATEGORIES
        + (
            "contact",
            "education",
            "employment",
            "skills",
            "certifications",
            "projects",
        ),
        domain_hints="A CV or resume describing a person's background and experience.",
    ),
    "lecture_slides": DocumentProfile(
        name="lecture_slides",
        instructions="For lecture slides, preserve course and learning structure.",
        categories=_GENERIC_CATEGORIES
        + (
            "course information",
            "learning objectives",
            "topics",
            "deadlines",
            "assignments",
            "exam requirements",
            "examples",
        ),
        domain_hints="Slides, lecture notes, teaching materials, or course handouts.",
    ),
    "invoice": DocumentProfile(
        name="invoice",
        instructions="For an invoice, preserve monetary labels and amounts exactly.",
        categories=_GENERIC_CATEGORIES
        + (
            "supplier",
            "customer",
            "invoice number",
            "line items",
            "subtotal",
            "VAT",
            "total",
        ),
        domain_hints="An invoice, receipt, or request for payment.",
    ),
    "contract": DocumentProfile(
        name="contract",
        instructions="For a contract, distinguish parties, duties, and key clauses.",
        categories=_GENERIC_CATEGORIES
        + ("parties", "payment terms", "termination", "key clauses"),
        domain_hints="An agreement or contract that establishes terms between parties.",
    ),
}
