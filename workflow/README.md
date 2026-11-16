# Managed jobs, registration and release records

**Path:** [Data](../data/README.md) → [Process](../processing/README.md) → [Train](../training/README.md) → [Evaluate](../evaluation/README.md) → **Package and register** → [Inference](../inference/README.md)  
**Book:** Chapters 4–6 and 10 · **Cost:** processing, training and evaluation launch billable SageMaker jobs; registry operations alter AWS state

## Before running
From the repository root, activate Python and `source scripts/setup-env.sh`. Complete [project infrastructure](../README.md#5-set-up-aws-infrastructure-in-the-books-order), upload the raw CSV to `s3://$S3_BUCKET/raw/customer_churn.csv` and verify the relevant operation-specific quotas. The workflow scripts depend on outputs of earlier steps; they are **not** a single orchestration command.

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

**Chapter 7 GitHub delivery IAM:** The book creates `workflow/github-trust.json` and `workflow/github-pipeline-policy.json`. This repository provides [trust](github-trust.json.template) and [policy](github-pipeline-policy.json.template) templates. After establishing `GITHUB_OIDC_PROVIDER_ARN`, the exact `GITHUB_OIDC_SUB`, `S3_BUCKET` and `SAGEMAKER_PIPELINE_ROLE_ARN`, run `python scripts/render-iam.py github`. It creates local, ignored JSON files and performs **no AWS changes**. Review the exact OIDC subject and IAM permissions before using the book's role-creation commands.

**Additional manuscript files:** Chapter 4 generates `workflow/env.sh` locally and it remains gitignored. Chapter 6 uses [`write_deployment_verification.py`](write_deployment_verification.py) after a successful deployment to write a separate, durable verification record; it requires the known request, local and hosted responses and the exported model/endpoint identifiers. Chapter 10 defines [`empty_versioned_bucket.sh`](empty_versioned_bucket.sh) for *deliberate* deletion of verified versioned S3 objects. Preserve evidence and confirm the exact bucket before sourcing or invoking it. Neither script runs automatically. The cleanup helper defines a Bash function and must be **sourced deliberately**; making the file executable does not perform cleanup.

**Failure boundary:** missing `latest_*` file means a hand-off is incomplete; `AccessDenied`, quota or S3 errors must be resolved at the failed boundary. **Cleanup:** record evidence first, remove endpoints and Registry resources in dependency order, then project storage and infrastructure according to [cleanup instructions](../README.md#10-cleanup-stop-charges-and-remove-only-your-project). **Next:** [Inference](../inference/README.md) or [Pipeline automation](../pipeline/README.md).
