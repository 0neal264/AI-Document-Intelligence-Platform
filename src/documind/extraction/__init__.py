"""Interfaces and implementations for extracting document fields."""

from documind.extraction.cache import ExtractionCache
from documind.extraction.chunking import (
    ChunkingConfig,
    ChunkSegment,
    PageText,
    TextChunk,
    build_chunks,
)
from documind.extraction.gemini import (
    DEFAULT_GEMINI_MODEL,
    GeminiAPIError,
    GeminiConnectionError,
    GeminiProvider,
    GeminiRateLimitError,
    MissingGeminiAPIKeyError,
)
from documind.extraction.profile import (
    DOCUMENT_PROFILES,
    GENERIC_DOCUMENT_PROFILE,
    DocumentProfile,
)
from documind.extraction.provider import (
    ChunkProcessingRecord,
    ChunkProcessingStatus,
    ExtractionError,
    ExtractionProvider,
    ExtractionResult,
    MalformedExtractionError,
    MergeRecord,
    MockProvider,
    PageProcessingRecord,
    PageProcessingStatus,
    ProcessingMetadata,
    SourcedField,
    SourceEvidence,
    TemporaryExtractionError,
)
from documind.extraction.service import ExtractionRunConfig, ExtractionService

__all__ = [
    "DEFAULT_GEMINI_MODEL",
    "DOCUMENT_PROFILES",
    "GENERIC_DOCUMENT_PROFILE",
    "ChunkProcessingRecord",
    "ChunkProcessingStatus",
    "ChunkSegment",
    "ChunkingConfig",
    "DocumentProfile",
    "ExtractionCache",
    "ExtractionError",
    "ExtractionProvider",
    "ExtractionResult",
    "ExtractionRunConfig",
    "ExtractionService",
    "GeminiAPIError",
    "GeminiConnectionError",
    "GeminiProvider",
    "GeminiRateLimitError",
    "MalformedExtractionError",
    "MergeRecord",
    "MissingGeminiAPIKeyError",
    "MockProvider",
    "PageProcessingRecord",
    "PageProcessingStatus",
    "PageText",
    "ProcessingMetadata",
    "SourceEvidence",
    "SourcedField",
    "TemporaryExtractionError",
    "TextChunk",
    "build_chunks",
]
