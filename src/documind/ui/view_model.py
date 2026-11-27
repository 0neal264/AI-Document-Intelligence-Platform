"""UI-independent dashboard summaries, filters, and export formats."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime

from documind.extraction.provider import ExtractionResult, SourcedField


@dataclass(frozen=True)
class EvidenceView:
    statement: str
    category: str
    page_number: int
    quote: str
    verified: bool | None
    needs_review: bool


@dataclass(frozen=True)
class FactView:
    statement: str
    category: str
    page_numbers: tuple[int, ...]
    evidence: tuple[EvidenceView, ...]
    needs_review: bool
    source_field: str


@dataclass(frozen=True)
class PageCell:
    page_number: int
    status: str


@dataclass(frozen=True)
class DashboardView:
    title: str
    document_type: str | None
    organisation: str | None
    page_count: int | None
    profile: str | None
    model: str | None
    processed_at: str | None
    status: str | None
    pages_covered: int | None
    fact_count: int
    entity_count: int
    date_count: int
    review_count: int
    uncovered_pages: tuple[int, ...]
    page_cells: tuple[PageCell, ...]
    facts: tuple[FactView, ...]
    entities: tuple[FactView, ...]
    dates: tuple[FactView, ...]
    all_items: tuple[FactView, ...]
    summary_facts: tuple[FactView, ...]
    summary_concepts: tuple[FactView, ...]


@dataclass(frozen=True)
class CoverageSummary:
    status_text: str
    complete: bool
    uncovered_pages: tuple[int, ...]


@dataclass(frozen=True)
class DateDisplay:
    label: str
    original_text: str
    iso_date: str | None


_FACT_COLLECTIONS = (
    ("important_facts", "Fact"),
    ("key_concepts", "Key concept"),
    ("events_activities", "Event or activity"),
    ("requirements_obligations", "Requirement or obligation"),
    ("definitions", "Definition"),
    ("missing_information", "Missing information"),
)


def build_dashboard_view(result: ExtractionResult) -> DashboardView:
    """Derive dashboard display data solely from a validated result model."""
    facts = tuple(
        view
        for field_name, fallback in _FACT_COLLECTIONS
        for view in _items(getattr(result, field_name), field_name, fallback)
    )
    entities = tuple(_items(result.key_entities, "key_entities", "Entity"))
    dates = tuple(_items(result.relevant_dates, "relevant_dates", "Date"))
    identity_items = tuple(
        _items([result.document_title], "document_title", "Title")
        + _items([result.document_type], "document_type", "Document type")
        + _items([result.organisation], "organisation", "Organisation")
    )
    all_items = (*identity_items, *facts, *entities, *dates)
    metadata = result.processing
    pdf_title = (result.pdf_metadata or {}).get("Title")
    title = (
        result.document_title.value
        or pdf_title
        or result.filename
        or "Untitled document"
    )
    page_cells = (
        tuple(
            PageCell(page_number=record.page_number, status=record.status.value)
            for record in metadata.page_records
        )
        if metadata
        else ()
    )
    summary_facts = tuple(
        view for view in facts if view.source_field == "important_facts"
    )
    summary_concepts = tuple(
        view for view in facts if view.source_field in {"key_concepts", "definitions"}
    )

    return DashboardView(
        title=title,
        document_type=result.document_type.value,
        organisation=result.organisation.value,
        page_count=metadata.total_pages if metadata else None,
        profile=metadata.profile if metadata else None,
        model=metadata.model if metadata else None,
        processed_at=metadata.processed_at.isoformat(timespec="minutes")
        if metadata
        else None,
        status=metadata.status if metadata else None,
        pages_covered=len(metadata.covered_pages) if metadata else None,
        fact_count=sum(
            len(getattr(result, field_name))
            for field_name in (
                "important_facts",
                "key_concepts",
                "events_activities",
                "requirements_obligations",
                "definitions",
            )
        ),
        entity_count=len(result.key_entities),
        date_count=len(result.relevant_dates),
        review_count=sum(item.needs_review for item in all_items),
        uncovered_pages=tuple(metadata.uncovered_pages) if metadata else (),
        page_cells=page_cells,
        facts=facts,
        entities=entities,
        dates=dates,
        all_items=all_items,
        summary_facts=summary_facts,
        summary_concepts=summary_concepts,
    )


def filter_facts(
    facts: tuple[FactView, ...] | list[FactView],
    *,
    query: str = "",
    category: str | None = None,
    page_number: int | None = None,
    needs_review: bool | None = None,
) -> tuple[FactView, ...]:
    """Filter fact rows by text, category, cited page, and review flag."""
    needle = query.casefold().strip()
    return tuple(
        item
        for item in facts
        if (
            not needle
            or needle in item.statement.casefold()
            or any(needle in evidence.quote.casefold() for evidence in item.evidence)
        )
        and (category is None or item.category == category)
        and (page_number is None or page_number in item.page_numbers)
        and (needs_review is None or item.needs_review is needs_review)
    )


def category_counts(facts: tuple[FactView, ...] | list[FactView]) -> dict[str, int]:
    """Count result facts by their extracted category."""
    counts: dict[str, int] = {}
    for item in facts:
        counts[item.category] = counts.get(item.category, 0) + 1
    return dict(sorted(counts.items()))


def coverage_summary(view: DashboardView) -> CoverageSummary:
    """Describe coverage using only page status records in the result."""
    uncovered = tuple(sorted(set(view.uncovered_pages)))
    if not view.page_cells:
        return CoverageSummary("Page coverage unavailable", False, uncovered)
    if not uncovered and all(
        cell.status not in {"failed", "empty"} for cell in view.page_cells
    ):
        return CoverageSummary("Complete", True, ())
    if uncovered:
        pages = ", ".join(map(str, uncovered))
        return CoverageSummary(f"Partial: pages {pages} not covered", False, uncovered)
    return CoverageSummary("Partial: some pages need review", False, ())


def date_display(item: FactView) -> DateDisplay:
    """Format a clearly recognizable extracted date without guessing ambiguous values."""
    value = item.statement.strip()
    parsed = None
    for date_format in ("%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%d %b %Y"):
        try:
            parsed = datetime.strptime(value, date_format).date()
            break
        except ValueError:
            continue
    return DateDisplay(
        label=item.category,
        original_text=item.statement,
        iso_date=parsed.isoformat() if parsed else None,
    )


def group_items(
    items: tuple[FactView, ...] | list[FactView],
) -> dict[str, tuple[FactView, ...]]:
    """Group display items by their profile-provided category."""
    groups: dict[str, list[FactView]] = {}
    for item in items:
        groups.setdefault(item.category, []).append(item)
    return {name: tuple(values) for name, values in sorted(groups.items())}


def facts_for_page(
    items: tuple[FactView, ...] | list[FactView], page_number: int
) -> tuple[FactView, ...]:
    """Return items with evidence on a selected page."""
    return tuple(item for item in items if page_number in item.page_numbers)


def narrative_summary(view: DashboardView) -> str:
    """Compose a short summary from extracted facts, concepts, and dates."""
    sections = (
        ("Facts", view.summary_facts),
        ("Key concepts", view.summary_concepts),
        ("Key dates", view.dates),
    )
    return " ".join(
        f"{label}: " + "; ".join(item.statement for item in items) + "."
        for label, items in sections
        if items
    )


def export_json(result: ExtractionResult) -> str:
    """Serialize the result model without making a provider request."""
    return result.model_dump_json(indent=2, exclude_none=True)


def export_csv(facts: tuple[FactView, ...] | list[FactView]) -> str:
    """Build a flat CSV of fact statements and their evidence references."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=("statement", "category", "pages", "needs_review", "evidence"),
    )
    writer.writeheader()
    for item in facts:
        writer.writerow(
            {
                "statement": item.statement,
                "category": item.category,
                "pages": ";".join(map(str, item.page_numbers)),
                "needs_review": item.needs_review,
                "evidence": " | ".join(
                    f"p. {entry.page_number}: {entry.quote}" for entry in item.evidence
                ),
            }
        )
    return output.getvalue()


def export_markdown(result: ExtractionResult, view: DashboardView | None = None) -> str:
    """Create a source-grounded Markdown report from the validated result."""
    view = view or build_dashboard_view(result)
    lines = [f"# {view.title}", ""]
    identity = [
        ("Document type", view.document_type),
        ("Organisation", view.organisation),
        ("Profile", view.profile),
        ("Model", view.model),
        ("Status", view.status),
    ]
    lines.extend(f"- **{label}:** {value}" for label, value in identity if value)
    if view.page_count is not None:
        lines.append(f"- **Pages covered:** {view.pages_covered} / {view.page_count}")
    lines.extend(["", "## Facts", ""])
    if not view.facts:
        lines.append("No facts were extracted.")
    for item in view.facts:
        pages = ", ".join(map(str, item.page_numbers)) or "No page reference"
        review = " · Needs human review" if item.needs_review else ""
        lines.append(f"- **{item.category}:** {item.statement} (pages {pages}){review}")
        for evidence in item.evidence:
            lines.append(f"  - p. {evidence.page_number}: > {evidence.quote}")
    return "\n".join(lines).rstrip() + "\n"


def _items(
    values: list[SourcedField], source_field: str, fallback_category: str
) -> list[FactView]:
    result: list[FactView] = []
    for value in values:
        if value.value is None:
            continue
        evidence = tuple(
            EvidenceView(
                statement=value.value,
                category=value.category or fallback_category,
                page_number=source.page_number,
                quote=source.quote,
                verified=source.verified,
                needs_review=source.verified is False or value.needs_review,
            )
            for source in value.evidence
        )
        result.append(
            FactView(
                statement=value.value,
                category=value.category or fallback_category,
                page_numbers=tuple(sorted({item.page_number for item in evidence})),
                evidence=evidence,
                needs_review=value.needs_review
                or any(item.verified is False for item in evidence),
                source_field=source_field,
            )
        )
    return result
