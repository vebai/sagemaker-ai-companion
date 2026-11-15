import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

COLUMNS = [
    "tenure_months", "contract_type", "monthly_charges",
    "support_calls", "payment_method", "churned",
]
CONTRACTS = {"month_to_month", "one_year", "two_year"}
PAYMENTS = {"electronic_check", "bank_transfer", "credit_card", "mailed_check"}

def validate(df):
    if df.empty or list(df.columns) != COLUMNS or df.isna().any().any():
        raise ValueError("Invalid schema, empty data or missing values")

    for col in ["tenure_months", "monthly_charges", "support_calls", "churned"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
        if not np.isfinite(df[col]).all():
            raise ValueError(f"{col} contains invalid numeric value, such as NaN or infinity values")

    for col in ["tenure_months", "support_calls", "churned"]:
        if not np.equal(df[col], np.floor(df[col])).all():
            raise ValueError(f"{col} must contain whole numbers")
        df[col] = df[col].astype(int)

    if (df[["tenure_months", "monthly_charges", "support_calls"]] < 0).any().any():
        raise ValueError("Numeric features must be non-negative")

    for col in ["contract_type", "payment_method"]:
        df[col] = df[col].astype(str).str.strip().str.lower()

    if not set(df.contract_type) <= CONTRACTS:
        raise ValueError("Unsupported contract_type")
    if not set(df.payment_method) <= PAYMENTS:
        raise ValueError("Unsupported payment_method")
    if not set(df.churned) <= {0, 1}:
        raise ValueError("churned must contain only 0 or 1")

    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",
                        default="/opt/ml/processing/input/customer_churn.csv")
    parser.add_argument("--output",
                        default="/opt/ml/processing/output")
    args = parser.parse_args()

    df = validate(pd.read_csv(args.input))
    train, remainder = train_test_split(
        df, test_size=.30, random_state=42, stratify=df.churned)
    validation, test = train_test_split(
        remainder, test_size=.50, random_state=42,
        stratify=remainder.churned)

    for name, split in [
        ("train", train),
        ("validation", validation),
        ("test", test),
    ]:
        out = Path(args.output) / name
        out.mkdir(parents=True, exist_ok=True)
        split.to_csv(out / "data.csv", index=False)
        print(f"{name}: {len(split)} rows")

if __name__ == "__main__":
    main()
