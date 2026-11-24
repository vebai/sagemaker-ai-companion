# SageMaker AI workflow, infrastructure and troubleshooting

Run commands from the **repository root**, follow the book's chapter order, and check the result of each stage before continuing. Managed AWS jobs and endpoints may incur charges.

[Repository overview](../README.md) · [Account and tool setup](setup.md) · [Cleanup](cleanup.md)

## 5. Set up AWS infrastructure in the book's order

**Chapter 4 — create and verify the initial project resources.** Follow the book to create your project S3 bucket, the SageMaker execution role and its permissions. Verify the actual bucket, role trust, caller identity and `iam:PassRole` before running managed processing or training. **Do not run Terraform yet.** The repository supplies source files; cloning it does not create any AWS resources.

**Chapter 7 — build the Pipeline and configure its execution role.** The book's [ML release workflow](../examples/chapter-07/ml-release.yml) is supplied as an **inactive reference file**. Moving it into `.github/workflows/` will enable its triggers and can launch billable managed jobs. Keep it inactive until AWS role trust, required repository variables, instance quotas, approval gates and cost controls are confirmed.

**Chapter 8 — adopt existing infrastructure into Terraform.** The canonical [`infrastructure/terraform/`](../infrastructure/terraform/README.md) contains the full Chapter 8 book configuration (10 managed resources, referencing the existing shared GitHub OIDC provider). The book explains when to import rather than create existing resources. The repository makes one intentional exception to the printed Terraform code: it looks up the shared GitHub OIDC provider instead of managing it; the original printed source is preserved under `examples/chapter-08/`. Do not use `terraform apply` to create duplicate S3 buckets, IAM roles or a shared GitHub OIDC provider.

First create or identify a **separate, private S3 Terraform state bucket** according to Chapter 8. The state bucket must not be the project data bucket, and its lifecycle must be managed separately. Set `github_oidc_subject` to the exact subject of your GitHub repository, not the author's value. Initialise the backend with the same key as the book's Chapter 8 example:

```bash
terraform -chdir=infrastructure/terraform init -reconfigure \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config="key=sagemaker-churn/dev/terraform.tfstate" \
  -backend-config="region=eu-west-2" \
  -backend-config="encrypt=true"
```

**Before running this**, define `TF_STATE_BUCKET` for a state bucket you own and verify that its existing state belongs to this specific project. Initialise and validate, then follow the book's exact import and plan-review sequence. The GitHub OIDC provider at `token.actions.githubusercontent.com` is referenced as an existing shared resource. Verify that your AWS account has this provider before planning; do not import it into the project state.

## 6. Verify the Chapter 8 configuration before changes

From the repository root, while using your approved AWS profile:

```bash
source scripts/setup-env.sh
aws sts get-caller-identity
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform workspace show
terraform -chdir=infrastructure/terraform state list
terraform -chdir=infrastructure/terraform plan -out=project.tfplan
terraform -chdir=infrastructure/terraform show project.tfplan
terraform -chdir=infrastructure/terraform show -json project.tfplan > /tmp/sagemaker-ch08-plan.json
python scripts/review-chapter8-plan.py /tmp/sagemaker-ch08-plan.json
```

**Stop here and review the output.** The additional plan guard fails closed if the plan would create, modify or delete the GitHub OIDC provider, if it would delete resources, or if unexpected resource types appear. The shared provider is referenced, not owned by this stack. The guard is not an authorisation to apply. Only after completing the book's import steps, confirming resource ownership and reviewing the complete proposed changes should you run `terraform -chdir=infrastructure/terraform apply project.tfplan`. Provider, role and state ownership must be reviewed individually.

Terraform does not deploy SageMaker jobs, models or endpoints. The GitHub workflow remains inactive unless you deliberately enable it. This repository's Terraform checks were validated offline; a new, independent clean-account live deployment of this full Chapter 8 configuration has not been established.

## 7. Run the learning workflow

**A. Generate and upload the dataset (local; S3 upload incurs requests/storage).**

```bash
python data/create_dataset.py
head -n 3 data/customer_churn.csv
aws s3 cp data/customer_churn.csv "s3://$S3_BUCKET/raw/customer_churn.csv"
aws s3api head-object --bucket "$S3_BUCKET" --key raw/customer_churn.csv
```

You can inspect the processing implementation locally before paying for managed compute:

```bash
python processing/process.py \
  --input data/customer_churn.csv \
  --output data/processed
ls data/processed/{train,validation,test}/data.csv
```

**B. Managed processing (billable).** Confirm your **processing** quota for `ml.m5.xlarge`.

```bash
python workflow/run_processing.py
PROCESSING_JOB="$(cat workflow/latest_processing_job.txt)"
aws sagemaker describe-processing-job \
  --processing-job-name "$PROCESSING_JOB" \
  --query '{Status:ProcessingJobStatus,Failure:FailureReason}' --output json
```

The submission uses `wait=False`: **do not submit training until processing has reached `Completed`**. Check the job status again later, and verify the files:

```bash
for split in train validation test; do
  aws s3api head-object --bucket "$S3_BUCKET" \
    --key "processed/$split/data.csv" --query ContentLength --output text
done
```

**C. Managed training (billable).** Confirm your **training** quota for `ml.m5.xlarge`.

```bash
python workflow/run_training.py
TRAINING_JOB="$(cat workflow/latest_training_job.txt)"
aws sagemaker describe-training-job --training-job-name "$TRAINING_JOB" \
  --query '{Status:TrainingJobStatus,Failure:FailureReason}' --output json
```

Wait until the job reports `Completed`, then capture its actual model artefact URI for the next step:

```bash
aws sagemaker describe-training-job --training-job-name "$TRAINING_JOB" \
  --query 'ModelArtifacts.S3ModelArtifacts' --output text \
  > workflow/latest_model_artifact.txt
cat workflow/latest_model_artifact.txt
```

**D. Managed evaluation and release gate (billable).** The script reads `workflow/latest_model_artifact.txt`.

```bash
python workflow/run_evaluation.py
EVALUATION_JOB="$(cat workflow/latest_evaluation_job.txt)"
aws sagemaker describe-processing-job --processing-job-name "$EVALUATION_JOB" \
  --query '{Status:ProcessingJobStatus,Failure:FailureReason}' --output json
```

Wait for `Completed` before downloading the evidence expected by the packaging and registration scripts:

```bash
aws s3 cp "$(cat workflow/latest_evaluation_uri.txt)" evaluation/evaluation.json
python -m json.tool evaluation/evaluation.json | head -n 45
```

Review the measured metrics and `release_decision`. **A completed job does not prove acceptable model quality.** Only a passing candidate may progress to packaging and registration.

**E. Package and register only a passing release.**

```bash
python workflow/build_release_artifact.py
python workflow/register_model.py
cat workflow/latest_model_package_arn.txt
aws sagemaker describe-model-package \
  --model-package-name "$(cat workflow/latest_model_package_arn.txt)" \
  --query '{Status:ModelPackageStatus,Approval:ModelApprovalStatus}' \
  --output json
```

Registration starts in **`PendingManualApproval`**. Use Chapter 5 to inspect evidence and authorise approval explicitly. For a candidate you have independently confirmed meets the gate, the operator can approve it:

```bash
aws sagemaker update-model-package \
  --model-package-arn "$(cat workflow/latest_model_package_arn.txt)" \
  --model-approval-status Approved
aws sts get-caller-identity --query Arn --output text \
  > workflow/latest_approval_actor.txt
python workflow/write_release_record.py
```

This is a *manual governance decision*, not an instruction to approve a failing model. Deployment from the approved package, endpoint invocation, rollback, monitoring and verification are detailed in **Chapters 6 and 9**. A real-time endpoint incurs charges **until it is deleted**, even with no prediction traffic.

**F. SageMaker Pipeline and GitHub automation.** Start in **Chapter 7**:

```bash
python pipeline/build_pipeline.py
python -m json.tool pipeline/pipeline_definition.json >/dev/null
```

This builds a **local pipeline definition**; it does **not** publish or execute a pipeline. Follow Chapter 7 for creation/update, execution parameters, step inspection and release gating. The Pipeline can create multiple billable processing/training jobs per execution. GitHub's offline validation and OIDC identity-test workflows do **not** automatically run that pipeline.

## 8. Follow the repository map

Use this as the learning path; each link opens the relevant directory README. The stage number indicates **when to use it**, not a script to run automatically.

| Path | When to use it / expected outcome | AWS effect | Book chapter |
|---|---|---|
| [data/](../data/) | Start: generate a reproducible CSV dataset | Local only | 4 |
| [processing/](../processing/) | After data: validate and split into train/validation/test | Local or billable via workflow | 4 |
| [training/](../training/) | After processing: produce model artefact | Billable managed training | 4 |
| [evaluation/](../evaluation/) | After training: report metrics and release decision | Local or billable via workflow | 5 |
| [inference/](../inference/) | After approved release: serving input/output contract | Used by billable endpoint | 6 |
| [workflow/](../workflow/) | Orchestrate manual stages, package and register releases | Managed jobs and AWS changes | 4–5 |
| [pipeline/](../pipeline/) | Build an automated definition; publish/run via book | Local build; billable when run | 7 |
| [pipeline/release_source/](../pipeline/release_source/) | Supporting code bundled into the Pipeline release | Runs inside Pipeline | 7 |
| [infrastructure/terraform/](../infrastructure/terraform/) | **Chapter 8:** adopt and govern the book's full infrastructure configuration | Manages AWS infrastructure | 8 |
| [monitoring/](../monitoring/) | Chapter 9: data capture and input comparison | Local source; AWS capture has costs | 9 |
| [scripts/](../scripts/) | **Start here:** read AWS identity; offline validation | Read-only / local | Start |

Follow the linked README for each stage's **prerequisites → inputs → command → output → verification → next step**. The top-level `inference/` file is the manual release-serving implementation; `pipeline/release_source/` contains the corresponding code packaged by the managed Pipeline. They must remain compatible with the evaluated model. Generated files, credentials, local models and Terraform state should remain **outside Git**.

## 9. How to inspect failures

Start with identity and state, not repeated submissions:

```bash
aws sts get-caller-identity
echo "$AWS_REGION $S3_BUCKET"
aws sagemaker describe-processing-job --processing-job-name "$PROCESSING_JOB"
aws sagemaker describe-training-job --training-job-name "$TRAINING_JOB"
```

- **Quota/instance errors:** check the *correct operation-specific instance quota* in `eu-west-2`. Changing the training instance in one script does not update processing, Pipeline or endpoint settings.
- **`AccessDenied` or ECR errors:** distinguish caller IAM, `iam:PassRole`, SageMaker execution-role trust and permissions, organisation explicit denies and container image access.
- **Missing S3 files:** verify the exact bucket/key and previous job's `Completed` state. A submitted job is not a successful job.
- **Pipeline failed:** inspect failed step, CloudWatch logs and IAM rights including `sagemaker:AddTags` and required S3 read access; do not automatically approve a candidate.
- **Inference failures:** check endpoint state, model package/image compatibility, `text/csv` input format, feature order and the release threshold.
- **Cost surprises:** list live endpoints, active jobs, S3 versions and monitoring schedules before troubleshooting further. See Chapter 10.

Use the SageMaker AI console for visual confirmation of Processing jobs, Training jobs, Pipelines, Model Registry, Endpoints and CloudWatch logs. Keep the Region aligned.

