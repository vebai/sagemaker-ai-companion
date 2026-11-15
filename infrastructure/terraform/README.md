# Terraform infrastructure

This directory defines the project S3 bucket, S3 security controls, SageMaker workload IAM role and SageMaker Pipeline IAM role.

## Prerequisites

- Terraform 1.10 or later
- AWS CLI authenticated to the intended account
- Region `eu-west-2`
- A separately created S3 bucket for Terraform backend state

The backend uses S3 locking. Each reader must configure their own state bucket.

## Offline validation

From the repository root:

```bash
terraform -chdir=infrastructure/terraform init -backend=false
terraform -chdir=infrastructure/terraform validate
```

The first command downloads providers but does not connect the remote backend or create AWS infrastructure.

## Deployment

Follow the book's backend bootstrap, `terraform init`, reviewed `terraform plan` and `terraform apply` instructions. Do not run `apply` before reviewing the target account, IAM permissions and potential resource costs.

## Cleanup

Export any required evidence first. Review `terraform state list` and a destruction plan. Only destroy resources that belong to this project. The separate backend bucket and shared platform infrastructure are outside this stack.
