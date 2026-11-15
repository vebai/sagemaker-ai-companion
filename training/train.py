import argparse, json, os
from pathlib import Path
import joblib, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FEATURES = [
    "tenure_months", "contract_type", "monthly_charges",
    "support_calls", "payment_method",
]
LABEL = "churned"
NUMERIC = ["tenure_months", "monthly_charges", "support_calls"]
CATEGORICAL = ["contract_type", "payment_method"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-iter", type=int, default=500)
    args = parser.parse_args()

    train_dir = Path(
        os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train"))
    model_dir = Path(
        os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
    df = pd.read_csv(train_dir / "data.csv")

    preprocess = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])

    model = Pipeline([
        ("preprocess", preprocess),
        ("classifier", LogisticRegression(
            max_iter=args.max_iter,
            random_state=42,
        )),
    ])

    model.fit(df[FEATURES], df[LABEL])
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / "model.joblib")

    metadata = {
        "features": FEATURES,
        "label": LABEL,
        "positive_class": 1,
        "algorithm": "LogisticRegression",
    }
    (model_dir / "model_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    print("Training complete")

if __name__ == "__main__":
    main()
