# DocuMind

DocuMind is a portfolio prototype that explores turning fictional PDF documents
into structured, validated, traceable data with a human review step. It is being
built in small milestones so each part stays understandable and explainable.

> This is an educational prototype using fictional data. It does not claim
> regulatory, GxP, or production compliance.

## Milestone 1: foundation

The landing page and deterministic mock provider run without an API key and make
no network calls. PDF ingestion and live extraction are planned for later
milestones.

## Run the demo

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
streamlit run app.py
```

The app starts in `demo` mode and needs no OpenAI API key. The mock provider
does not send document text to a service. Local development settings can go in
a root `.env` file, which is ignored by Git:

```dotenv
DOCUMIND_MODE=demo
DOCUMIND_MODEL=gpt-4o-mini
```

Values already set in the hosting environment take precedence over `.env`.
`DOCUMIND_MODEL` only changes the displayed model setting in this milestone.
Live extraction is not implemented; selecting `DOCUMIND_MODE=live` displays a
notice and still makes no OpenAI request.

## Development checks

```bash
pytest
ruff check .
```

## Run with Docker

Build and start the demo from the repository root:

```bash
docker build -t documind .
docker run --rm -p 8501:8501 documind
```

Open <http://localhost:8501>. To pass configuration from the host, add
`-e DOCUMIND_MODE=demo` (or other supported settings) to `docker run`. Do not
copy a secrets file into the image.

## Planned profiles

The planned profiles are fictional life sciences trial synopses and business
service contracts. A later milestone will show how to add a profile using its
own schema and rules files.

## Screenshots

Placeholder: add a screenshot of the Streamlit landing page after launching it.
