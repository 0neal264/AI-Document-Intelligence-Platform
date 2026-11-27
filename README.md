# DocuMind – AI Document Intelligence Platform

**Extract. Understand. Verify.**

DocuMind is an AI-powered document intelligence platform that transforms PDF documents into structured, searchable information with source-level evidence.

Instead of simply extracting information, DocuMind connects each extracted fact to its original page and supporting text, helping users understand where information came from and whether it can be verified.

## Key Features

- **AI-powered extraction:** Extract facts, entities, dates, concepts and key information from PDFs.
- **Evidence-backed results:** Link extracted information to supporting quotes and page numbers.
- **Evidence verification:** Check source quotes and flag information requiring human review.
- **Long-document processing:** Process large PDFs using page-aware chunking.
- **Document classification:** Supports CVs, lecture slides, invoices, contracts and general documents.
- **Interactive dashboard:** Explore extracted information and processing coverage.
- **Data export:** Download results as JSON, CSV or Markdown.
- **Offline mode:** Test the workflow without an API key using the mock provider.

## Tech Stack

Python · Streamlit · Google Gemini API · Pydantic · PyPDF · Pytest · Ruff · Docker

## Architecture

\`\`\`text
PDF Upload
    ↓
PDF Ingestion
    ↓
Document Classification
    ↓
Page-aware Chunking
    ↓
AI Extraction
    ↓
Evidence Verification
    ↓
Interactive Dashboard
    ↓
JSON / CSV / Markdown
\`\`\`

## Getting Started

**1. Clone the repository**

\`\`\`bash
git clone https://github.com/0neal264/AI-Document-Intelligence-Platform.git
cd AI-Document-Intelligence-Platform
\`\`\`

**2. Set up the environment**

\`\`\`bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
\`\`\`

**3. Run DocuMind**

\`\`\`bash
streamlit run app.py
\`\`\`

DocuMind starts in offline Mock mode. To enable Gemini, create a `.env` file in the project root:

\`\`\`dotenv
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.5-flash-lite
\`\`\`

Then select **Gemini Developer API** in the application.

## Run Tests

\`\`\`bash
pytest
ruff check .
\`\`\`

## Project Scope

DocuMind is an educational prototype. AI-generated information can contain errors, and evidence matching does not guarantee that an extracted interpretation is correct. Human review remains important.

**The goal:** Make document extraction more transparent, traceable and reliable.
