# Managed jobs, registration and release records

**Path:** [Data](../data/README.md) → [Process](../processing/README.md) → [Train](../training/README.md) → [Evaluate](../evaluation/README.md) → **Package and register** → [Inference](../inference/README.md)  
**Book:** Chapters 4–5 · **Cost:** processing, training and evaluation launch billable SageMaker jobs; registry operations alter AWS state

## Before running
From the repository root, activate Python and `source scripts/setup-env.sh`. Complete [project infrastructure](../README.md#6-review-and-deploy-the-supporting-aws-infrastructure), upload the raw CSV to `s3://$S3_BUCKET/raw/customer_churn.csv` and verify the relevant operation-specific quotas. The workflow scripts depend on outputs of earlier steps; they are **not** a single orchestration command.

## Run in order and inspect each hand-off

| Order | Run from repository root | Input → output | Verification |
|---|---|---|---|
| 1 | `python workflow/run_processing.py` | Raw S3 CSV → `workflow/latest_processing_job.txt` | Processing job **Completed**; three processed CSVs in S3 |
| 2 | `python workflow/run_training.py` | Processed training data → `workflow/latest_training_job.txt` | Training job **Completed**; capture `workflow/latest_model_artifact.txt` from job description |
| 3 | `python workflow/run_evaluation.py` | Model artefact + held-out splits → `workflow/latest_evaluation_job.txt`, `latest_evaluation_uri.txt` | Processing job **Completed**; download report to `evaluation/evaluation.json` |
| 4 | `python workflow/build_release_artifact.py` | Passing evaluation JSON + training artefact → `latest_release_artifact.txt` and SHA-256 | Uploaded release package exists; digest recorded |
| 5 | `python workflow/register_model.py` | Passing release artefact → `latest_model_package_arn.txt` | Registry package exists, initially **PendingManualApproval** |
| 6 | **Manual approval** (Chapter 5) | Evidence review → approved package + `latest_approval_actor.txt` | Verify the package is **Approved** and actor recorded |
| 7 | `python workflow/write_release_record.py` | Approved package, dataset/evaluation lineage → release JSON in S3 | Verify evidence and release-record URI |

**Canonical first command (billable):**
```bash
python workflow/run_processing.py
aws sagemaker describe-processing-job \
  --processing-job-name "$(cat workflow/latest_processing_job.txt)" \
  --query '{Status:ProcessingJobStatus,Failure:FailureReason}'
```

All managed submissions use asynchronous execution: a returned job name means **submitted**, not **completed**. The complete command sequence and evidence checks are in the [root README](../README.md#7-run-the-learning-workflow). Do not run later steps while an earlier job is pending or failed; do not approve a failing model. Check that your caller can `iam:PassRole` and that the managed execution role has S3 and ECR access.

**Failure boundary:** missing `latest_*` file means a hand-off is incomplete; `AccessDenied`, quota or S3 errors must be resolved at the failed boundary. **Cleanup:** record evidence first, remove endpoints and Registry resources in dependency order, then project storage and infrastructure according to [cleanup instructions](../README.md#10-cleanup-stop-charges-and-remove-only-your-project). **Next:** [Inference](../inference/README.md) or [Pipeline automation](../pipeline/README.md).
