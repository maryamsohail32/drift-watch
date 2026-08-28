# Project Coding Rules (Non-Obvious Only)

- **No package config exists** (`pyproject.toml`, `setup.cfg`, `requirements.txt` are all absent). Do not assume or create one without being asked; install dependencies ad-hoc.
- **Tests must run from project root** — `tests/test_pipeline_health.py` imports `from src.ml_pipeline import ...`. Running `pytest` from inside `src/` or `tests/` will fail with `ModuleNotFoundError`.
- **Single test command**: `pytest tests/test_pipeline_health.py::test_sentinel_audit`
- **`DriftSentinel.__init__` opens the schema file immediately** — always instantiate with a valid path to `schemas/feature_schema.yaml`. Missing file raises `FileNotFoundError` at construction time, not at `audit()` time.
- **Target leakage detection is hardcoded** in `drift_sentinel.py`: it checks for the literal column name `"normalized_amount"` with `"default_flag"` present. New leakage patterns require explicit code additions to `DriftSentinel.audit()`.
- **`schemas/feature_schema.yaml` intentionally omits `default_flag`** from `features:` — it lives under `target:` only. Adding it to `features:` would suppress leakage detection.
- **`preprocess_features` mutates via `.copy()`** — it returns a new DataFrame; callers should not expect in-place modification.
- WatsonX credentials are loaded in `DriftSentinel.__init__` but **not used in any current audit logic** — `self.api_key` etc. are stored for future extension only.
