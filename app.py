import streamlit as st
import pandas as pd
import numpy as np
import time
from src.drift_sentinel import DriftSentinel
st.sidebar.image("assets/logo.png", width=120)
# Page Configuration
st.set_page_config(
    page_title="Drift Watch — MLOps Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e222d;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #2e364f;
        text-align: center;
    }
    .status-badge-critical {
        background-color: #3d1418;
        color: #ff4b4b;
        padding: 6px 12px;
        border-radius: 6px;
        border: 1px solid #ff4b4b;
        font-weight: 600;
    }
    .status-badge-high {
        background-color: #3d2b0f;
        color: #ffa500;
        padding: 6px 12px;
        border-radius: 6px;
        border: 1px solid #ffa500;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State for Interactive Demo
if 'remediated' not in st.session_state:
    st.session_state.remediated = False

# Sidebar Controls & Metadata
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg", width=120)
    st.title("Drift Watch")
    st.caption("IBM TechXchange 2026 Hackathon Prototype")
    
    st.markdown("---")
    st.subheader("🎛️ Live Demo Controls")
    
    inject_leakage = st.toggle("Inject Target Leakage", value=True, disabled=st.session_state.remediated)
    max_amount_input = st.slider("Max Transaction Amount ($)", min_value=1000, max_value=300000, value=250000, step=10000, disabled=st.session_state.remediated)
    
    if st.button("Reset Demo State"):
        st.session_state.remediated = False
        st.rerun()

    st.markdown("---")
    st.subheader("🤖 IBM Agentic System")
    st.success("IBM Bob 2.0 Agent: Active")
    st.info("Rule Framework: `AGENTS.md` Loaded")
    st.caption("Engine: `watsonx.ai` Sentinel Runtime")

# Data Construction based on Demo Controls
def build_demo_data(remediated=False, leakage=True, max_val=250000):
    if remediated:
        raw_data = {
            "account_age_months": [12.5, 24.0, 36.1, 48.8, 24.0],
            "transaction_amount_usd": [100.50, 45000.00, 45.00, 120.00, 310.00],
            "credit_score": [720, 680, 590, 810, 750],
            "default_flag": [0, 1, 0, 0, 1]
        }
        df = pd.DataFrame(raw_data)
        df["account_age_months"] = df["account_age_months"].round().astype(int)
        df["normalized_amount"] = df["transaction_amount_usd"] / 50000.0
    else:
        raw_data = {
            "account_age_months": [12.5, 24.0, 36.1, 48.8, np.nan],
            "transaction_amount_usd": [100.50, float(max_val), 45.00, 120.00, 310.00],
            "credit_score": [720, 680, 590, 810, 750],
            "default_flag": [0, 1, 0, 0, 1]
        }
        df = pd.DataFrame(raw_data)
        df["account_age_months"] = df["account_age_months"].fillna(0).astype(int)
        if leakage:
            df["normalized_amount"] = df["transaction_amount_usd"] / (df["default_flag"] + 1)
        else:
            df["normalized_amount"] = df["transaction_amount_usd"] / 50000.0
            
    return pd.DataFrame(raw_data), df

raw_df, processed_df = build_demo_data(
    remediated=st.session_state.remediated,
    leakage=inject_leakage,
    max_val=max_amount_input
)

sentinel = DriftSentinel("schemas/feature_schema.yaml")
findings = sentinel.audit(processed_df)

# Header Section
st.title("🛡️ Drift Watch — MLOps Sentinel")
st.markdown("**Autonomous Quality & Silent Failure Sentinel for Production Machine Learning Pipelines**")

st.markdown("---")

# Dynamic Metrics Banner
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Features Monitored", len(processed_df.columns), delta="3 Schema Defined")
with m2:
    if st.session_state.remediated or not findings:
        st.metric("Pipeline Health Score", "100%", delta="Healthy", delta_color="normal")
    else:
        st.metric("Pipeline Health Score", f"{max(0, 100 - len(findings)*35)}%", delta=f"-{len(findings)*35}% Failure", delta_color="inverse")
with m3:
    st.metric("Silent Anomalies Detected", len(findings), delta="Action Required" if findings else "Clean", delta_color="inverse" if findings else "normal")
with m4:
    st.metric("HTTP Pipeline Status", "200 OK", delta="Masked Degradation" if findings else "Verified Safe", delta_color="off" if findings else "normal")

st.markdown("<br>", unsafe_allow_html=True)

# Main Dashboard Tabs
tab1, tab2, tab3 = st.tabs(["🚨 Live Pipeline Audit", "📊 Data Flow Inspection", "💡 Auto-Remediation & Code Fixes"])

with tab1:
    st.subheader("Pipeline Audit Sentinel")
    st.caption("Scanning preprocessed features against business validation invariants and schema contracts.")
    
    if findings:
        st.error(f"⚠️ Audit Complete: {len(findings)} Silent Failures Detected That Bypass Standard Exception Handling")
        
        for f in findings:
            if "[CRITICAL]" in f:
                st.markdown(f"""
                <div style="background-color: rgba(255, 75, 75, 0.1); border-left: 5px solid #ff4b4b; padding: 14px; border-radius: 4px; margin-bottom: 10px;">
                    <span class="status-badge-critical">CRITICAL</span> &nbsp; <b>{f.replace('[CRITICAL] ', '')}</b>
                    <br><small style="color:#aaa;">Impact: Models consume target information during prediction, corrupting downstream evaluation metrics.</small>
                </div>
                """, unsafe_allow_html=True)
            elif "[HIGH]" in f:
                st.markdown(f"""
                <div style="background-color: rgba(255, 165, 0, 0.1); border-left: 5px solid #ffa500; padding: 14px; border-radius: 4px; margin-bottom: 10px;">
                    <span class="status-badge-high">HIGH</span> &nbsp; <b>{f.replace('[HIGH] ', '')}</b>
                    <br><small style="color:#aaa;">Impact: Out-of-bounds inputs or unasserted zero-imputation lead to unexpected drift during inference.</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("✅ All pipeline assertions verified. Zero silent failures detected.")

with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("1. Ingestion Data (`load_raw_data`)")
        st.dataframe(raw_df, use_container_width=True)
        
    with col_b:
        st.subheader("2. Engineered Output (`preprocess_features`)")
        st.dataframe(processed_df, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Feature Distribution vs Schema Limits")
    st.caption("Visualizing `transaction_amount_usd` against schema max bound ($50,000.00)")
    
    chart_data = pd.DataFrame({
        "Sample Record": [f"Row {i}" for i in range(len(processed_df))],
        "Transaction Amount": processed_df["transaction_amount_usd"]
    })
    st.bar_chart(chart_data, x="Sample Record", y="Transaction Amount")

with tab3:
    st.subheader("Recommended Code Patches (Generated via IBM Bob 2.0)")
    
    if not st.session_state.remediated and findings:
        if st.button("🤖 Apply IBM Bob Automated Patch & Re-Audit", type="primary"):
            st.session_state.remediated = True
            st.rerun()
    elif st.session_state.remediated:
        st.success("🎉 Automated patch applied successfully! Pipeline Health restored to 100%.")

    st.markdown("### 1. Target Leakage Remediation")
    st.code("""
# ❌ Flawed Transformation (Target Leakage)
df_clean["normalized_amount"] = df_clean["transaction_amount_usd"] / (df_clean["default_flag"] + 1)

# ✅ Correct Transformation (Independent Feature Normalization)
df_clean["normalized_amount"] = df_clean["transaction_amount_usd"] / 50000.0
""", language="python")

    st.markdown("### 2. Explicit Imputation & Truncation Guard")
    st.code("""
# ❌ Flawed Transformation (Silent Truncation & Null Masking)
df_clean["account_age_months"] = df_clean["account_age_months"].fillna(0).astype(int)

# ✅ Correct Transformation (Preserve Nulls or Explicit Asserted Imputation)
df_clean["account_age_months"] = df_clean["account_age_months"].round().astype(int)
""", language="python")


# ---------------------------------------------------------
# Streaming Micro-Batch Monitor (Future Work Visualizer)
# ---------------------------------------------------------
st.markdown("---")
with st.expander("⚡ Live Streaming Micro-Batch Monitor (Experimental)"):
    st.caption("Simulates real-time windowed drift monitoring across incoming data batches.")
    if st.button("▶ Run Streaming Micro-Batch Simulation"):
        chart_place = st.empty()
        status_place = st.empty()
        stream_data = []
        
        for batch_num in range(1, 6):
            # Batches 1-3 healthy, Batch 4-5 degraded
            health_score = 100 if batch_num < 4 else 30
            stream_data.append({"Batch": f"Batch #{batch_num}", "Health Score": health_score})
            
            chart_place.line_chart(data=stream_data, x="Batch", y="Health Score")
            
            if batch_num < 4:
                status_place.success(f"Ingesting Batch #{batch_num}... Pipeline Nominal (100%)")
            else:
                status_place.error(f"Ingesting Batch #{batch_num}... ⚠️ ALERT: Target Leakage & Drift Detected (30%)")
            
            time.sleep(0.7)