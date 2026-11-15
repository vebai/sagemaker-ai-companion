import csv, math, random
from pathlib import Path

OUT = Path("data/customer_churn.csv")
rng = random.Random(42)
contracts = ["month_to_month", "one_year", "two_year"]
payments = ["electronic_check", "bank_transfer", "credit_card", "mailed_check"]
rows = []

for _ in range(600):
    tenure = rng.randint(1, 72)
    contract = rng.choices(contracts, weights=[.55, .25, .20], k=1)[0]
    charges = round(rng.uniform(25, 120), 2)
    calls = rng.randint(0, 6)
    payment = rng.choices(payments, weights=[.35, .25, .25, .15], k=1)[0]

    score = (-1.343 - .035 * tenure
             + (.9 if contract == "month_to_month"
                else -.4 if contract == "two_year" else 0)
             + .018 * (charges - 65) + .22 * calls
             + (.45 if payment == "electronic_check" else 0))

    churned = int(rng.random() < 1 / (1 + math.exp(-score)))
    rows.append([tenure, contract, charges, calls, payment, churned])

OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow([
        "tenure_months", "contract_type", "monthly_charges",
        "support_calls", "payment_method", "churned",
    ])
    writer.writerows(rows)

print(f"rows={len(rows)} churn={sum(row[-1] for row in rows)}")
