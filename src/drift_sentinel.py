import os
import yaml
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class DriftSentinel:
    def __init__(self, schema_path: str):
        self.api_key = os.getenv("IBM_CLOUD_API_KEY")
        self.project_id = os.getenv("WATSONX_PROJECT_ID")
        self.watsonx_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        
        with open(schema_path, 'r') as f:
            self.schema = yaml.safe_load(f)

    def check_dynamic_leakage(self, df: pd.DataFrame, target_col: str = "default_flag", threshold: float = 0.85) -> list:
        """
        Dynamically identifies features with unexpectedly high linear correlation to the target variable.
        """
        if target_col not in df.columns:
            return []
        
        numeric_df = df.select_dtypes(include=["number"])
        if target_col not in numeric_df.columns:
            return []
            
        correlations = numeric_df.corr()[target_col].abs()
        suspicious_features = correlations[(correlations > threshold) & (correlations.index != target_col)]
        
        findings = []
        for feature, corr_val in suspicious_features.items():
            findings.append({
                "feature": feature,
                "rule": f"Dynamic Correlation Guard (corr = {corr_val:.2f})",
                "severity": "CRITICAL",
                "message": f"Feature '{feature}' shows extreme correlation ({corr_val:.2f}) with target label '{target_col}'."
            })
        return findings

    def audit(self, df: pd.DataFrame):
        findings = []
        feature_specs = {f['name']: f for f in self.schema['features']}
        target_name = self.schema.get('target', {}).get('name', 'default_flag')

        for col in df.columns:
            if col not in feature_specs:
                # Target leakage: unknown column derived from the target column
                if target_name and target_name in df.columns and col != target_name:
                    findings.append(
                        f"[CRITICAL] Target leakage detected on feature '{col}' derived from target."
                    )
                continue

            spec = feature_specs[col]

            # Null check
            if not spec['allow_null'] and df[col].isnull().any():
                findings.append(f"[HIGH] Disallowed nulls in column '{col}'.")

            # Dtype check
            expected_type = spec.get('type')
            if expected_type == 'int' and not pd.api.types.is_integer_dtype(df[col]):
                findings.append(
                    f"[MEDIUM] dtype mismatch on '{col}': expected int, got {df[col].dtype}."
                )
            elif expected_type == 'float' and not pd.api.types.is_float_dtype(df[col]):
                findings.append(
                    f"[MEDIUM] dtype mismatch on '{col}': expected float, got {df[col].dtype}."
                )

            # Bounds checks (min and max)
            if 'min' in spec and (df[col] < spec['min']).any():
                findings.append(
                    f"[HIGH] Out of bounds values detected in '{col}' below min {spec['min']}."
                )
            if 'max' in spec and (df[col] > spec['max']).any():
                findings.append(
                    f"[HIGH] Out of bounds values detected in '{col}' exceeding max {spec['max']}."
                )

        # Dynamic Correlation Check Integration
        if target_name and target_name in df.columns:
            dynamic_findings = self.check_dynamic_leakage(df, target_col=target_name)
            for f in dynamic_findings:
                formatted_msg = f"[{f['severity']}] {f['message']}"
                if formatted_msg not in findings:
                    findings.append(formatted_msg)

        return findings

if __name__ == "__main__":
    from ml_pipeline import load_raw_data, preprocess_features
    sentinel = DriftSentinel("schemas/feature_schema.yaml")
    processed_df = preprocess_features(load_raw_data())
    for finding in sentinel.audit(processed_df):
        print(finding)