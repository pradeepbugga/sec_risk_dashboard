# Extraction pipeline

The code that produces `data/global_cluster_data.json` and
`data/executive_summaries/` at the repo root — the data this dashboard
displays. See the root [README](../README.md#pipeline) for what each of the
14 stages does; this file covers how to run them.

## Setup

```
conda env create -f environment.yml
conda activate sec
```

or, without conda:

```
pip install -r requirements.txt
```

Running the archived diagnostic scripts under `archive/` additionally needs
`archive/requirements-optional.txt` (pulls in `torch`/`sentence-transformers`,
not needed for the main pipeline).

You'll also need `DATABASE_URL` (or `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`)
set if you're using `insert.py` / `db/connection.py`, and `OPENAI_API_KEY` for
the embedding and executive-summary stages.

## Running it

This is a hand-run, disk-chained pipeline, not a single entry point — each
stage reads the previous stage's output from a local `data/` directory (not
tracked in git; only `data/tickers.csv` is) and writes its own output there
for the next stage. Run scripts from this directory (`pipeline/`) so their
relative `./data/...` paths resolve correctly. Rough order:

1. `filing_parser/pipeline/section_ingest.py` — download filings, extract the
   Risk Factors section
2. `chunk/add_start_stop.py` → `chunk/heading_hierarchy.py` →
   `chunk/extract_text_chunk.py` → `chunk/postprocessing.py` — parse
   structure, classify headings, chunk into paragraphs
3. `embedding/embed_te3_large.py` — embed chunks (OpenAI text-embedding-3-large)
4. `cluster/microclustering.py` → `cluster/adaptive_macroclustering.py` —
   cluster risk topics per firm, then across the industry
5. `backend/gen_full_json.py` — aggregate everything into
   `data/global_cluster_data.json`
6. `llm_api/executive_summary.py` — generate per-firm/year narrative summaries

`archive/` holds one-off diagnostic and exploratory scripts that were run
against real pipeline output during development but aren't part of this main
flow.
