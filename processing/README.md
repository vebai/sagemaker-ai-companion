# 2. Prepare data for training

**Path:** [Generate data](../data/README.md) → **Process** → [Train](../training/README.md) → [Evaluate](../evaluation/README.md)  
**Book:** Chapter 4 · **Cost:** local execution is free of AWS compute charges; managed processing is billable

## Purpose and prerequisites
`process.py` checks the input schema, permissible categorical values, numeric fields and missing values, then splits the dataset into **training, validation and test** CSVs. Generate `data/customer_churn.csv` first. Run from the repository root.

## Local run (no AWS resources)
```bash
python processing/process.py --input data/customer_churn.csv --output data/processed
ls data/processed/{train,validation,test}/data.csv
```

| Argument | Required? | Purpose |
|---|---|---|
| `--input` | Optional locally | Source CSV; default is the SageMaker container input path |
| `--output` | Optional locally | Directory for the three split folders; default is the SageMaker container output path |

**Output:** `data/processed/train/data.csv`, `validation/data.csv`, `test/data.csv`. The split has approximately 70% / 15% / 15% of records, stratified by label.

## Managed processing (AWS, billable)
After completing [Terraform infrastructure setup](../README.md#6-review-and-deploy-the-supporting-aws-infrastructure), [uploading raw data](../README.md#7-run-the-learning-workflow) and checking the processing quota for **`ml.m5.xlarge`**:
```bash
source scripts/setup-env.sh
python workflow/run_processing.py
aws sagemaker describe-processing-job \
  --processing-job-name "$(cat workflow/latest_processing_job.txt)" \
  --query '{Status:ProcessingJobStatus,Failure:FailureReason}'
```
The submission is asynchronous. Wait for **`Completed`**, then confirm all three `processed/*/data.csv` objects exist in the project S3 bucket before training.

**Failure boundary:** An invalid schema is a data-contract failure; `AccessDenied`, unavailable quota and missing S3 objects are AWS configuration failures. **Cleanup:** Local splits can be deleted once evidence is retained; managed job output remains in S3 until removed. **Next:** [Train](../training/README.md).
