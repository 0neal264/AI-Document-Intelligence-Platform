# DocuMind

DocuMind is a portfolio prototype that explores turning fictional PDF documents
into structured, validated, traceable data with a human review step. It is being
built in small milestones so each part stays understandable and explainable.

> This is an educational prototype using fictional data. It does not claim
> regulatory, GxP, or production compliance.

## Gemini extraction

DocuMind defaults to `MockProvider`, which needs no credentials or network
service. Select **Gemini Developer API** in the app to extract a document with
Google's Gemini API. The default model is `gemini-3.5-flash-lite`; inference is
provided by Google, not run locally.

## Milestone 2: PDF ingestion

The `documind.ingestion` package validates PDF uploads and extracts text page
by page using pypdf. `ingest_pdf(content, filename)` returns a document ID,
filename, page count, normalized PDF metadata, and 1-indexed page results.
Each page reports `extracted`, `empty`, or `failed`; page extraction errors are
retained on the page instead of being skipped. Invalid file types, malformed
PDFs, encrypted PDFs, and files over the configured size limit raise clear
ingestion exceptions. The default upload limit is 10 MiB and can be changed per
call with `max_upload_bytes`. This module does not depend on Streamlit or an
LLM provider.

## Create a Gemini API key

Create a key in [Google AI Studio](https://aistudio.google.com/app/apikey),
then configure DocuMind with a root `.env` file. `.env` is ignored by Git.

```dotenv
APP_ENV=development
EXTRACTION_PROVIDER=mock
GEMINI_API_KEY=your-google-ai-studio-key
GEMINI_MODEL=gemini-3.5-flash-lite
```

Hosting environment variables take precedence over `.env`. You can also
select **Gemini Developer API** in the Streamlit provider selector. If
`GEMINI_API_KEY` is missing, the interface explains how to configure it and
keeps Gemini processing disabled. The API key is never displayed or logged.

Do not enable paid billing for the Google AI Studio project if you want to
avoid paid API usage. Gemini free-tier availability and request/token limits
are restricted, vary by model and project, and can change; usage is not
unlimited. Check the [current Gemini API pricing and free-tier details](https://ai.google.dev/gemini-api/docs/pricing)
and the [AI Studio rate limits for your project](https://aistudio.google.com/rate-limit).
DocuMind makes a bounded number of requests for each explicit processing
action, retries only temporary failures within a small configured limit, and
does not switch providers. It cannot prevent charges if billing is enabled on
the Google project.

Gemini requests send extracted PDF text to Google. Google documents that free
tier content may be used to improve its products; do not submit confidential
or sensitive documents unless permitted by your policies. See Google's
[Gemini API additional terms](https://ai.google.dev/gemini-api/terms).

## Page-aware extraction

The extraction service uses a bounded map/reduce workflow. In **Auto detect**
mode, it uses one request on the first readable pages to choose a profile, then
extracts each text chunk. You can instead select `general`, `cv`,
`lecture_slides`, `invoice`, or `contract` in the app. Profiles live as data in
`documind.extraction.profile`; they suggest categories but do not require the
model to fill unsupported fields.

Chunking is measured in characters. Defaults are 8,000 characters per chunk,
400 characters of sentence overlap, and at most 16 chunks. The run allows at
most 18 provider requests, including profile detection and bounded retries.
Three attempts are allowed for temporary errors, with exponential backoff and
jitter; HTTP 400 errors are not retried. A recognized exhausted quota stops
the run immediately. There is no provider switching. These limits bound work
but do not guarantee a specific request count for a document: page lengths,
sentence boundaries, profile detection, cache hits, and retries all affect it.

Pages are split on paragraphs and sentence boundaries. One sentence longer
than the chunk size remains intact. Every source segment keeps its original
page number. Empty, low-text, and failed pages are listed separately in result
processing metadata. If a chunk fails or a configured cap leaves content
unprocessed, successful results are retained and the result is marked partial
with the affected page numbers.

Successful structured chunk responses are cached locally under
`.documind-cache/`. The cache key includes a document-content hash, chunk index,
profile, configured model, prompt version, and chunk-content hash. This lets a
rerun reuse completed chunks. Cache files include extracted values and evidence
quotes, so treat that directory as sensitive local data. Remove it to clear
cached results. The cache is ignored by Git.

Repeated list items merge only when their category and text match after case,
whitespace, and punctuation normalization. The engine keeps all page quotes
when it merges. Similar but non-identical facts remain separate. After merging,
each quote is checked against the cited page; unverifiable evidence is retained
and marked for human review instead of being discarded. These checks are
deterministic and are not a substitute for reviewing extracted content.

## Install and run locally

Mock mode runs without an API key. To install DocuMind and start the app:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
streamlit run app.py
```

The `documind.extraction.service.ExtractionService` accepts a document from the
independent PDF ingestion module and any provider implementing
`ExtractionProvider`. Results contain typed fields, supporting quotes,
1-indexed page references, evidence verification, and optional processing
metadata. Unsupported values remain null; a populated field without evidence
fails Pydantic validation. Old result JSON remains loadable because new result
fields are optional. Gemini quota errors, connectivity issues, and malformed
results produce safe messages without exposing SDK credentials or document
text. Model confidence values are uncalibrated estimates, not validated
probabilities.

## Development checks

```bash
pytest
ruff check .
ruff format --check .
```

## Run with Docker

Build and start the demo from the repository root:

```bash
docker build -t documind .
docker run --rm -p 8501:8501 documind
```

Open <http://localhost:8501>. The Docker image starts in Mock mode by default.
Do not copy a `.env` file into the image.

## Profiles

Profiles are lightweight data definitions and can be extended in
`documind.extraction.profile` without changing the extraction engine.

## Dashboard

After processing, DocuMind shows an identity strip and counts derived from the
result, followed by a page coverage map. Select a page to inspect the supported
facts and evidence on it. Tabs provide an overview, searchable and filterable
facts, grouped entities and dates, evidence checks, chunk processing details,
and JSON, CSV, or Markdown exports. The view-model that computes counts,
grouping, filters, and exports is independent of Streamlit.

## Screenshots

Placeholder: add a screenshot of the Streamlit landing page after launching it.
