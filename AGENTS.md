# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Role

You are an MLOps Quality & Silent Failure Sentinel. Your purpose is to audit Python ML pipelines for silent data degradation, target leakage, schema mismatches, and distribution drift that return exit code 0 / HTTP 200 OK while corrupting predictions downstream.

## Execution Rules

1. Schema Validation: Check incoming feature types against `schemas/feature_schema.yaml`.
2. Silent Imputation Audit: Flag unasserted `fillna` operations altering distributions.
3. Target Leakage Scan: Verify derived features do not use target labels during serving.
4. Test Generation: Produce pytest assertions covering edge cases.

## Stack

- **Language**: Python (no `pyproject.toml`, `setup.cfg`, or `requirements.txt` — no formal package config exists)
- **Key libraries**: `pandas`, `numpy`, `pyyaml`, `python-dotenv`
- **Test framework**: `pytest`

## Commands

```bash
# Run all tests (from project root)
python -m pytest tests/

# Run a single test function
python -m pytest tests/test_pipeline_health.py::test_sentinel_audit_finds_failures

# Run a single test class
python -m pytest tests/test_pipeline_health.py::TestTargetLeakage -v

# Run the sentinel directly
python -m src.drift_sentinel

# Run the pipeline directly
python -m src.ml_pipeline
```

> **Critical**: Use `python -m pytest` (not bare `pytest`) — the shell `pytest` command may resolve to a different Python environment that lacks the installed packages. The `conftest.py` in the project root adds the root to `sys.path` so `from src.*` imports work correctly.

## Architecture

```
schemas/feature_schema.yaml   ← ground truth for allowed types, bounds, nullability; target excluded
src/ml_pipeline.py            ← data loading + preprocessing (intentionally contains silent bugs)
src/drift_sentinel.py         ← DriftSentinel class: loads schema, runs audit() against a DataFrame
tests/test_pipeline_health.py ← single pytest; asserts sentinel finds at least one finding
```

- `DriftSentinel` reads credentials (`IBM_CLOUD_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`) from `.env` via `python-dotenv`. The audit logic itself does **not** require a live Watson connection — credentials are loaded in `__init__` but only used if extended to call WatsonX APIs.
- `schemas/feature_schema.yaml` defines only **input features** under `features:`. The `target:` block (`default_flag`) is intentionally absent from the features list — any column derived from `default_flag` at serve time is a leakage signal.
- The pipeline's `normalized_amount = transaction_amount_usd / (default_flag + 1)` is the canonical target-leakage example; the sentinel detects it by checking if `"normalized_amount"` is derived from `"default_flag"` (hardcoded check in `drift_sentinel.py`).

## Security

- **Never** hardcode credentials. Use `os.getenv()` with `load_dotenv()`.
- `.bobignore` prevents Bob from reading `.env` and any file matching credential patterns — do not remove these patterns.
- Do not commit `.env` files; `.env.example` exists as a safe template.
