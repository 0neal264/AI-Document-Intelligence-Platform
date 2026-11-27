"""Pure view-model tests for dashboard counts, filtering, and exports."""

import csv
import json
from datetime import UTC, datetime

from documind.extraction import (
    ChunkProcessingRecord,
    ChunkProcessingStatus,
    ExtractionResult,
    PageProcessingRecord,
    PageProcessingStatus,
    ProcessingMetadata,
    SourcedField,
    SourceEvidence,
)
from documind.ui.view_model import (
    build_dashboard_view,
    category_counts,
    coverage_summary,
    date_display,
    export_csv,
    export_json,
    export_markdown,
    facts_for_page,
    filter_facts,
    group_items,
    narrative_summary,
)


def sample_result() -> ExtractionResult:
    return ExtractionResult(
        document_id="doc-view-model",
        filename="sample.pdf",
        pdf_metadata={"Title": "PDF title"},
        document_title=SourcedField(
            value="Extracted title",
            evidence=[
                SourceEvidence(page_number=1, quote="Extracted title", verified=True)
            ],
        ),
        document_type=SourcedField(
            value="Contract",
            evidence=[SourceEvidence(page_number=1, quote="Contract", verified=True)],
        ),
        organisation=SourcedField(
            value="Northwind",
            evidence=[SourceEvidence(page_number=1, quote="Northwind", verified=True)],
            needs_review=True,
        ),
        important_facts=[
            SourcedField(
                value="The policy applies to contractors.",
                category="Policy",
                evidence=[
                    SourceEvidence(
                        page_number=3,
                        quote="The policy applies to contractors.",
                        verified=False,
                    )
                ],
            ),
            SourcedField(
                value="The term is one year.",
                category="Term",
                evidence=[
                    SourceEvidence(
                        page_number=2, quote="The term is one year.", verified=True
                    )
                ],
            ),
        ],
        key_concepts=[
            SourcedField(
                value="Renewal",
                category="Contract concept",
                evidence=[
                    SourceEvidence(page_number=2, quote="Renewal", verified=True)
                ],
            )
        ],
        key_entities=[
            SourcedField(
                value="Northwind",
                category="Party",
                evidence=[
                    SourceEvidence(page_number=1, quote="Northwind", verified=True)
                ],
            )
        ],
        relevant_dates=[
            SourcedField(
                value="1 January 2026",
                category="Effective date",
                evidence=[
                    SourceEvidence(page_number=2, quote="1 January 2026", verified=True)
                ],
            )
        ],
        processing=ProcessingMetadata(
            status="partial",
            profile="contract",
            profile_source="detected",
            model="gemini-test-model",
            processed_at=datetime(2026, 11, 27, 12, 30, tzinfo=UTC),
            total_pages=3,
            covered_pages=[1, 2],
            uncovered_pages=[3],
            page_records=[
                PageProcessingRecord(
                    page_number=1,
                    status=PageProcessingStatus.PROCESSED,
                    character_count=80,
                ),
                PageProcessingRecord(
                    page_number=2,
                    status=PageProcessingStatus.LOW_TEXT,
                    character_count=20,
                ),
                PageProcessingRecord(
                    page_number=3,
                    status=PageProcessingStatus.FAILED,
                    character_count=0,
                    error_message="Text extraction failed for this PDF page.",
                ),
            ],
            chunks=[
                ChunkProcessingRecord(
                    chunk_index=1,
                    page_numbers=[1, 2],
                    status=ChunkProcessingStatus.SUCCEEDED,
                    attempt_count=1,
                    duration_ms=500,
                )
            ],
        ),
    )


def test_dashboard_counts_identity_and_coverage_come_from_result():
    view = build_dashboard_view(sample_result())

    assert view.title == "Extracted title"
    assert view.document_type == "Contract"
    assert view.organisation == "Northwind"
    assert view.page_count == 3
    assert view.pages_covered == 2
    assert view.fact_count == 3
    assert view.entity_count == 1
    assert view.date_count == 1
    assert view.review_count == 2
    assert view.status == "partial"
    assert [(cell.page_number, cell.status) for cell in view.page_cells] == [
        (1, "processed"),
        (2, "low_text"),
        (3, "failed"),
    ]


def test_fact_filters_and_page_selection_return_only_matching_items():
    view = build_dashboard_view(sample_result())

    policy = filter_facts(
        view.facts,
        query="POLICY",
        category="Policy",
        page_number=3,
        needs_review=True,
    )
    page_two = facts_for_page(view.all_items, 2)

    assert [item.statement for item in policy] == ["The policy applies to contractors."]
    assert len(page_two) == 3
    assert all(2 in item.page_numbers for item in page_two)


def test_grouping_and_exports_preserve_categories_quotes_and_pages():
    result = sample_result()
    view = build_dashboard_view(result)
    grouped = group_items(view.entities)
    json_payload = json.loads(export_json(result))
    csv_rows = list(csv.DictReader(export_csv(view.facts).splitlines()))
    markdown = export_markdown(result, view)
    summary = narrative_summary(view)

    assert list(grouped) == ["Party"]
    assert json_payload["processing"]["uncovered_pages"] == [3]
    assert csv_rows[0]["pages"] == "3"
    assert csv_rows[0]["needs_review"] == "True"
    assert "The policy applies to contractors." in markdown
    assert "p. 3: > The policy applies to contractors." in markdown
    assert "Key dates: 1 January 2026." in summary


def test_sidebar_counts_and_coverage_status_come_from_result():
    view = build_dashboard_view(sample_result())

    assert category_counts(view.facts) == {
        "Contract concept": 1,
        "Policy": 1,
        "Term": 1,
    }
    coverage = coverage_summary(view)
    assert coverage.complete is False
    assert coverage.uncovered_pages == (3,)
    assert coverage.status_text == "Partial: pages 3 not covered"


def test_date_display_normalizes_clear_dates_and_keeps_original_text():
    view = build_dashboard_view(sample_result())

    display = date_display(view.dates[0])

    assert display.label == "Effective date"
    assert display.iso_date == "2026-01-01"
    assert display.original_text == "1 January 2026"
