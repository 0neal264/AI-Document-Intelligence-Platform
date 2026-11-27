"""Streamlit entry point for the DocuMind extraction dashboard."""

from __future__ import annotations

import hashlib

import streamlit as st

from documind.config import Settings
from documind.extraction import (
    DOCUMENT_PROFILES,
    ExtractionError,
    ExtractionService,
    GeminiConnectionError,
    GeminiProvider,
    GeminiRateLimitError,
    MissingGeminiAPIKeyError,
    MockProvider,
)
from documind.ingestion import PDFIngestionError, ingest_pdf
from documind.logging_config import configure_logging
from documind.ui.dashboard import render_dashboard
from documind.ui.styles import dashboard_styles

configure_logging()
settings = Settings.from_environment()

st.set_page_config(page_title="DocuMind", layout="wide")
st.markdown(dashboard_styles(), unsafe_allow_html=True)


def _provider_label(value: str) -> str:
    return "Mock (offline)" if value == "mock" else "Gemini Developer API"


def _profile_label(value: str) -> str:
    return "Auto detect" if value == "auto" else value.replace("_", " ").title()


def _show_landing_header() -> None:
    st.markdown(
        '<div class="dm-header"><div><h1 class="dm-wordmark">DocuMind</h1>'
        '<p class="dm-tagline">Document intelligence with source evidence</p></div>'
        '<div class="dm-prototype">Prototype for fictional documents</div></div>',
        unsafe_allow_html=True,
    )


with st.sidebar.expander("Provider and settings", expanded=False):
    provider_choice = st.selectbox(
        "Extraction provider",
        options=("mock", "gemini"),
        index=("mock", "gemini").index(
            settings.extraction_provider
            if settings.extraction_provider in {"mock", "gemini"}
            else "mock"
        ),
        format_func=_provider_label,
    )
    profile_choice = st.selectbox(
        "Document profile",
        options=("auto", *DOCUMENT_PROFILES),
        format_func=_profile_label,
        help="Auto detect from the opening pages or choose a profile manually.",
    )
    if provider_choice == "gemini":
        if settings.gemini_api_key:
            st.caption(f"Model: {settings.gemini_model}")
        else:
            st.warning("Add GEMINI_API_KEY to your .env file to enable Gemini.")
        st.caption(
            "Document text is sent to Google. Free-tier limits apply; DocuMind "
            "does not switch providers automatically."
        )
    else:
        st.caption("Mock runs offline and needs no API key.")

st.markdown('<div class="section-title">Document</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
display_result = None

if uploaded_file is None:
    _show_landing_header()
    st.info("Upload a PDF to see its extracted facts, evidence, and page coverage.")
    st.session_state.pop("_documind_upload_hash", None)
    st.session_state.pop("_documind_result_hash", None)
    st.session_state.pop("_documind_result", None)
else:
    file_bytes = uploaded_file.getvalue()
    upload_hash = hashlib.sha256(
        uploaded_file.name.encode("utf-8") + b"\0" + file_bytes
    ).hexdigest()
    if st.session_state.get("_documind_upload_hash") != upload_hash:
        st.session_state["_documind_upload_hash"] = upload_hash
        st.session_state.pop("_documind_result_hash", None)
        st.session_state.pop("_documind_result", None)

    try:
        document = ingest_pdf(file_bytes, uploaded_file.name)
    except PDFIngestionError:
        _show_landing_header()
        st.error(
            "DocuMind could not read this PDF. Check that it is a valid, "
            "unencrypted PDF within the upload size limit."
        )
    else:
        st.caption(f"{document.filename} · {document.page_count} pages ready")
        if st.button(
            "Process document",
            type="primary",
            disabled=provider_choice == "gemini" and not settings.gemini_api_key,
        ):
            st.session_state.pop("_documind_result", None)
            st.session_state.pop("_documind_result_hash", None)
            if provider_choice == "mock":
                provider = MockProvider()
            else:
                provider = GeminiProvider(
                    model=settings.gemini_model,
                    api_key=settings.gemini_api_key,
                )
            progress = st.progress(0, text="Preparing extraction")

            def update_progress(completed: int, total: int, label: str) -> None:
                fraction = completed / total if total else 1.0
                progress.progress(min(fraction, 1.0), text=label)

            try:
                result = ExtractionService(
                    provider,
                    profile=profile_choice,
                    progress_callback=update_progress,
                ).extract_document(document)
            except MissingGeminiAPIKeyError:
                st.error("Add GEMINI_API_KEY to your .env file, then restart DocuMind.")
            except GeminiRateLimitError as exc:
                st.error(str(exc))
            except GeminiConnectionError:
                st.error(
                    "Gemini could not be reached. Check your connection and retry."
                )
            except ExtractionError as exc:
                st.error(str(exc))
            except ValueError:
                st.error(
                    "The selected profile or Gemini configuration is invalid. "
                    "Review the settings and try again."
                )
            else:
                st.session_state["_documind_result"] = result
                st.session_state["_documind_result_hash"] = upload_hash
                display_result = result

        if display_result is None:
            stored_hash = st.session_state.get("_documind_result_hash")
            if stored_hash == upload_hash:
                display_result = st.session_state.get("_documind_result")
        if display_result is not None:
            render_dashboard(display_result)
        else:
            if provider_choice == "mock":
                _show_landing_header()
                st.caption("Mock is selected. It can run the extraction flow offline.")
            else:
                _show_landing_header()
                st.info("Process the document to build its dashboard.")

st.markdown(
    '<div class="dm-footer">Prototype for demonstration with fictional documents</div>',
    unsafe_allow_html=True,
)
