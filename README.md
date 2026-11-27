# DocuMind – AI Document Intelligence Platform

**Extract. Understand. Verify.**

DocuMind turns PDF documents into structured, searchable information with source-level evidence. Every extracted fact is linked to the page and the supporting text it came from, so you can check where it came from and whether it holds up.

## Contents

- [Why DocuMind](#why-documind)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Exports](#exports)
- [Development](#development)
- [Tech Stack](#tech-stack)
- [Project Scope](#project-scope)

## Why DocuMind

LLM-based extraction is useful but hard to trust: a result without a source is just a claim. DocuMind keeps every extracted item tied to a page number and a supporting quote, checks that quote against the document, and flags anything that needs a human to look at it.

## Key Features

- **AI-powered extraction:** Facts, entities, dates, concepts and key information from PDFs.
- **Evidence-backed results:** Each item links to a supporting quote and page number.
- **Evidence verification:** Source quotes are checked against the document, and unverified items are flagged for human review.
- **Long-document processing:** Page-aware chunking for large PDFs.
- **Document classification:** Supports CVs, lecture slides, invoices, contracts and general documents.
- **Interactive dashboard:** Explore extracted information and processing coverage.
- **Data export:** Download results as JSON, CSV or Markdown.
- **Offline mode:** Try the full workflow without an API key using the mock provider.

## How It Works

```text
PDF Upload → PDF Ingestion → Document Classification → Page-aware Chunking
           → AI Extraction → Evidence Verification → Dashboard → JSON / CSV / Markdown
```

| Step | What happens |
|---|---|
| PDF Ingestion | Text is read from the PDF page by page, so page numbers are kept. |
| Classification | The document type is detected (CV, lecture slides, invoice, contract or general). |
| Chunking | The text is split into chunks that stay linked to their source pages. |
| Extraction | The AI model extracts facts, entities, dates and concepts as structured, validated data. |
| Verification | Each supporting quote is matched against the source text, and weak matches are flagged. |
| Dashboard | Results, evidence and processing coverage are shown in the Streamlit app. |

## Getting Started

**Requirements:** Python 3.11

**1. Clone the repository**

```bash
git clone https://github.com/0neal264/AI-Document-Intelligence-Platform.git
cd AI-Document-Intelligence-Platform
```

**2. Set up the environment**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**3. Run DocuMind**

```bash
streamlit run app.py
```

DocuMind starts in offline **Mock** mode, so you can try it without an API key.

## Configuration

To use Gemini, create a `.env` file in the project root:

```dotenv
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.5-flash-lite
```

Then select **Gemini Developer API** in the app.

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key. Not needed in Mock mode. |
| `GEMINI_MODEL` | The Gemini model used for extraction. |

Keep your `.env` file out of version control.

## Exports

Results can be downloaded from the dashboard as:

- **JSON** for use in other tools and pipelines
- **CSV** for spreadsheets
- **Markdown** for readable reports

## Development

```bash
pytest
ruff check .
```

## Tech Stack

Python · Streamlit · Google Gemini API · Pydantic · PyPDF · Pytest · Ruff · Docker

## Project Scope

DocuMind is an educational prototype. AI-generated information can contain errors, and evidence matching does not guarantee that an extracted interpretation is correct. Human review remains important.

**The goal:** Make document extraction more transparent, traceable and reliable.
