"""Page-preserving character chunking for long document text."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PageText:
    """Text associated with one original 1-indexed PDF page."""

    page_number: int
    text: str


@dataclass(frozen=True)
class ChunkSegment:
    """A text segment and the page from which it came."""

    page_number: int
    text: str


@dataclass(frozen=True)
class TextChunk:
    """One request-sized group of source segments."""

    index: int
    segments: tuple[ChunkSegment, ...]
    page_numbers: tuple[int, ...]
    text: str


@dataclass(frozen=True)
class ChunkingResult:
    """Created chunks plus pages omitted by the configured chunk cap."""

    chunks: tuple[TextChunk, ...]
    omitted_pages: tuple[int, ...]


@dataclass(frozen=True)
class ChunkingConfig:
    """Chunk limits measured in characters, including sentence overlap."""

    max_chunk_chars: int = 8_000
    overlap_chars: int = 400
    max_chunks: int = 16

    def __post_init__(self) -> None:
        if self.max_chunk_chars < 1:
            raise ValueError("max_chunk_chars must be positive.")
        if self.overlap_chars < 0:
            raise ValueError("overlap_chars cannot be negative.")
        if self.max_chunks < 1:
            raise ValueError("max_chunks must be positive.")


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def build_chunks(
    pages: list[PageText] | tuple[PageText, ...],
    config: ChunkingConfig = ChunkingConfig(),
) -> ChunkingResult:
    """Split paragraph then sentence boundaries without cutting sentences.

    A sentence longer than ``max_chunk_chars`` remains whole. Overlap reuses
    complete trailing sentences, so each segment keeps its original page.
    """
    units = [
        ChunkSegment(page_number=page.page_number, text=sentence)
        for page in pages
        for sentence in _sentences(page.text)
    ]
    chunks: list[TextChunk] = []
    current: list[ChunkSegment] = []
    index = 0
    consumed = 0

    for unit_position, unit in enumerate(units):
        if current and _length(current) + _length([unit]) > config.max_chunk_chars:
            chunks.append(_make_chunk(index + 1, current))
            index += 1
            if index >= config.max_chunks:
                break
            current = _overlap_tail(current, config.overlap_chars)
            while (
                current and _length(current) + _length([unit]) > config.max_chunk_chars
            ):
                current.pop(0)
        current.append(unit)
        consumed = unit_position + 1

    if current and len(chunks) < config.max_chunks:
        chunks.append(_make_chunk(len(chunks) + 1, current))

    omitted_pages = tuple(sorted({unit.page_number for unit in units[consumed:]}))
    return ChunkingResult(tuple(chunks), omitted_pages)


def _sentences(text: str) -> list[str]:
    result: list[str] = []
    for paragraph in re.split(r"\n\s*\n+", text):
        paragraph = " ".join(paragraph.split())
        if not paragraph:
            continue
        result.extend(
            sentence for sentence in _SENTENCE_END.split(paragraph) if sentence
        )
    return result


def _length(segments: list[ChunkSegment]) -> int:
    return sum(
        len(f"[Page {segment.page_number}]\n{segment.text}") + 1 for segment in segments
    )


def _overlap_tail(
    segments: list[ChunkSegment], overlap_chars: int
) -> list[ChunkSegment]:
    if overlap_chars == 0:
        return []
    tail: list[ChunkSegment] = []
    size = 0
    for segment in reversed(segments):
        if tail and size >= overlap_chars:
            break
        tail.insert(0, segment)
        size += len(segment.text) + 1
    return tail


def _make_chunk(index: int, segments: list[ChunkSegment]) -> TextChunk:
    page_numbers = tuple(dict.fromkeys(segment.page_number for segment in segments))
    rendered = "\n".join(
        f"[Page {segment.page_number}]\n{segment.text}" for segment in segments
    )
    return TextChunk(index, tuple(segments), page_numbers, rendered)
