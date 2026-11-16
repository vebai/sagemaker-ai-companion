# Foundation — Terraform infrastructure

**Path:** [Start](../../README.md) → **AWS foundation** → [Data](../../data/README.md) → [Managed workflow](../../workflow/README.md)  
**Book:** Chapter 8 · **Cost:** creates S3/IAM resources; storage, S3 versions, logs and managed workloads may incur AWS charges

## Purpose and prerequisites
The Terraform configuration manages **eight** project-owned resources: the project S3 bucket, its public-access/versioning/encryption controls, two SageMaker execution IAM roles and their inline policies. It does **not** deploy SageMaker jobs, a Pipeline, model endpoints, CloudWatch log groups, a GitHub OIDC provider or its test roles.

Before an apply, install Terraform >= 1.10, authenticate AWS CLI to the correct account, use Region `eu-west-2`, verify IAM/S3 permissions and prepare a **separate, private S3 bucket for Terraform state**. The project bucket must not be used as its own backend. Full, copyable backend bootstrap commands are in the [root README](../../README.md#5-bootstrap-a-private-s3-backend-for-terraform).

## Offline validation (no AWS resources created)
From the repository root:
```bash
terraform -chdir=infrastructure/terraform init -backend=false -input=false
terraform -chdir=infrastructure/terraform validate
./scripts/validate.sh
```

## Apply (AWS resources created)
First initialise the dedicated backend using the root README. Then, from the repository root:
```bash
source scripts/setup-env.sh
aws sts get-caller-identity
terraform -chdir=infrastructure/terraform workspace show
terraform -chdir=infrastructure/terraform plan -out=project.tfplan
terraform -chdir=infrastructure/terraform show project.tfplan
# Review the complete plan and account before you authorise:
terraform -chdir=infrastructure/terraform apply project.tfplan
```

**Verify:** `aws s3api head-bucket --bucket "$S3_BUCKET"` and `aws iam get-role --role-name SageMakerChurnExecutionRole` plus `SageMakerChurnPipelineRole`; verify role trust and permissions. State ownership matters: **do not adopt or overwrite existing manually created resources without the book's Chapter 8 procedure**. The static validation does not establish a successful deployment from a fresh account.

## Destroy only after dependent AWS resources have been removed
Follow [root cleanup](../../README.md#10-cleanup-stop-charges-and-remove-only-your-project) and Chapter 10. Back up evidence; stop/delete endpoints and remove model/registry/Pipeline resources; inspect S3 **all object versions and delete markers**. The bucket uses `force_destroy = false`, so it must be empty before Terraform can delete it.

```bash
aws sts get-caller-identity
terraform -chdir=infrastructure/terraform workspace show
terraform -chdir=infrastructure/terraform state list
terraform -chdir=infrastructure/terraform plan -destroy -out=destroy.tfplan
terraform -chdir=infrastructure/terraform show destroy.tfplan
# Execute only the reviewed plan:
terraform -chdir=infrastructure/terraform apply destroy.tfplan
terraform -chdir=infrastructure/terraform state list
```

**The separately created state bucket, any shared IAM/OIDC provider and GitHub test roles remain outside this stack.** Review state retention independently; do not destroy another project's state or shared infrastructure. **Failure boundary:** missing permissions, pre-existing role/bucket names, S3 versions or wrong backend/workspace. **Next:** [Prepare dataset](../../data/README.md).
