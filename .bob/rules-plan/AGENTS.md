# Project Architecture Rules (Non-Obvious Only)

- **Audit logic is stateless per call** — `DriftSentinel.audit(df)` takes a full DataFrame snapshot; there is no streaming, windowing, or stateful drift tracking.
- **Leakage detection is not schema-driven** — the `schemas/feature_schema.yaml` has no `leakage` or `derived_from` fields. Leakage checks in `DriftSentinel.audit()` are hardcoded per-column. Any generalised leakage detection requires either schema extension or a separate derivation registry.
- **Schema bounds checking is one-directional** — `audit()` checks `max` only; `min` is defined in the schema but not yet validated in code. Plans to add min-bound checks should add a symmetric block alongside the existing `max` check.
- **No `__init__.py` files exist in `src/` or `tests/`** — the project relies on `pytest`'s root-relative import resolution. Adding `__init__.py` could break existing imports.
- **WatsonX integration is a stub** — credentials are stored in `DriftSentinel.__init__` but no API calls are made. Any plan to add WatsonX model monitoring should extend `DriftSentinel`, not create a parallel class.
