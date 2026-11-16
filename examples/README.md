# Manuscript Chapters 7–8 — Canonical source under review

These files reproduce the source listings printed in *Deploying Machine Learning with Amazon SageMaker AI* (uploaded 16 November 2026, 21:18). The **manuscript is unchanged**.

## What is where

- [`infrastructure/terraform-book/`](../../infrastructure/terraform-book/README.md): Chapter 8's full Terraform configuration, including project storage, two SageMaker roles, the GitHub OIDC provider, GitHub delivery role and IAM policies.
- [`examples/chapter-07/ml-release.yml`](../chapter-07/ml-release.yml): Chapter 7's complete ML release workflow, **stored as a reference and not an active GitHub workflow**.
- [`infrastructure/terraform/`](../../infrastructure/terraform/README.md): the existing **eight-resource** companion stack, preserved while the book implementation is reviewed. Do not mix these two Terraform states.

## Offline validation (does not deploy)

From the repository root:

```bash
terraform -chdir=infrastructure/terraform-book init -backend=false -input=false
terraform -chdir=infrastructure/terraform-book validate
terraform -chdir=infrastructure/terraform init -backend=false -input=false
./scripts/validate.sh
```

## Do not deploy until ownership is resolved

The Chapter 8 source **creates an AWS GitHub OIDC provider** at `token.actions.githubusercontent.com`. The author's AWS account already has a shared provider, so applying the book configuration without an explicit import/ownership decision can conflict with existing infrastructure. The original Chapter 8 example is retained exactly for review, not made the default applied stack.

The Chapter 7 YAML automatically starts billable SageMaker Pipeline executions for some pushes to `main` if placed under `.github/workflows/`. It is deliberately under `examples/` so it cannot run. Activate only after configuring the required GitHub variables, restricting the AWS trust policy to the correct repository identity, checking service quotas and costs, and intentionally approving the trigger behaviour.

**Validation boundary:** The manuscript listing has been extracted and Terraform receives offline validation in CI. No new AWS infrastructure or billable ML job was started by this alignment work.
