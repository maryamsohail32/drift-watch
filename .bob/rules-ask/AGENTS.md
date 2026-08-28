# Project Documentation Context (Non-Obvious Only)

- The pipeline in `src/ml_pipeline.py` **intentionally contains two silent bugs** (comments mark them): a float→int truncation via `fillna(0).astype(int)` and target leakage in `normalized_amount`. These are not defects to fix — they are the audit targets.
- `schemas/feature_schema.yaml` is the **sole source of truth** for what constitutes a valid feature. `default_flag` appears only under `target:`, making any feature derived from it a leakage signal by definition.
- There is **no formal test suite beyond one file** (`tests/test_pipeline_health.py` with a single test function). The test asserts findings are non-empty — it is a regression guard, not a spec.
- `DriftSentinel` currently performs **static DataFrame auditing only** — it does not connect to WatsonX, stream data, or monitor production traffic, despite loading WatsonX credentials.
- The project originated from an IBM Hackathon template; `README.md` describes the template, not the ML application.
