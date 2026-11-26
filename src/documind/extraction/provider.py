"""A tiny provider boundary and deterministic demo implementation."""

from typing import Protocol

from pydantic import BaseModel


class ExtractionResult(BaseModel):
    """Placeholder result shape for the first project milestone."""

    message: str


class ExtractionProvider(Protocol):
    """Common interface that future live and mock providers will implement."""

    def extract(self, text: str) -> ExtractionResult:
        """Return a structured result for document text."""


class MockProvider:
    """Return a fixed response without reading, sending, or logging input text."""

    def extract(self, text: str) -> ExtractionResult:
        del text
        return ExtractionResult(message="Demo mode is ready for document processing.")
