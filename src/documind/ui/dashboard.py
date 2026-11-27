"""Streamlit rendering for the validated extraction result model."""

from __future__ import annotations

from html import escape

import streamlit as st

from documind.extraction.provider import ExtractionResult
from documind.ui.view_model import (
    DashboardView,
    EvidenceView,
    FactView,
    build_dashboard_view,
    category_counts,
    coverage_summary,
    date_display,
    export_csv,
    export_json,
    export_markdown,
    filter_facts,
    group_items,
    narrative_summary,
)


def render_dashboard(result: ExtractionResult) -> None:
    """Render the result dashboard; view calculations remain in view_model."""
    view = build_dashboard_view(result)
    with st.sidebar:
        _render_sidebar(view, result)
    _render_main(view, result)


def _render_sidebar(view: DashboardView, result: ExtractionResult) -> None:
    st.markdown('<h1 class="dm-wordmark">DocuMind</h1>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sidebar-title">{escape(view.title)}</div>', unsafe_allow_html=True
    )
    identity = " · ".join(
        value for value in (view.document_type, view.organisation) if value
    )
    st.markdown(
        f'<div class="sidebar-muted">{escape(identity or "Document details unavailable")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sidebar-heading">Page coverage</div>', unsafe_allow_html=True
    )
    cells = []
    for page in view.page_cells:
        status = (
            page.status
            if page.status in {"processed", "low_text", "empty", "failed"}
            else "failed"
        )
        mark = "×" if status == "failed" else str(page.page_number)
        cells.append(
            f'<span class="coverage-cell {status}" title="Page {page.page_number}: {status}">{mark}</span>'
        )
    if cells:
        st.markdown(
            f'<div class="coverage-map">{"".join(cells)}</div>', unsafe_allow_html=True
        )
        st.caption("Processed · Low text · Empty · Failed (×)")
        coverage = coverage_summary(view)
        st.markdown(
            f'<div class="coverage-status">{escape(coverage.status_text)}</div>',
            unsafe_allow_html=True,
        )
        page_options = ("All pages", *(cell.page_number for cell in view.page_cells))
        st.selectbox(
            "Filter by page",
            page_options,
            key=f"dashboard-page-{result.document_id or result.filename or 'result'}",
        )
    else:
        st.caption("Page coverage unavailable")

    st.markdown('<div class="sidebar-heading">Categories</div>', unsafe_allow_html=True)
    counts = category_counts(view.facts)
    categories = ("All", *counts)
    st.radio(
        "Filter facts by category",
        categories,
        label_visibility="collapsed",
        key=f"dashboard-category-{result.document_id or result.filename or 'result'}",
        format_func=lambda item: (
            f"{item}  ·  {sum(counts.values()) if item == 'All' else counts[item]}"
        ),
    )


def _render_main(view: DashboardView, result: ExtractionResult) -> None:
    tabs = st.tabs(
        ("Overview", "Facts", "Entities and dates", "Evidence", "Processing", "Export")
    )
    with tabs[0]:
        _render_overview(view)
    with tabs[1]:
        _render_facts(view, result)
    with tabs[2]:
        _render_entities_and_dates(view)
    with tabs[3]:
        _render_evidence(view)
    with tabs[4]:
        _render_processing(result)
    with tabs[5]:
        _render_exports(result, view)


def _render_overview(view: DashboardView) -> None:
    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
    if not view.summary_facts and not view.summary_concepts and not view.dates:
        st.info("No facts, concepts, or dates were extracted from this document.")
        return
    st.write(narrative_summary(view))
    for label, items in (
        ("Key facts", view.summary_facts),
        ("Key concepts", view.summary_concepts),
        ("Key dates", view.dates),
    ):
        if items:
            st.markdown(f"**{label}**")
            _render_fact_table(items[:5], f"overview-{label}")


def _render_facts(view: DashboardView, result: ExtractionResult) -> None:
    st.markdown('<div class="section-title">Facts</div>', unsafe_allow_html=True)
    query = st.text_input("Search facts", placeholder="Search statements and evidence")
    category_choice = st.session_state.get(
        f"dashboard-category-{result.document_id or result.filename or 'result'}", "All"
    )
    page_choice = st.session_state.get(
        f"dashboard-page-{result.document_id or result.filename or 'result'}",
        "All pages",
    )
    filtered = filter_facts(
        view.facts,
        query=query,
        category=None if category_choice == "All" else category_choice,
        page_number=None if page_choice == "All pages" else page_choice,
    )
    if filtered:
        _render_fact_table(filtered, "facts")
    else:
        st.info("No facts match these filters.")


def _render_fact_table(
    items: tuple[FactView, ...] | list[FactView], key_prefix: str
) -> None:
    rows = [
        '<div class="facts-table"><div class="facts-head"><span>Statement</span><span>Category</span><span>Page</span><span>Evidence</span></div>'
    ]
    for item in items:
        marker = " needs-review" if item.needs_review else ""
        pages = ", ".join(map(str, item.page_numbers)) or "—"
        state = (
            "Needs review"
            if item.needs_review
            else (
                "Verified"
                if item.evidence and all(e.verified is True for e in item.evidence)
                else "Not checked"
            )
        )
        state_class = (
            "review-chip"
            if item.needs_review
            else ("verified-text" if state == "Verified" else "muted")
        )
        rows.append(
            f'<div class="fact-grid-row{marker}"><span class="statement">{escape(item.statement)}</span><span>{escape(item.category)}</span><span>{escape(pages)}</span><span class="{state_class}">{state}</span></div>'
        )
    rows.append("</div>")
    st.markdown(
        f'<div class="table-scroll">{"".join(rows)}</div>', unsafe_allow_html=True
    )
    for index, item in enumerate(items):
        if item.evidence:
            with st.expander(
                f"Source evidence · {item.statement[:65]}",
                key=f"{key_prefix}-evidence-{index}-{item.source_field}",
            ):
                _render_evidence_entries(item.evidence)


def _render_entities_and_dates(view: DashboardView) -> None:
    st.markdown(
        '<div class="section-title">Entities and dates</div>', unsafe_allow_html=True
    )
    entities, dates = st.columns(2)
    with entities:
        st.markdown("**Entities**")
        _render_grouped(view.entities)
    with dates:
        st.markdown("**Dates**")
        if not view.dates:
            st.caption("No dates extracted.")
        for index, item in enumerate(view.dates):
            formatted = date_display(item)
            date_label = formatted.iso_date or formatted.original_text
            suffix = (
                f" · Original text: {formatted.original_text}"
                if formatted.iso_date
                else ""
            )
            st.markdown(
                f"**{escape(formatted.label)}:** {escape(date_label)}{escape(suffix)}"
            )
            _render_fact_table((item,), f"date-{item.category}-{index}")


def _render_evidence(view: DashboardView) -> None:
    st.markdown('<div class="section-title">Evidence</div>', unsafe_allow_html=True)
    entries = [evidence for item in view.all_items for evidence in item.evidence]
    if not entries:
        st.info("No source evidence is available.")
        return
    for entry in entries:
        _render_evidence_entries((entry,))


def _render_evidence_entries(entries: tuple[EvidenceView, ...]) -> None:
    for entry in entries:
        status = (
            "Verified"
            if entry.verified is True
            else "Needs review"
            if entry.needs_review or entry.verified is False
            else "Not checked"
        )
        quote = _highlight_quote(entry.quote, entry.statement, entry.verified is True)
        st.markdown(
            f'<div class="evidence-card"><div class="evidence-quote">{quote}</div><div class="evidence-meta"><span class="page-badge">Page {entry.page_number}</span><span class="{"verified-text" if status == "Verified" else "review-chip" if status == "Needs review" else "muted"}">{status}</span></div></div>',
            unsafe_allow_html=True,
        )


def _highlight_quote(quote: str, statement: str, verified: bool) -> str:
    safe_quote = escape(quote)
    if verified:
        return f"<mark>{safe_quote}</mark>"
    needle = statement.strip()
    if needle and needle.casefold() in quote.casefold():
        start = quote.casefold().index(needle.casefold())
        end = start + len(needle)
        return f"{escape(quote[:start])}<mark>{escape(quote[start:end])}</mark>{escape(quote[end:])}"
    return safe_quote


def _render_grouped(items: tuple[FactView, ...]) -> None:
    if not items:
        st.caption("No items extracted.")
        return
    for category, group in group_items(items).items():
        st.markdown(f"**{escape(category)}**")
        _render_fact_table(group, f"group-{category}")


def _render_processing(result: ExtractionResult) -> None:
    processing = result.processing
    st.markdown('<div class="section-title">Processing</div>', unsafe_allow_html=True)
    if processing is None:
        st.info("Processing details are not available for this result.")
        return
    if processing.message:
        st.info(processing.message)
    page_rows = [record.model_dump(mode="json") for record in processing.page_records]
    if page_rows:
        st.markdown("**Page status**")
        st.dataframe(page_rows, hide_index=True, use_container_width=True)
    chunks = []
    if processing.classification:
        chunks.append(
            {
                "stage": "Profile detection",
                **processing.classification.model_dump(mode="json"),
            }
        )
    chunks.extend(
        {"stage": "Extraction", **record.model_dump(mode="json")}
        for record in processing.chunks
    )
    if chunks:
        st.markdown("**Chunks and attempts**")
        st.dataframe(chunks, hide_index=True, use_container_width=True)
    if processing.merge_log:
        st.markdown("**Merge log**")
        st.dataframe(
            [record.model_dump(mode="json") for record in processing.merge_log],
            hide_index=True,
            use_container_width=True,
        )
    if processing.uncovered_pages:
        st.warning(
            "Pages not covered: " + ", ".join(map(str, processing.uncovered_pages))
        )


def _render_exports(result: ExtractionResult, view: DashboardView) -> None:
    st.markdown('<div class="section-title">Export</div>', unsafe_allow_html=True)
    for label, data, filename, mime in (
        (
            "Download JSON",
            export_json(result),
            "documind-result.json",
            "application/json",
        ),
        (
            "Download facts CSV",
            export_csv(view.facts),
            "documind-facts.csv",
            "text/csv",
        ),
        (
            "Download Markdown",
            export_markdown(result, view),
            "documind-report.md",
            "text/markdown",
        ),
    ):
        st.download_button(label, data, filename, mime)
    st.caption(
        "Exports are generated from this result and make no additional API calls."
    )
