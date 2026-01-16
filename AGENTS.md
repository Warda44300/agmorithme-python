# Repository Guidelines

## Project Structure & Module Organization
This repo mixes data-processing scripts and a small API:
- Top-level `01_*.py` to `04_*.py` scripts form the LinkedIn CSV pipeline (normalize, enrich, dedupe, score).
- `tri_*.py` and `sync_prospects_postgres.py` handle filtering and database sync.
- `wdc_api/` is a FastAPI service with routers, schemas, models, and DB setup.
- Data artifacts (`*.csv`, `*.db`, `*.xlsx`) live at the repo root; treat them as generated inputs/outputs.
- `venv/` is a local virtual environment (do not commit changes inside).

## Build, Test, and Development Commands
Run scripts directly with Python (examples use the repo root as working dir):
- `python 01_normalisation_linkedin.py` reads `Connections_from_LinkedIn.csv` and writes `linkedin_normalise.csv`.
- `python 02_enrichissement_minimal.py` and `python 03_dedoublonnage_qualite.py` continue the pipeline.
- `python tri_csv_v1.py` filters CSVs using rules in `wdc_api/configs/`.
- `python sync_prospects_postgres.py` upserts `prospects_recommandes.csv` into PostgreSQL.
- `uvicorn wdc_api.main:app --reload` runs the API locally.

## Coding Style & Naming Conventions
- Python, 4-space indentation, snake_case for functions and variables.
- Files use descriptive snake_case; pipeline steps are prefixed with numbers (e.g., `01_...`).
- Favor short helper functions and inline type hints where they already exist.
- No formatter/linter is configured; keep changes consistent with existing style.

## Testing Guidelines
- No formal test framework is present. Use `python test_postgres.py` for DB connectivity checks.
- If you add tests, follow `test_*.py` naming and document the command you used.

## Commit & Pull Request Guidelines
- Git history is not available in this environment, so no commit message convention is confirmed.
- PRs should include a brief description, the scripts/commands run, and before/after row counts for CSV outputs.

## Security & Configuration Tips
- API auth uses `WDC_API_KEY` (see `wdc_api/security.py`).
- DB config lives in `wdc_api/database.py` (`DATABASE_URL`) and `sync_prospects_postgres.py` (`PG_CONFIG`).
- Avoid committing real credentials; prefer environment variables or a local, ignored config.
