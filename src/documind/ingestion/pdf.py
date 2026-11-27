"""PDF ingestion without dependencies on the UI or extraction providers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO
from typing import Any
from uuid import uuid4

from pypdf import PdfReader
from pypdf.errors import PdfReadError

DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class PDFIngestionError(ValueError):
    """Base exception for invalid or unreadable PDF uploads."""


class InvalidPDFTypeError(PDFIngestionError):
    """Raised when the filename or file contents are not a PDF."""


class UploadTooLargeError(PDFIngestionError):
    """Raised when an upload exceeds the configured byte limit."""


class EncryptedPDFError(PDFIngestionError):
    """Raised when an encrypted PDF cannot be read without a password."""


class InvalidPDFError(PDFIngestionError):
    """Raised when a PDF is empty, malformed, or cannot be parsed."""


class ExtractionStatus(StrEnum):
    EXTRACTED = "extracted"
    EMPTY = "empty"
    FAILED = "failed"


@dataclass(frozen=True)
class Page:
    """Extracted text and outcome for one 1-indexed PDF page."""

    page_number: int
    extracted_text: str
    extraction_status: ExtractionStatus
    error: str | None = None


@dataclass(frozen=True)
class Document:
    """Structured, source-aware result of ingesting a PDF."""

    document_id: str
    filename: str
    page_count: int
    metadata: dict[str, str | None]
    pages: tuple[Page, ...]


def ingest_pdf(
    content: bytes,
    filename: str,
    *,
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> Document:
    """Validate and extract a PDF, recording each page's extraction outcome.

    The upload limit is configurable per call. Page-level extraction failures
    are represented explicitly in the returned page instead of being skipped.
    """
    if not filename.lower().endswith(".pdf"):
        raise InvalidPDFTypeError("Upload must have a .pdf filename extension.")
    if max_upload_bytes <= 0:
        raise ValueError("max_upload_bytes must be greater than zero.")
    if len(content) > max_upload_bytes:
        raise UploadTooLargeError(
            f"PDF is {len(content)} bytes; limit is {max_upload_bytes} bytes."
        )
    if not content or b"%PDF-" not in content[:1024]:
        raise InvalidPDFTypeError("File does not contain a PDF signature.")

    try:
        reader = PdfReader(BytesIO(content), strict=True)
        if reader.is_encrypted:
            raise EncryptedPDFError("Encrypted PDFs are not supported.")
        page_count = len(reader.pages)
        metadata = _metadata_dict(reader.metadata)
    except EncryptedPDFError:
        raise
    except (PdfReadError, OSError, ValueError, KeyError) as exc:
        raise InvalidPDFError(f"Could not read PDF: {exc}") from exc

    extracted_pages: list[Page] = []
    for index, pdf_page in enumerate(reader.pages, start=1):
        try:
            text = pdf_page.extract_text()
        # pypdf does not expose a stable, complete exception set for malformed
        # page content. Keep this boundary local and record every parser failure.
        except Exception as exc:  # noqa: BLE001
            extracted_pages.append(
                Page(
                    page_number=index,
                    extracted_text="",
                    extraction_status=ExtractionStatus.FAILED,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue
        normalized_text = text or ""
        extracted_pages.append(
            Page(
                page_number=index,
                extracted_text=normalized_text,
                extraction_status=(
                    ExtractionStatus.EXTRACTED
                    if normalized_text.strip()
                    else ExtractionStatus.EMPTY
                ),
            )
        )

    return Document(
        document_id=str(uuid4()),
        filename=filename,
        page_count=page_count,
        metadata=metadata,
        pages=tuple(extracted_pages),
    )


def _metadata_dict(metadata: Any) -> dict[str, str | None]:
    if metadata is None:
        return {}
    return {
        str(key).removeprefix("/"): None if value is None else str(value)
        for key, value in metadata.items()
    }
