# Chapter 8 — Full Terraform configuration from the book

**Book:** Chapter 8, Section 8.6.

This directory contains the **book's** `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf` and `terraform.tfvars.example`, matching the book's configuration with one deliberate safety change: **the shared GitHub OIDC provider is read using a Terraform data source, not created or owned by this stack**. The exact printed `main.tf` and `outputs.tf` are retained under [`../../examples/chapter-08/`](../../examples/chapter-08/).

The earlier eight-resource implementation is retained for migration review in [`../terraform-legacy/`](../terraform-legacy/README.md). **Use one Terraform configuration and one state at a time. Do not initialise the two projects with the same backend key.**

## Read-only/offline check

```bash
terraform -chdir=infrastructure/terraform init -backend=false -input=false
terraform -chdir=infrastructure/terraform validate
```

The build checks configuration syntax and provider schemas; it does **not** prove that an apply would succeed in a fresh account.

## Review the exact plan (read-only)

Once you have completed the book's controlled state ownership and import steps, generate a saved plan and review it before any AWS mutation:

```bash
terraform -chdir=infrastructure/terraform plan -out=project.tfplan
terraform -chdir=infrastructure/terraform show project.tfplan
terraform -chdir=infrastructure/terraform show -json project.tfplan > /tmp/sagemaker-ch08-plan.json
python scripts/review-chapter8-plan.py /tmp/sagemaker-ch08-plan.json
```

The plan reviewer intentionally **stops** if Terraform proposes any creation, replacement or modification of the shared OIDC provider, or any deletion. It is a safety check, not blanket approval of a live apply; follow the book's identity and import steps before considering it.

## Before any live apply

The book's printed example manages the **GitHub OIDC provider** and the GitHub delivery role in addition to the S3 bucket and SageMaker roles. The canonical repository version references `token.actions.githubusercontent.com` as an existing shared provider. You must verify it exists and has audience `sts.amazonaws.com`. It is not part of this Terraform stack's lifecycle.

Follow Chapter 8 to **adopt existing AWS resources through imports**, rather than creating duplicates. Review the exact AWS account, Region, state bucket, backend key and `github_oidc_subject` before planning. The sample uses `dev`, `eu-west-2`, and a separate state bucket with S3 locking and versioning. Plan actions, review before apply and stop if a shared provider appears as a managed resource in the plan.

The [Chapter 7 GitHub release workflow](../../examples/chapter-07/ml-release.yml) is staged as an **inactive example**. No push to this repository currently starts that workflow from the example file. Activation requires conscious configuration and cost review.

**Never run `terraform apply` or `terraform destroy` just to validate this extracted example.**
