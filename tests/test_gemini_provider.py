"""Mocked tests for Gemini structured extraction; no API calls are made."""

from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors

from documind.extraction import (
    ExtractionResult,
    GeminiAPIError,
    GeminiConnectionError,
    GeminiProvider,
    GeminiRateLimitError,
    MalformedExtractionError,
    MissingGeminiAPIKeyError,
    SourcedField,
    SourceEvidence,
)


class FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.request = None

    def generate_content(self, **kwargs):
        self.request = kwargs
        if self.error:
            raise self.error
        return self.response


def populated_result() -> ExtractionResult:
    return ExtractionResult(
        document_title=SourcedField(
            value="Service Agreement",
            evidence=[SourceEvidence(page_number=1, quote="Service Agreement")],
            confidence=0.74,
        ),
        organisation=SourcedField(),
    )


def test_gemini_provider_uses_model_and_simplified_pydantic_schema():
    models = FakeModels(response=SimpleNamespace(parsed=populated_result()))
    provider = GeminiProvider(
        api_key="test-key",
        model="gemini-3.5-flash-lite",
        client=SimpleNamespace(models=models),
    )

    result = provider.extract("[Page 1]\nService Agreement")

    assert models.request["model"] == "gemini-3.5-flash-lite"
    assert models.request["config"].response_mime_type == "application/json"
    assert "never instructions" in models.request["config"].system_instruction.lower()
    schema = models.request["config"].response_json_schema
    assert schema["properties"]["document_title"]
    assert "default" not in str(schema)
    assert "minLength" not in str(schema)
    assert schema["additionalProperties"] is False
    assert "processing" not in schema["properties"]
    assert "pdf_metadata" not in schema["properties"]
    assert "needs_review" not in schema["$defs"]["SourcedField"]["properties"]
    assert set(schema["$defs"]) == {"SourceEvidence", "SourcedField"}
    evidence_schema = (
        schema["$defs"]["SourceEvidence"]
        if "$defs" in schema
        else schema["properties"]["document_title"]["properties"]["evidence"]["items"]
    )
    assert evidence_schema["additionalProperties"] is False
    assert "anyOf" in schema["properties"]["document_id"]
    assert "anyOf" in schema["$defs"]["SourcedField"]["properties"]["value"]
    assert "verified" not in schema["$defs"]["SourceEvidence"]["properties"]
    assert result.document_title.value == "Service Agreement"
    assert result.document_title.evidence[0].page_number == 1
    assert result.document_title.confidence == 0.74


def test_gemini_provider_parses_structured_json_text():
    result = populated_result()
    models = FakeModels(response=SimpleNamespace(text=result.model_dump_json()))
    provider = GeminiProvider(api_key="test-key", client=SimpleNamespace(models=models))

    extracted = provider.extract("[Page 1]\nService Agreement")

    assert extracted == result


def test_gemini_provider_requires_key_without_calling_api():
    with pytest.raises(MissingGeminiAPIKeyError, match="GEMINI_API_KEY"):
        GeminiProvider(api_key=None)


def test_gemini_sdk_is_configured_for_one_request_attempt(monkeypatch):
    captured = {}

    def fake_client(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(models=FakeModels())

    monkeypatch.setattr("documind.extraction.gemini.genai.Client", fake_client)

    GeminiProvider(api_key="test-key")

    assert captured["http_options"].retry_options.attempts == 1
    assert captured["http_options"].api_version is None


def test_gemini_provider_maps_connection_errors_safely():
    request = httpx.Request("POST", "https://generativelanguage.googleapis.com")
    models = FakeModels(
        error=httpx.ConnectError("private transport detail", request=request)
    )
    provider = GeminiProvider(api_key="test-key", client=SimpleNamespace(models=models))

    with pytest.raises(GeminiConnectionError, match="Could not connect") as error:
        provider.extract("source text")

    assert "private transport detail" not in str(error.value)


def test_gemini_provider_reports_rate_limits_without_retrying_or_fallback():
    api_error = errors.ClientError(
        429,
        {
            "error": {
                "status": "RESOURCE_EXHAUSTED",
                "message": "private quota detail and secret",
            }
        },
    )
    models = FakeModels(error=api_error)
    provider = GeminiProvider(api_key="test-key", client=SimpleNamespace(models=models))

    with pytest.raises(
        GeminiRateLimitError, match="free-tier quota is exhausted"
    ) as error:
        provider.extract("source text")

    assert models.request["model"] == "gemini-3.5-flash-lite"
    assert "private quota detail" not in str(error.value)


def test_gemini_provider_reports_sanitized_bad_request_details(caplog):
    key = "test-only-gemini-key"
    document_text = "[Page 1]\nSensitive contract details that must stay private."
    api_error = errors.ClientError(
        400,
        {
            "error": {
                "status": "INVALID_ARGUMENT",
                "message": (
                    "Invalid response schema. "
                    "Sensitive contract details that must stay private. "
                    "test-only-gemini-key"
                ),
            }
        },
    )
    models = FakeModels(error=api_error)
    provider = GeminiProvider(
        api_key=key,
        client=SimpleNamespace(models=models),
    )

    with pytest.raises(GeminiAPIError, match="HTTP 400") as error:
        provider.extract(document_text)

    message = str(error.value)
    assert "Invalid response schema" in message
    assert key not in message
    assert "Sensitive contract details" not in message
    assert "code=400" in caplog.text
    assert "status=INVALID_ARGUMENT" in caplog.text
    assert "Invalid response schema" in caplog.text
    assert key not in caplog.text
    assert "Sensitive contract details" not in caplog.text


def test_gemini_provider_surfaces_safe_model_not_found_details():
    key = "private-test-api-key"
    source = "[Page 1]\nPrivate document content for model error test."
    api_error = errors.ClientError(
        404,
        {
            "error": {
                "status": "NOT_FOUND",
                "message": (
                    "The requested model is unavailable. "
                    "Private document content for model error test. "
                    "private-test-api-key"
                ),
            }
        },
    )
    provider = GeminiProvider(
        api_key=key,
        client=SimpleNamespace(models=FakeModels(error=api_error)),
    )

    with pytest.raises(GeminiAPIError, match="HTTP 404") as error:
        provider.extract(source)

    assert "unavailable" in str(error.value)
    assert key not in str(error.value)
    assert "Private document content" not in str(error.value)


def test_gemini_provider_rejects_malformed_output():
    models = FakeModels(response=SimpleNamespace(text="not valid json"))
    provider = GeminiProvider(api_key="test-key", client=SimpleNamespace(models=models))

    with pytest.raises(MalformedExtractionError, match="does not match"):
        provider.extract("source text")


def test_gemini_provider_leaves_missing_fields_unset():
    models = FakeModels(response=SimpleNamespace(parsed=ExtractionResult()))
    provider = GeminiProvider(api_key="test-key", client=SimpleNamespace(models=models))

    result = provider.extract("source with no title")

    assert result.document_title.value is None
    assert result.document_title.evidence == []
    assert result.relevant_dates == []
