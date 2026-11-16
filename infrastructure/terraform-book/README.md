# Chapter 8 — Full Terraform configuration from the book

**Source:** Section 8.6 of *Deploying Machine Learning with Amazon SageMaker AI*, 16 November 2026 manuscript.

This directory contains the **book's** `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf` and `terraform.tfvars.example`, extracted without changing their intended resource configuration.

The original eight-resource companion implementation remains in [`../terraform/`](../terraform/README.md). **Use one Terraform configuration and one state at a time. Do not initialise the two projects with the same backend key.**

## Read-only/offline check

```bash
terraform -chdir=infrastructure/terraform-book init -backend=false -input=false
terraform -chdir=infrastructure/terraform-book validate
```

The build checks configuration syntax and provider schemas; it does **not** prove that an apply would succeed in a fresh account.

## Before any live apply

The book example manages the **GitHub OIDC provider** and the GitHub delivery role in addition to the S3 bucket and SageMaker roles. If `token.actions.githubusercontent.com` is already managed by another Terraform state or team, **do not create/import it into this state without approval and a complete lifecycle ownership decision**.

The book's Chapter 8 teaches **adoption of existing AWS resources through imports**, not blind creation of duplicates. Review the exact AWS account, Region, state bucket, backend key and `github_oidc_subject` before planning. The sample uses `dev`, `eu-west-2`, and a separate state bucket with S3 locking and versioning. Plan actions, review before apply and stop if a protected shared provider is listed for deletion or replacement.

The [Chapter 7 GitHub release workflow](../../examples/chapter-07/ml-release.yml) is staged as an **inactive example**. No push to this repository currently starts that workflow from the example file. Activation requires conscious configuration and cost review.

**Never run `terraform apply` or `terraform destroy` just to validate this extracted example.**
