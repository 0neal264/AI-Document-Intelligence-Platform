"""Tests for page-aware sentence chunking."""

from documind.extraction import ChunkingConfig, PageText, build_chunks


def test_chunks_keep_sentence_and_page_mapping_and_apply_overlap():
    result = build_chunks(
        [
            PageText(1, "First sentence is here. Second sentence is also here."),
            PageText(2, "Third sentence belongs to page two."),
        ],
        ChunkingConfig(max_chunk_chars=34, overlap_chars=20, max_chunks=10),
    )

    assert len(result.chunks) > 1
    assert result.omitted_pages == ()
    assert result.chunks[0].page_numbers == (1,)
    sentences = {
        "First sentence is here.",
        "Second sentence is also here.",
        "Third sentence belongs to page two.",
    }
    assert all(
        segment.text in sentences
        for chunk in result.chunks
        for segment in chunk.segments
    )
    assert all(
        "[Page 1]" in chunk.text or "[Page 2]" in chunk.text for chunk in result.chunks
    )
    assert "First sentence is here." in result.chunks[0].text
    assert any(2 in chunk.page_numbers for chunk in result.chunks)


def test_chunk_cap_reports_pages_with_omitted_text():
    result = build_chunks(
        [PageText(i, f"Page {i} has one complete sentence.") for i in range(1, 4)],
        ChunkingConfig(max_chunk_chars=10, overlap_chars=0, max_chunks=1),
    )

    assert len(result.chunks) == 1
    assert result.omitted_pages == (2, 3)
    assert result.chunks[0].text.endswith("Page 1 has one complete sentence.")


def test_very_long_single_sentence_is_not_split_mid_sentence():
    sentence = "A" * 80 + "."
    result = build_chunks(
        [PageText(7, sentence)],
        ChunkingConfig(max_chunk_chars=20, overlap_chars=0),
    )

    assert len(result.chunks) == 1
    assert sentence in result.chunks[0].text
    assert result.chunks[0].page_numbers == (7,)
