"""Offline tests for the multi-stage extraction service."""

from documind.extraction import (
    ChunkingConfig,
    ChunkProcessingStatus,
    ExtractionResult,
    ExtractionRunConfig,
    ExtractionService,
    GeminiAPIError,
    GeminiRateLimitError,
    PageProcessingStatus,
    SourcedField,
    SourceEvidence,
)
from documind.ingestion import Document, ExtractionStatus, Page


class SequenceProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def extract(self, text):
        self.calls.append(text)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def make_document(*texts: str) -> Document:
    pages = tuple(
        Page(
            page_number=index,
            extracted_text=text,
            extraction_status=(
                ExtractionStatus.EXTRACTED if text else ExtractionStatus.EMPTY
            ),
        )
        for index, text in enumerate(texts, start=1)
    )
    return Document("doc-test", "synthetic.pdf", len(pages), {}, pages)


def result_for(page: int, quote: str, *facts: tuple[str, str]) -> ExtractionResult:
    return ExtractionResult(
        important_facts=[
            SourcedField(
                value=value,
                category=category,
                evidence=[SourceEvidence(page_number=page, quote=quote)],
            )
            for value, category in facts
        ]
    )


def config(tmp_path, **overrides):
    values = {
        "cache_directory": tmp_path,
        "request_delay_seconds": 0,
        "retry_base_delay_seconds": 0,
        "retry_max_delay_seconds": 0,
    }
    values.update(overrides)
    return ExtractionRunConfig(**values)


def test_page_processing_metadata_records_each_page_once(tmp_path):
    document = make_document(
        "This page has enough characters to be considered normal text.",
        "",
        "short text",
        "failed source",
    )
    pages = list(document.pages)
    pages[3] = Page(4, "", ExtractionStatus.FAILED, error="private parser detail")
    document = Document(document.document_id, document.filename, 4, {}, tuple(pages))
    provider = SequenceProvider(
        [result_for(1, "This page has enough characters to be considered normal text.")]
    )

    extracted = ExtractionService(
        provider,
        profile="general",
        config=config(tmp_path),
    ).extract_document(document)

    records = extracted.processing.page_records
    assert [record.page_number for record in records] == [1, 2, 3, 4]
    assert [record.status for record in records] == [
        PageProcessingStatus.PROCESSED,
        PageProcessingStatus.EMPTY,
        PageProcessingStatus.LOW_TEXT,
        PageProcessingStatus.FAILED,
    ]
    assert "private parser detail" not in str(extracted.processing)
    assert extracted.processing.uncovered_pages == [4]


def test_transient_error_retries_with_bounded_attempt_count(tmp_path):
    provider = SequenceProvider(
        [
            GeminiRateLimitError("Temporary rate limit", quota_exhausted=False),
            result_for(1, "Retryable source sentence."),
        ]
    )
    delays = []
    document = make_document("Retryable source sentence.")

    result = ExtractionService(
        provider,
        profile="general",
        config=config(tmp_path, max_attempts_per_request=3),
        sleeper=delays.append,
        random_value=lambda: 0,
    ).extract_document(document)

    assert len(provider.calls) == 2
    assert result.processing.chunks[0].attempt_count == 2
    assert result.processing.chunks[0].status == ChunkProcessingStatus.SUCCEEDED
    assert delays == [0]


def test_request_limit_marks_unrequested_pages_uncovered(tmp_path):
    provider = SequenceProvider(
        [result_for(1, "First page is a complete and independent statement.")]
    )
    document = make_document(
        "First page is a complete and independent statement.",
        "Second page is a complete and independent statement.",
        "Third page is a complete and independent statement.",
    )
    cfg = config(
        tmp_path,
        chunking=ChunkingConfig(max_chunk_chars=20, overlap_chars=0, max_chunks=10),
        max_requests=1,
    )

    result = ExtractionService(
        provider, profile="general", config=cfg
    ).extract_document(document)

    assert len(provider.calls) == 1
    assert result.processing.api_requests == 1
    assert result.processing.request_limit == 1
    assert result.processing.uncovered_pages == [2, 3]
    assert [chunk.status for chunk in result.processing.chunks] == [
        ChunkProcessingStatus.SUCCEEDED,
        ChunkProcessingStatus.SKIPPED,
        ChunkProcessingStatus.SKIPPED,
    ]


def test_permanent_bad_request_is_not_retried(tmp_path):
    provider = SequenceProvider([GeminiAPIError("Safe HTTP 400 reason")])
    result = ExtractionService(
        provider,
        profile="general",
        config=config(tmp_path, max_attempts_per_request=4),
    ).extract_document(make_document("Some document text."))

    assert len(provider.calls) == 1
    assert result.processing.chunks[0].status == ChunkProcessingStatus.FAILED
    assert result.processing.chunks[0].error_message == "Safe HTTP 400 reason"


def test_quota_exhaustion_stops_remaining_requests(tmp_path):
    provider = SequenceProvider(
        [GeminiRateLimitError("Quota exhausted", quota_exhausted=True)]
    )
    document = make_document(
        "First page is a complete sentence and should be a chunk.",
        "Second page is another complete sentence and should be a chunk.",
    )
    cfg = config(
        tmp_path,
        chunking=ChunkingConfig(max_chunk_chars=25, overlap_chars=0, max_chunks=8),
        max_attempts_per_request=3,
    )

    result = ExtractionService(
        provider, profile="general", config=cfg
    ).extract_document(document)

    assert len(provider.calls) == 1
    assert result.processing.quota_exhausted is True
    assert result.processing.status == "partial"
    assert result.processing.chunks[0].attempt_count == 1
    assert result.processing.chunks[1].status == ChunkProcessingStatus.SKIPPED


def test_partial_failure_keeps_successful_items_and_uncovered_pages(tmp_path):
    provider = SequenceProvider(
        [
            result_for(
                1, "First page has its own complete statement.", ("First fact", "fact")
            ),
            RuntimeError("must not leak private text"),
            result_for(
                3, "Third page has its own complete statement.", ("Third fact", "fact")
            ),
        ]
    )
    document = make_document(
        "First page has its own complete statement.",
        "Second page has its own complete statement.",
        "Third page has its own complete statement.",
    )
    cfg = config(
        tmp_path,
        chunking=ChunkingConfig(max_chunk_chars=20, overlap_chars=0, max_chunks=10),
    )

    result = ExtractionService(
        provider, profile="general", config=cfg
    ).extract_document(document)

    assert [fact.value for fact in result.important_facts] == [
        "First fact",
        "Third fact",
    ]
    assert result.processing.status == "partial"
    assert result.processing.uncovered_pages == [2]
    assert "must not leak" not in str(result.processing)


def test_duplicate_facts_merge_evidence_and_distinct_facts_remain(tmp_path):
    provider = SequenceProvider(
        [
            result_for(
                1,
                "Source on page one.",
                ("Payment is due within 30 days!", "payment term"),
                ("Payment is due within 60 days.", "payment term"),
            ),
            result_for(
                2,
                "Source on page two.",
                ("payment is due within 30 days", "payment term"),
            ),
        ]
    )
    document = make_document("Source on page one.", "Source on page two.")
    cfg = config(
        tmp_path,
        chunking=ChunkingConfig(max_chunk_chars=10, overlap_chars=0, max_chunks=10),
    )

    result = ExtractionService(
        provider, profile="general", config=cfg
    ).extract_document(document)

    assert len(result.important_facts) == 2
    duplicate = result.important_facts[0]
    assert [evidence.page_number for evidence in duplicate.evidence] == [1, 2]
    assert [evidence.quote for evidence in duplicate.evidence] == [
        "Source on page one.",
        "Source on page two.",
    ]
    assert result.important_facts[1].value == "Payment is due within 60 days."
    assert result.processing.merge_log[0].reason == "normalized text matched exactly"


def test_evidence_is_verified_against_the_original_page_text(tmp_path):
    provider = SequenceProvider(
        [result_for(1, "This quote is not in the page.", ("A claimed fact", "fact"))]
    )
    result = ExtractionService(
        provider,
        profile="general",
        config=config(tmp_path),
    ).extract_document(make_document("Actual page text."))

    item = result.important_facts[0]
    assert item.needs_review is True
    assert item.evidence[0].verified is False


def test_successful_chunk_response_is_cached_for_reruns(tmp_path):
    provider = SequenceProvider([result_for(1, "Cacheable source sentence.")])
    document = make_document("Cacheable source sentence.")
    run_config = config(tmp_path)

    first = ExtractionService(
        provider, profile="general", config=run_config
    ).extract_document(document)
    second = ExtractionService(
        provider, profile="general", config=run_config
    ).extract_document(document)

    assert len(provider.calls) == 1
    assert first.important_facts == second.important_facts
    assert second.processing.chunks[0].cache_hit is True
    assert second.processing.chunks[0].attempt_count == 0


def test_auto_profile_detection_uses_a_separate_first_pages_request(tmp_path):
    provider = SequenceProvider(
        [
            ExtractionResult(
                document_type=SourcedField(
                    value="lecture_slides",
                    evidence=[SourceEvidence(page_number=1, quote="Course overview")],
                )
            ),
            result_for(
                1, "Course overview and learning goals.", ("Learning goals", "topic")
            ),
        ]
    )
    result = ExtractionService(
        provider,
        config=config(tmp_path),
    ).extract_document(make_document("Course overview and learning goals."))

    assert len(provider.calls) == 2
    assert result.processing.profile == "lecture_slides"
    assert result.processing.profile_source == "detected"
    assert "Ignore" not in provider.calls[0]
    assert "untrusted" in provider.calls[0].lower()
