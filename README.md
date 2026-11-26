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

The default mode is `demo`. To change the displayed model setting, set
`DOCUMIND_MODEL` in the environment. `OPENAI_API_KEY` is not used in this
milestone. Live mode will be implemented later.

## Development checks

```bash
pytest
ruff check .
```

## Planned profiles

The planned profiles are fictional life sciences trial synopses and business
service contracts. A later milestone will show how to add a profile using its
own schema and rules files.

## Screenshots

Placeholder: add a screenshot of the Streamlit landing page after launching it.
