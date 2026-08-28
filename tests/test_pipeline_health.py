import pytest
from src.ml_pipeline import load_raw_data, preprocess_features
from src.drift_sentinel import DriftSentinel

def test_sentinel_audit():
    sentinel = DriftSentinel("schemas/feature_schema.yaml")
    processed_df = preprocess_features(load_raw_data())
    findings = sentinel.audit(processed_df)
    assert len(findings) > 0, "Sentinel should flag silent bugs in the baseline pipeline."