# Deploying Machine Learning with Amazon SageMaker AI

Companion code for **Deploying Machine Learning with Amazon SageMaker AI** by Victor Ebai.

This repository provides the working files used in the book's practical exercises. The book explains the engineering decisions, implementation sequence, evidence interpretation, troubleshooting and recovery procedures.

## Learning workflow

Prepare data → Process → Train → Evaluate → Apply release gate → Package → Register → Deploy → Monitor → Diagnose → Recover

Follow the book's chapters in order when running AWS exercises. The scripts are not independent deployment shortcuts.

## Prerequisites

- Python 3.11 and pip
- AWS CLI configured with an appropriate AWS identity
- Terraform 1.10 or later for infrastructure exercises
- An AWS account with the required SageMaker quotas and permissions
- AWS Region `eu-west-2` for the documented labs

Managed SageMaker jobs and real-time endpoints can incur charges. Check quotas, review costs and follow the book's cleanup procedures.

## Quick start

Run from your MacBook or an appropriately configured Linux workstation:

```bash
git clone https://github.com/vebai/sagemaker-ai-companion.git
cd sagemaker-ai-companion
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
source scripts/setup-env.sh
./scripts/validate.sh
```

The GitHub URL above is the **proposed** repository address. It will work once the repository has been created under that name.

`setup-env.sh` checks your AWS identity and prepares environment variables. It does not create cloud resources.

## Repository structure

| Directory | Purpose |
|---|---|
| `data/` | Generate the example dataset |
| `processing/` | Prepare and split data |
| `training/` | Train and save the model |
| `evaluation/` | Evaluate performance and produce evidence |
| `inference/` | Model serving contract |
| `workflow/` | Managed jobs, registration and release records |
| `pipeline/` | SageMaker Pipeline and release packaging |
| `infrastructure/terraform/` | Project bucket, IAM roles and S3 controls |
| `scripts/` | Environment setup and offline validation |

Read the README inside each directory before using its scripts.

## AWS environment

```bash
source scripts/setup-env.sh
```

This sets `AWS_REGION`, `PROJECT_NAME`, `S3_BUCKET` and `SAGEMAKER_ROLE_ARN` using your current AWS account.

The IAM roles and project S3 bucket must exist before running managed workloads. Follow the infrastructure setup in the book.

Terraform's S3 backend requires a separately prepared state bucket. Do not point it at the project data bucket.

## Verification

```bash
./scripts/validate.sh
```

This performs offline Python syntax, IAM template and Terraform checks. It does not train a model or prove that AWS resources have been deployed successfully.

## Cost control and cleanup

Stop or delete active endpoints after completing serving and monitoring exercises. Inspect active jobs and other billable resources. Preserve evidence needed for verification before deleting storage.

If Terraform manages your resources, review ownership and the destruction plan before applying it. Never delete a shared GitHub OIDC provider or another project's Terraform state.

## Important

Use your own AWS credentials and account. Do not commit credentials, generated model artefacts, Terraform state, S3 data or private validation evidence.
