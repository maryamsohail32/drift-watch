import streamlit as st
import pandas as pd
from src.ml_pipeline import load_raw_data, preprocess_features
from src.drift_sentinel import DriftSentinel

st.set_page_config(
    page_title="Drift Watch — MLOps Sentinel",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Drift Watch — MLOps Sentinel")
st.subheader("Autonomous Quality & Silent Failure Sentinel for ML Pipelines")

st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. Raw Pipeline Input")
    raw_df = load_raw_data()
    st.dataframe(raw_df, use_container_width=True)

with col2:
    st.header("2. Processed Output (Pre-Sentinel)")
    processed_df = preprocess_features(raw_df)
    st.dataframe(processed_df, use_container_width=True)

st.markdown("---")

st.header("3. Sentinel Audit Results")

if st.button("Run Drift Watch Audit", type="primary"):
    sentinel = DriftSentinel("schemas/feature_schema.yaml")
    findings = sentinel.audit(processed_df)
    
    if findings:
        for finding in findings:
            if "[CRITICAL]" in finding:
                st.error(finding)
            elif "[HIGH]" in finding:
                st.warning(finding)
            else:
                st.info(finding)
    else:
        st.success("No silent failures detected. Pipeline health check passed!")