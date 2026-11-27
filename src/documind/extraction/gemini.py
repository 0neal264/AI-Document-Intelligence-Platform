"""Google Gemini Developer API provider using the official google-genai SDK."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from documind.extraction.provider import (
    _SYSTEM_INSTRUCTIONS,
    ExtractionError,
    ExtractionResult,
    MalformedExtractionError,
    TemporaryExtractionError,
)

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
_LOGGER = logging.getLogger(__name__)


class MissingGeminiAPIKeyError(ExtractionError):
    """Raised when Gemini is selected without a configured API key."""

    safe_for_user = True


class GeminiRateLimitError(ExtractionError):
    """Raised when Gemini free-tier quota or rate limits are reached."""

    safe_for_user = True

    def __init__(self, message: str, *, quota_exhausted: bool = False) -> None:
        super().__init__(message)
        self.quota_exhausted = quota_exhausted
        self.retryable = not quota_exhausted


class GeminiConnectionError(TemporaryExtractionError):
    """Raised when the Gemini API cannot be reached."""

    safe_for_user = True


class GeminiAPIError(ExtractionError):
    """Raised for other Gemini API errors without exposing SDK details."""

    safe_for_user = True

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class GeminiProvider:
    """Generate source-grounded structured extractions with Gemini."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = DEFAULT_GEMINI_MODEL,
        timeout_ms: int = 60_000,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self._api_key_for_redaction = api_key
        if client is not None:
            self._client = client
        else:
            if not api_key:
                raise MissingGeminiAPIKeyError(
                    "Add GEMINI_API_KEY to your local .env file to use Gemini."
                )
            retry_options = types.HttpRetryOptions(attempts=1)
            self._client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    timeout=timeout_ms,
                    retry_options=retry_options,
                ),
            )
        self._config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTIONS,
            response_mime_type="application/json",
            response_json_schema=_gemini_json_schema(),
            temperature=0,
            max_output_tokens=8192,
        )

    def extract(self, text: str) -> ExtractionResult:
        """Generate and validate structured extraction data without retries."""
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=text,
                config=self._config,
            )
        except errors.ClientError as exc:
            detail = _safe_api_detail(
                getattr(exc, "message", None),
                document_text=text,
                api_key=getattr(self, "_api_key_for_redaction", None),
            )
            _LOGGER.warning(
                "Gemini API client error: code=%s status=%s message=%s",
                exc.code,
                exc.status,
                detail or "No API error message was provided.",
            )
            if exc.code == 429:
                raw_message = getattr(exc, "message", "")
                quota_exhausted = isinstance(raw_message, str) and any(
                    marker in raw_message.lower()
                    for marker in ("quota", "per day", "daily limit", "exhausted")
                )
                raise GeminiRateLimitError(
                    "Gemini free-tier quota is exhausted. Check AI Studio usage "
                    "and wait for the quota to reset. DocuMind will not switch "
                    "providers."
                    if quota_exhausted
                    else "Gemini rate limit reached. DocuMind may retry a limited "
                    "number of times; check AI Studio usage if this continues.",
                    quota_exhausted=quota_exhausted,
                ) from None
            if exc.code in {401, 403}:
                if detail:
                    raise GeminiAPIError(
                        f"Gemini API returned HTTP {exc.code}: {_short_reason(detail)}"
                    ) from None
                raise GeminiAPIError(
                    "Gemini rejected this request. Check the API key and model "
                    "access in Google AI Studio."
                ) from None
            if detail:
                raise GeminiAPIError(
                    f"Gemini API returned HTTP {exc.code}: {_short_reason(detail)}",
                    retryable=exc.code >= 500,
                ) from None
            raise GeminiAPIError(
                f"Gemini API returned HTTP {exc.code} ({exc.status or 'unknown status'}).",
                retryable=exc.code >= 500,
            ) from None
        except (httpx.TimeoutException, httpx.RequestError, TimeoutError, OSError):
            raise GeminiConnectionError(
                "Could not connect to the Gemini API. Check your connection and "
                "try again."
            ) from None
        except errors.UnknownApiResponseError:
            raise MalformedExtractionError(
                "Gemini returned an invalid API response."
            ) from None
        except (ValidationError, ValueError):
            raise MalformedExtractionError(
                "Gemini returned data that does not match the extraction schema."
            ) from None

        try:
            parsed = getattr(response, "parsed", None)
        except (AttributeError, ValueError):
            parsed = None
        if isinstance(parsed, ExtractionResult):
            return parsed
        if isinstance(parsed, dict):
            try:
                return ExtractionResult.model_validate(parsed)
            except ValidationError:
                raise MalformedExtractionError(
                    "Gemini returned data that does not match the extraction schema."
                ) from None

        try:
            response_text = getattr(response, "text", None)
        except (AttributeError, ValueError):
            response_text = None
        if not isinstance(response_text, str) or not response_text.strip():
            raise MalformedExtractionError(
                "Gemini returned no structured extraction result."
            )
        try:
            return ExtractionResult.model_validate_json(response_text)
        except (ValidationError, ValueError):
            raise MalformedExtractionError(
                "Gemini returned data that does not match the extraction schema."
            ) from None


def _safe_api_detail(
    message: object,
    *,
    document_text: str,
    api_key: str | None,
) -> str:
    """Return a short API explanation with submitted secrets removed."""
    if not isinstance(message, str):
        return ""

    safe_message = message
    for sensitive_value in (api_key, document_text):
        if sensitive_value:
            safe_message = safe_message.replace(sensitive_value, "[redacted]")

    for line in document_text.splitlines():
        source_line = line.strip()
        if source_line:
            safe_message = safe_message.replace(source_line, "[document text redacted]")

    return " ".join(safe_message.split())[:500]


def _short_reason(detail: str) -> str:
    """Keep API diagnostics useful in the UI without displaying long payloads."""
    return detail[:180].rstrip()


def _gemini_json_schema() -> dict[str, Any]:
    """Build the supported Gemini JSON Schema subset from the shared model.

    ``response_json_schema`` accepts JSON Schema field names, including
    ``additionalProperties``. The SDK's ``response_schema`` converter instead
    maps Pydantic's ``extra='forbid'`` to an ``additional_properties`` field,
    which Gemini rejects in ``generation_config.response_schema``. Keep the
    supported JSON Schema constraint that forbids extra fields, while removing
    Pydantic defaults and ``minLength`` (not supported by Gemini's subset).
    The response still gets full Pydantic validation locally.
    """
    schema = ExtractionResult.model_json_schema()

    def simplify(node: dict[str, Any]) -> None:
        node.pop("default", None)
        node.pop("minLength", None)
        properties = node.get("properties")
        if isinstance(properties, dict):
            for pipeline_field in (
                "pdf_metadata",
                "processing",
                "verified",
                "needs_review",
            ):
                properties.pop(pipeline_field, None)
                required = node.get("required")
                if isinstance(required, list) and pipeline_field in required:
                    required.remove(pipeline_field)
        for value in node.values():
            if isinstance(value, dict):
                simplify(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        simplify(item)

    simplify(schema)
    definitions = schema.get("$defs")
    if isinstance(definitions, dict):
        references: set[str] = set()

        def collect_references(node: object) -> None:
            if isinstance(node, dict):
                reference = node.get("$ref")
                if isinstance(reference, str) and reference.startswith("#/$defs/"):
                    references.add(reference.removeprefix("#/$defs/"))
                for value in node.values():
                    collect_references(value)
            elif isinstance(node, list):
                for value in node:
                    collect_references(value)

        root_schema = {key: value for key, value in schema.items() if key != "$defs"}
        collect_references(root_schema)
        while True:
            previous_count = len(references)
            for name in tuple(references):
                definition = definitions.get(name)
                if definition is not None:
                    collect_references(definition)
            if len(references) == previous_count:
                break
        schema["$defs"] = {
            name: value for name, value in definitions.items() if name in references
        }
        if not schema["$defs"]:
            schema.pop("$defs")
    return schema
