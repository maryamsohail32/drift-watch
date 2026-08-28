# 🤖 IBM Bob 2.0 — Parallel Subagent Audit Log

---

## Parallel Audit Results — `credit_risk_pipeline`

### Subagent A — Schema Invariant Audit

**9 total violations across 2 features:**

| Feature | Violation | Severity | Stage | Rows |
|---|---|---|---|---|
| `account_age_months` | Null (`np.nan`) violates `allow_null: false` | 🔴 CRITICAL | Raw | idx 4 |
| `account_age_months` | `fillna(0)` masks the null — imputed value `0` hides the quality problem | 🔴 CRITICAL | Processed | idx 4 |
| `account_age_months` | Source dtype is `float`, schema requires `int` | 🟠 HIGH | Raw | idx 0–3 |
| `transaction_amount_usd` | `250000.00` is **5× schema max** of `50000.00` — passes through unchanged | 🔴 CRITICAL | Raw + Processed | idx 1 |
| `normalized_amount` | Column exists in processed DataFrame, **absent from schema entirely** | 🟠 HIGH | Processed | all |
| `normalized_amount` | Target leakage via `default_flag` — see Subagent B | 🔴 CRITICAL | Processed | all |
| `credit_score` | ✅ No violations | — | — | — |
| `default_flag` | ✅ `allowed_values` respected | — | — | — |

---

### Subagent B — Target Leakage Dependency Trace

**One direct leakage point, no transitive leakage:**

**`src/ml_pipeline.py:18`**

```python
df_clean["normalized_amount"] = df_clean["transaction_amount_usd"] / (df_clean["default_flag"] + 1)
```

**Dependency Graph:**

```text
default_flag (TARGET)
    │
    │  Line 18: transaction_amount_usd / (default_flag + 1)
    ▼
normalized_amount  ──►  [end — no transitive leakage]

At serving (default_flag absent):
    └──► KeyError: 'default_flag'  [immediate crash]
```

---

### Sentinel Gap Convergence & Remediation Status

- Min Bound Check: Applied in `drift_sentinel.py`
- Schema-Driven Leakage Guard: Applied in `drift_sentinel.py`
- Type Assertions: Applied in `drift_sentinel.py`
- Interactive Remediation Engine: Integrated in `app.py`