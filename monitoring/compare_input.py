import csv
import json
from pathlib import Path
from statistics import mean

features = [
    "tenure_months",
    "contract_type",
    "monthly_charges",
    "support_calls",
    "payment_method",
]

with open(
    "monitoring/baseline-train.csv",
    encoding="utf-8",
) as handle:
    baseline = list(csv.DictReader(handle))

production = []

for path in Path(
    "monitoring/capture"
).rglob("*"):
    if not path.is_file():
        continue

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():
        try:
            record = json.loads(line)

            raw = record[
                "captureData"
            ][
                "endpointInput"
            ][
                "data"
            ]

            values = next(
                csv.reader([raw])
            )

            if len(values) == len(features):
                production.append(
                    dict(zip(features, values))
                )

        except (
            json.JSONDecodeError,
            KeyError,
            StopIteration,
        ):
            continue

if not production:
    raise SystemExit(
        "No compatible captured input found."
    )

baseline_charge = mean(
    float(row["monthly_charges"])
    for row in baseline
)

production_charge = mean(
    float(row["monthly_charges"])
    for row in production
)

baseline_monthly = mean(
    row["contract_type"]
    == "month_to_month"
    for row in baseline
)

production_monthly = mean(
    row["contract_type"]
    == "month_to_month"
    for row in production
)

print(
    "monthly_charges mean:",
    baseline_charge,
    "→",
    production_charge,
)

print(
    "month_to_month share:",
    baseline_monthly,
    "→",
    production_monthly,
)
