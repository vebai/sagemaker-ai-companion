import argparse
import json
import tarfile
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
)

FEATURES = [
    "tenure_months",
    "contract_type",
    "monthly_charges",
    "support_calls",
    "payment_method",
]
LABEL = "churned"

CANDIDATE_THRESHOLDS = [
    0.10, 0.15, 0.20, 0.25, 0.30,
    0.35, 0.40, 0.45, 0.50,
]

VALIDATION_RECALL_TARGET = 0.75
MIN_TEST_RECALL = 0.75
MIN_TEST_PRECISION = 0.35


def safe_extract(archive, destination):
    root = destination.resolve()

    for member in archive.getmembers():
        if member.issym() or member.islnk():
            raise ValueError("Model archive contains a link")

        target = (destination / member.name).resolve()

        if target != root and root not in target.parents:
            raise ValueError("Unsafe path in model archive")

    archive.extractall(destination)


def measure(y_true, probabilities, threshold):
    predictions = (probabilities >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
        labels=[0, 1],
    ).ravel()

    return {
        "accuracy": float(
            accuracy_score(y_true, predictions)
        ),
        "precision": float(
            precision_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        default="/opt/ml/processing/model/model.tar.gz",
    )
    parser.add_argument(
        "--validation",
        default="/opt/ml/processing/validation/data.csv",
    )
    parser.add_argument(
        "--test",
        default="/opt/ml/processing/test/data.csv",
    )
    parser.add_argument(
        "--output",
        default="/opt/ml/processing/output/evaluation.json",
    )
    parser.add_argument(
        "--model-artifact-uri",
        required=True,
    )
    parser.add_argument(
        "--validation-data-uri",
        required=True,
    )
    parser.add_argument(
        "--test-data-uri",
        required=True,
    )

    args = parser.parse_args()

    model_dir = Path("/tmp/model")
    model_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(args.model, "r:gz") as archive:
        safe_extract(archive, model_dir)

    model = joblib.load(
        model_dir / "model.joblib"
    )

    if list(model.classes_) != [0, 1]:
        raise ValueError(
            "Expected classifier classes [0, 1]"
        )
    validation = pd.read_csv(
        args.validation
    )

    validation_probabilities = model.predict_proba(
        validation[FEATURES]
    )[:, 1]

    candidates = []

    for threshold in CANDIDATE_THRESHOLDS:
        metrics = measure(
            validation[LABEL],
            validation_probabilities,
            threshold,
        )

        candidates.append({
            "threshold": threshold,
            "precision": metrics["precision"],
            "recall": metrics["recall"],
        })

    eligible = [
        item
        for item in candidates
        if item["recall"] >= VALIDATION_RECALL_TARGET
    ]

    selected = max(
        (
            item["threshold"]
            for item in eligible
        ),
        default=None,
    )

    evidence = {
        "model_artifact_uri":
            args.model_artifact_uri,
        "validation_data_uri":
            args.validation_data_uri,
        "test_data_uri":
            args.test_data_uri,
        "threshold_selection": {
            "candidate_thresholds":
                CANDIDATE_THRESHOLDS,
            "candidate_results":
                candidates,
            "validation_recall_target":
                VALIDATION_RECALL_TARGET,
            "validation_target_met":
                selected is not None,
            "selected_decision_threshold":
                selected,
        },
        "test_metrics": None,
        "release_requirements": {
            "validation_recall_target":
                VALIDATION_RECALL_TARGET,
            "minimum_test_recall":
                MIN_TEST_RECALL,
            "minimum_test_precision":
                MIN_TEST_PRECISION,
        },
        "release_decision": "fail",
    }

    if selected is not None:
        test = pd.read_csv(args.test)

        probabilities = model.predict_proba(
            test[FEATURES]
        )[:, 1]

        metrics = measure(
            test[LABEL],
            probabilities,
            selected,
        )

        evidence["test_metrics"] = metrics

        if (
            metrics["recall"] >= MIN_TEST_RECALL
            and
            metrics["precision"] >= MIN_TEST_PRECISION
        ):
            evidence["release_decision"] = "pass"

    output = Path(args.output)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(evidence, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
