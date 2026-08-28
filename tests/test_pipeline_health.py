import pytest
import pandas as pd
import numpy as np
from src.ml_pipeline import load_raw_data, preprocess_features
from src.drift_sentinel import DriftSentinel

SCHEMA_PATH = "schemas/feature_schema.yaml"


@pytest.fixture
def sentinel():
    return DriftSentinel(SCHEMA_PATH)


@pytest.fixture
def raw_df():
    return load_raw_data()


@pytest.fixture
def processed_df(raw_df):
    return preprocess_features(raw_df)


# ---------------------------------------------------------------------------
# Regression guard (original test preserved)
# ---------------------------------------------------------------------------

def test_sentinel_audit_finds_failures(sentinel, processed_df):
    """Sentinel must raise at least one finding on the baseline pipeline."""
    findings = sentinel.audit(processed_df)
    assert len(findings) > 0, "Sentinel should flag silent bugs in the baseline pipeline."


# ---------------------------------------------------------------------------
# Silent Bug 1: fillna(0) + float→int truncation on account_age_months
# ---------------------------------------------------------------------------

class TestSilentImputation:
    def test_fillna_zero_masks_null(self, processed_df):
        """After preprocessing, no NaN should remain — but this masks the original null
        with a semantically invalid zero (0-month-old account)."""
        assert processed_df["account_age_months"].isnull().sum() == 0, (
            "fillna(0) silently imputes NaN; null is hidden rather than flagged."
        )

    def test_fillna_imputes_zero_not_median(self, raw_df, processed_df):
        """The imputed value is 0, not a statistically reasonable substitute."""
        null_mask = raw_df["account_age_months"].isnull()
        imputed_values = processed_df.loc[null_mask, "account_age_months"]
        assert (imputed_values == 0).all(), (
            "Expected fillna(0) to impute 0 for missing account_age_months."
        )

    def test_float_truncation_loses_precision(self, raw_df, processed_df):
        """astype(int) truncates (not rounds) floats — 36.1 → 36, 48.8 → 48."""
        non_null_mask = raw_df["account_age_months"].notna()
        original = raw_df.loc[non_null_mask, "account_age_months"]
        processed = processed_df.loc[non_null_mask, "account_age_months"]
        truncated = original.apply(lambda x: int(x))
        pd.testing.assert_series_equal(
            processed.reset_index(drop=True),
            truncated.reset_index(drop=True),
            check_names=False,
        )

    def test_sentinel_flags_null_in_raw_data(self, sentinel, raw_df):
        """Sentinel should flag the pre-imputation null on account_age_months."""
        findings = sentinel.audit(raw_df)
        null_findings = [f for f in findings if "account_age_months" in f and "null" in f.lower()]
        assert null_findings, (
            "Sentinel must flag disallowed null in account_age_months before imputation."
        )

    def test_sentinel_silent_after_imputation(self, sentinel, processed_df):
        """After fillna(0), sentinel no longer sees the null — imputation is silent."""
        findings = sentinel.audit(processed_df)
        null_findings = [f for f in findings if "account_age_months" in f and "null" in f.lower()]
        assert not null_findings, (
            "Post-imputation sentinel finds no null on account_age_months — "
            "the silent imputation succeeded in hiding the data quality issue."
        )


# ---------------------------------------------------------------------------
# Silent Bug 2: Target leakage — normalized_amount derived from default_flag
# ---------------------------------------------------------------------------

class TestTargetLeakage:
    def test_normalized_amount_uses_target(self, raw_df):
        """normalized_amount divides by (default_flag + 1) — the target leaks into features."""
        df = preprocess_features(raw_df)
        expected = raw_df["transaction_amount_usd"] / (raw_df["default_flag"] + 1)
        pd.testing.assert_series_equal(
            df["normalized_amount"].reset_index(drop=True),
            expected.reset_index(drop=True),
            check_names=False,
        )

    def test_sentinel_flags_target_leakage(self, sentinel, processed_df):
        """Sentinel must emit a CRITICAL finding for normalized_amount."""
        findings = sentinel.audit(processed_df)
        leakage_findings = [f for f in findings if "[CRITICAL]" in f and "leakage" in f.lower()]
        assert leakage_findings, (
            "Sentinel must detect CRITICAL target leakage on normalized_amount."
        )

    def test_sentinel_flags_arbitrary_leakage_column(self, sentinel, raw_df):
        """Leakage detection must fire for any unknown column when default_flag is present,
        not just the hardcoded 'normalized_amount' name."""
        df = raw_df.copy()
        df["log_default_ratio"] = np.log1p(df["transaction_amount_usd"] / (df["default_flag"] + 1))
        findings = sentinel.audit(df)
        leakage_findings = [f for f in findings if "[CRITICAL]" in f and "log_default_ratio" in f]
        assert leakage_findings, (
            "Sentinel should flag any unknown feature column when the target is present "
            "— not only the hardcoded column name 'normalized_amount'."
        )

    def test_no_false_leakage_without_target_column(self, sentinel):
        """No leakage finding when target column is absent from the DataFrame."""
        df = pd.DataFrame({
            "account_age_months": [12, 24],
            "transaction_amount_usd": [100.0, 200.0],
            "credit_score": [720, 680],
        })
        findings = sentinel.audit(df)
        leakage_findings = [f for f in findings if "[CRITICAL]" in f]
        assert not leakage_findings, (
            "Sentinel must not raise leakage findings when no target column is present."
        )


# ---------------------------------------------------------------------------
# Schema Validation: out-of-bounds values
# ---------------------------------------------------------------------------

class TestOutOfBounds:
    def test_transaction_amount_exceeds_schema_max(self, sentinel, raw_df):
        """Raw data contains 250000.00 which exceeds schema max of 50000.00."""
        findings = sentinel.audit(raw_df)
        bound_findings = [
            f for f in findings
            if "transaction_amount_usd" in f and "max" in f.lower()
        ]
        assert bound_findings, (
            "Sentinel must flag transaction_amount_usd = 250000 exceeding schema max 50000."
        )

    def test_sentinel_flags_below_min(self, sentinel):
        """Sentinel must flag values below schema min (min-bound check)."""
        df = pd.DataFrame({
            "account_age_months": [12, 24],
            "transaction_amount_usd": [0.005, 100.0],   # 0.005 < min 0.01
            "credit_score": [720, 680],
            "default_flag": [0, 1],
        })
        findings = sentinel.audit(df)
        min_findings = [
            f for f in findings
            if "transaction_amount_usd" in f and "min" in f.lower()
        ]
        assert min_findings, (
            "Sentinel must flag transaction_amount_usd below schema min 0.01."
        )

    def test_credit_score_below_min_flagged(self, sentinel):
        """Credit score below 300 must be flagged."""
        df = pd.DataFrame({
            "account_age_months": [12],
            "transaction_amount_usd": [100.0],
            "credit_score": [200],   # below min 300
            "default_flag": [0],
        })
        findings = sentinel.audit(df)
        assert any("credit_score" in f and "min" in f.lower() for f in findings), (
            "Sentinel must flag credit_score = 200 below schema min 300."
        )

    def test_no_findings_on_clean_data(self, sentinel):
        """A perfectly valid DataFrame must produce zero findings."""
        df = pd.DataFrame({
            "account_age_months": [12, 24, 36],
            "transaction_amount_usd": [100.0, 500.0, 1000.0],
            "credit_score": [720, 680, 750],
        })
        findings = sentinel.audit(df)
        assert findings == [], f"Unexpected findings on clean data: {findings}"


# ---------------------------------------------------------------------------
# Schema Validation: dtype mismatches
# ---------------------------------------------------------------------------

class TestDtypeValidation:
    def test_sentinel_flags_float_where_int_expected(self, sentinel):
        """account_age_months typed as float should be flagged as dtype mismatch."""
        df = pd.DataFrame({
            "account_age_months": [12.5, 24.0, 36.1],   # float, schema expects int
            "transaction_amount_usd": [100.0, 200.0, 300.0],
            "credit_score": [720, 680, 750],
        })
        findings = sentinel.audit(df)
        dtype_findings = [
            f for f in findings
            if "account_age_months" in f and "dtype" in f.lower()
        ]
        assert dtype_findings, (
            "Sentinel must flag account_age_months as float when schema expects int."
        )

    def test_sentinel_flags_int_where_float_expected(self, sentinel):
        """transaction_amount_usd typed as int should be flagged as dtype mismatch."""
        df = pd.DataFrame({
            "account_age_months": [12, 24, 36],
            "transaction_amount_usd": [100, 200, 300],   # int, schema expects float
            "credit_score": [720, 680, 750],
        })
        findings = sentinel.audit(df)
        dtype_findings = [
            f for f in findings
            if "transaction_amount_usd" in f and "dtype" in f.lower()
        ]
        assert dtype_findings, (
            "Sentinel must flag transaction_amount_usd as int when schema expects float."
        )


# ---------------------------------------------------------------------------
# Pipeline integrity
# ---------------------------------------------------------------------------

class TestPipelineIntegrity:
    def test_load_raw_data_schema(self, raw_df):
        """Raw DataFrame must contain all expected columns."""
        expected_cols = {"account_age_months", "transaction_amount_usd", "credit_score", "default_flag"}
        assert expected_cols.issubset(set(raw_df.columns))

    def test_preprocess_adds_normalized_amount(self, processed_df):
        """Preprocessing must produce the normalized_amount leakage column."""
        assert "normalized_amount" in processed_df.columns

    def test_preprocess_does_not_mutate_input(self, raw_df):
        """preprocess_features must not mutate the original DataFrame."""
        original_null_count = raw_df["account_age_months"].isnull().sum()
        _ = preprocess_features(raw_df)
        assert raw_df["account_age_months"].isnull().sum() == original_null_count, (
            "preprocess_features mutated the input DataFrame."
        )

    def test_processed_dtype_is_int64(self, processed_df):
        """After fillna(0).astype(int), account_age_months must be integer dtype."""
        assert pd.api.types.is_integer_dtype(processed_df["account_age_months"]), (
            "account_age_months should be int after astype(int)."
        )
