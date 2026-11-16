# 1. Generate the example dataset

**Path:** [Start](../README.md) → **Generate data** → [Process](../processing/README.md) → [Train](../training/README.md) → [Evaluate](../evaluation/README.md)  
**Book:** Chapter 4 · **Cost:** local only; no AWS job

## Purpose and prerequisites
`create_dataset.py` generates 600 deterministic synthetic customer-churn records. First complete [Python setup](../README.md#3-clone-configure-python-and-verify-identity). Run all commands from the repository root.

## Run
```bash
python data/create_dataset.py
head -n 3 data/customer_churn.csv
```

**Input:** None; the generator uses a fixed random seed.  
**Output:** `data/customer_churn.csv`, with five features and the `churned` label. This command does not upload anything to AWS.

## Verify and next step
Inspect the header and generated rows; a completed script is not evidence that later training will succeed. For an offline split, follow [Processing](../processing/README.md). For managed processing, first create the project S3 bucket and roles using the [infrastructure instructions](../README.md#5-bootstrap-a-private-s3-backend-for-terraform), then upload the CSV as `raw/customer_churn.csv` (see the [managed workflow](../workflow/README.md)).

**Failure boundary:** If the CSV is missing, check that the command ran from the repository root and that `data/` is writable. **Cleanup:** Delete the local generated CSV only when no longer needed.
