import csv
import io
import json
import math
from pathlib import Path

import joblib
import pandas as pd

FEATURES = [
    "tenure_months",
    "contract_type",
    "monthly_charges",
    "support_calls",
    "payment_method",
]

CONTRACTS = {
    "month_to_month",
    "one_year",
    "two_year",
}

PAYMENTS = {
    "electronic_check",
    "bank_transfer",
    "credit_card",
    "mailed_check",
}


def model_fn(model_dir):
    root = Path(model_dir)

    return {
        "model": joblib.load(
            root / "model.joblib"
        ),
        "policy": json.loads(
            (
                root
                / "decision_policy.json"
            ).read_text(
                encoding="utf-8"
            )
        ),
    }


def input_fn(
    request_body,
    content_type,
):
    if content_type != "text/csv":
        raise ValueError(
            "Unsupported content type: "
            f"{content_type}"
        )

    rows = list(
        csv.reader(
            io.StringIO(
                request_body.strip()
            )
        )
    )

    if not rows:
        raise ValueError(
            "Inference payload is empty"
        )

    parsed = []

    for row in rows:
        if len(row) != len(FEATURES):
            raise ValueError(
                "Each inference row must "
                "contain five values"
            )

        tenure = int(row[0])
        contract = (
            row[1].strip().lower()
        )
        charges = float(row[2])
        calls = int(row[3])
        payment = (
            row[4].strip().lower()
        )

        if not math.isfinite(charges):
            raise ValueError(
                "monthly_charges "
                "must be finite"
            )

        if (
            tenure < 0
            or charges < 0
            or calls < 0
        ):
            raise ValueError(
                "Numeric features "
                "must be non-negative"
            )

        if contract not in CONTRACTS:
            raise ValueError(
                "Unsupported contract_type"
            )

        if payment not in PAYMENTS:
            raise ValueError(
                "Unsupported payment_method"
            )

        parsed.append({
            "tenure_months": tenure,
            "contract_type": contract,
            "monthly_charges": charges,
            "support_calls": calls,
            "payment_method": payment,
        })

    return pd.DataFrame(
        parsed,
        columns=FEATURES,
    )


def predict_fn(
    input_data,
    bundle,
):
    probabilities = (
        bundle["model"]
        .predict_proba(input_data)[:, 1]
    )

    threshold = float(
        bundle["policy"][
            "decision_threshold"
        ]
    )

    predictions = (
        probabilities >= threshold
    ).astype(int)

    return [
        {
            "prediction":
                int(prediction),
            "probability":
                float(probability),
            "decision_threshold":
                threshold,
        }
        for prediction, probability
        in zip(
            predictions,
            probabilities,
        )
    ]


def output_fn(
    prediction,
    accept,
):
    if accept not in (
        "application/json",
        "*/*",
        None,
    ):
        raise ValueError(
            "Unsupported response type: "
            f"{accept}"
        )

    return (
        json.dumps(prediction),
        "application/json",
    )
