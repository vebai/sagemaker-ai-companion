# 3. Train the churn model

**Path:** [Process](../processing/README.md) → **Train** → [Evaluate](../evaluation/README.md) → [Register a release](../workflow/README.md)  
**Book:** Chapter 4 · **Cost:** managed training uses billable SageMaker compute

## Before running
A completed managed processing job must have produced `s3://$S3_BUCKET/processed/train/data.csv`. Configure the AWS environment with `source scripts/setup-env.sh`, verify your identity and Region, and check the **training-job** quota for **`ml.m5.xlarge`**. The instance quota for processing does not cover training.

## Run (AWS, billable)
From the repository root:
```bash
python workflow/run_training.py
aws sagemaker describe-training-job \
  --training-job-name "$(cat workflow/latest_training_job.txt)" \
  --query '{Status:TrainingJobStatus,Failure:FailureReason}'
```

**Input:** Training CSV from the S3 `processed/train/` channel. **Entry point:** `training/train.py` reads `SM_CHANNEL_TRAIN`, writes `model.joblib` to `SM_MODEL_DIR`, and accepts `--max-iter` (configured to 500 by `run_training.py`).

**Verify:** Submission is asynchronous; wait for status **`Completed`**. Inspect the job's model artefact URI:
```bash
aws sagemaker describe-training-job \
  --training-job-name "$(cat workflow/latest_training_job.txt)" \
  --query 'ModelArtifacts.S3ModelArtifacts' --output text \
  > workflow/latest_model_artifact.txt
cat workflow/latest_model_artifact.txt
```
Keep this hand-off file: evaluation and packaging need it. Training completion proves computation finished, **not** model quality.

**Failure boundary:** Check quota, IAM/`iam:PassRole`, container/ECR access, S3 input and CloudWatch logs. **Cleanup:** Training compute stops when the job completes; model artefacts and logs persist. **Next:** [Evaluate](../evaluation/README.md).
