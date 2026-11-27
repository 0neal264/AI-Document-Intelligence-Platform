"""Provider-independent extraction schema and service tests."""

import pytest
from pydantic import ValidationError

from documind.extraction import (
    ExtractionResult,
    ExtractionRunConfig,
    ExtractionService,
    MockProvider,
    SourcedField,
    SourceEvidence,
)
from documind.ingestion import Document, ExtractionStatus, Page


class RecordingProvider:
    def __init__(self):
        self.text = None

    def extract(self, text: str) -> ExtractionResult:
        self.text = text
        return ExtractionResult(
            document_title=SourcedField(
                value="Agreement",
                evidence=[SourceEvidence(page_number=2, quote="Agreement")],
            )
        )


def test_populated_extraction_field_requires_source_evidence():
    with pytest.raises(ValidationError, match="source evidence"):
        SourcedField(value="unsupported value")


def test_missing_extraction_field_can_remain_null():
    field = SourcedField()

    assert field.value is None
    assert field.evidence == []


def test_existing_result_json_still_loads_with_additive_optional_fields():
    old_result_json = (
        '{"document_title":{"value":"Legacy title",'
        '"evidence":[{"page_number":1,"quote":"Legacy title"}]}}'
    )

    result = ExtractionResult.model_validate_json(old_result_json)

    assert result.document_title.value == "Legacy title"
    assert result.document_title.evidence[0].verified is None
    assert result.key_concepts == []
    assert result.processing is None


def test_extraction_service_preserves_page_references_and_document_identity():
    document = Document(
        document_id="doc-123",
        filename="source.pdf",
        page_count=2,
        metadata={"Title": "Agreement from PDF metadata"},
        pages=(
            Page(1, "Intro", ExtractionStatus.EXTRACTED),
            Page(2, "Agreement", ExtractionStatus.EXTRACTED),
        ),
    )
    provider = RecordingProvider()

    result = ExtractionService(
        provider,
        profile="general",
        config=ExtractionRunConfig(cache_directory=None, request_delay_seconds=0),
    ).extract_document(document)

    assert "[Page 1]\nIntro" in provider.text
    assert "[Page 2]\nAgreement" in provider.text
    assert result.document_id == "doc-123"
    assert result.filename == "source.pdf"
    assert result.pdf_metadata == {"Title": "Agreement from PDF metadata"}
    assert result.document_title.evidence[0].page_number == 2
    assert result.processing is not None
    assert result.processing.status == "complete"
    assert [page.page_number for page in result.processing.page_records] == [1, 2]


def test_mock_provider_remains_usable_without_external_service():
    result = MockProvider().extract("private text")

    assert result.message.startswith("Demo mode")
    assert "private text" not in result.message
