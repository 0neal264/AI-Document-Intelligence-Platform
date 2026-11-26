"""Streamlit entry point. Business logic belongs in the package modules."""

import streamlit as st

from documind.config import Settings
from documind.extraction.provider import MockProvider
from documind.logging_config import configure_logging

configure_logging()
settings = Settings.from_environment()

st.set_page_config(page_title="DocuMind", page_icon="📄")
st.title("DocuMind")
st.subheader("AI-assisted document intelligence")
st.write(
    "Explore how fictional PDF documents can be turned into structured, "
    "traceable information with human review for uncertain results."
)
st.info(
    "This is a learning prototype. It does not provide regulatory, GxP, "
    "or production compliance."
)
st.caption(f"Current mode: {settings.mode} · Model setting: {settings.model}")

if settings.mode == "demo":
    st.success(MockProvider().extract("").message)
else:
    st.warning("Live extraction will be added in a later milestone.")
