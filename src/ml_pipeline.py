import pandas as pd
import numpy as np

def load_raw_data() -> pd.DataFrame:
    data = {
        "account_age_months": [12.5, 24.0, 36.1, 48.8, np.nan],
        "transaction_amount_usd": [100.50, 250000.00, 45.00, 120.00, 310.00],
        "credit_score": [720, 680, 590, 810, 750],
        "default_flag": [0, 1, 0, 0, 1]
    }
    return pd.DataFrame(data)

def preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()
    # Silent Bug 1: Float to Int truncation + fillna(0)
    df_clean["account_age_months"] = df_clean["account_age_months"].fillna(0).astype(int)
    # Silent Bug 2: Target leakage in normalized feature
    df_clean["normalized_amount"] = df_clean["transaction_amount_usd"] / (df_clean["default_flag"] + 1)
    return df_clean

if __name__ == "__main__":
    df = preprocess_features(load_raw_data())
    print("Pipeline executed with shape:", df.shape)