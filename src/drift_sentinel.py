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

    def audit(self, df: pd.DataFrame):
        findings = []
        feature_specs = {f['name']: f for f in self.schema['features']}
        target_name = self.schema.get('target', {}).get('name')

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

        return findings

if __name__ == "__main__":
    from ml_pipeline import load_raw_data, preprocess_features
    sentinel = DriftSentinel("schemas/feature_schema.yaml")
    processed_df = preprocess_features(load_raw_data())
    for finding in sentinel.audit(processed_df):
        print(finding)