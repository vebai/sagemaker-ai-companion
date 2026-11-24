# SageMaker AI — safe project cleanup

These steps intentionally separate control-plane cleanup, versioned S3 deletion, Terraform-managed resources and shared AWS infrastructure. **They are destructive; nothing runs automatically.**

[Repository overview](../README.md) · [AWS account checks](setup.md) · [S3 helper](../workflow/empty_versioned_bucket.sh)

## Stop compute, preserve evidence and remove project resources

> **Destructive actions.** This is not one command. Follow **Chapter 10, sections 10.13–10.14**, preserve evidence first, and verify ownership and dependencies. **Never run cleanup in a shared account without approval.** Deleting S3 versions and SageMaker control-plane resources is irreversible unless you have independently retained a backup.

**A. Stop active compute first.** Inspect rather than assuming all jobs are finished:

```bash
aws sagemaker list-endpoints --name-contains sagemaker-churn
aws sagemaker list-training-jobs --name-contains sagemaker-churn
aws sagemaker list-processing-jobs --name-contains sagemaker-churn
aws sagemaker list-pipelines --pipeline-name-prefix sagemaker-churn
aws sagemaker list-monitoring-schedules --name-contains sagemaker-churn
```

Stop in-progress jobs if necessary, and **delete project-owned endpoints** as soon as serving experiments are complete, using the actual names returned by AWS. Do **not** delete another team's resources. A SageMaker model, endpoint configuration, registered package and pipeline have separate lifecycles. After confirming there are no dependent endpoints or active executions, delete project-owned endpoint configurations, models, model package *versions*, model package group and pipeline in that order, using Chapter 10 and the actual resource names. Do not assume resources from a different run will have the example names.

**B. Back up S3 data and versions before emptying the project bucket.** The bucket has Terraform `force_destroy = false` and **versioning enabled**. `aws s3 rm --recursive` alone is **not enough** to clear versions; it can create delete markers. Export artefacts and metadata to a separate, trusted location and verify the backup first.

List versions and delete markers:

```bash
aws s3api list-object-versions --bucket "$S3_BUCKET" \
  --query '{Versions:Versions[].{Key:Key,VersionId:VersionId},DeleteMarkers:DeleteMarkers[].{Key:Key,VersionId:VersionId}}' \
  --output json
```

For a **dedicated, verified project bucket only**, after separately backing up the data and recording the complete version inventory, use the existing [versioned-S3 cleanup helper](../workflow/empty_versioned_bucket.sh). It is a sourced function, **not an automatically executed script**. The function checks the selected Region, your actual AWS account via STS, the exact expected project bucket name, `S3_BUCKET`, and an explicit confirmation variable before deleting versions or delete markers.

From the **repository root**, inspect first and proceed only after independently verifying the backup and every resource identifier:

```bash
source scripts/setup-env.sh
aws sts get-caller-identity
aws s3api list-object-versions --bucket "$S3_BUCKET" --output json
# Check the inventory and the separate backup before proceeding.
source workflow/empty_versioned_bucket.sh
export CONFIRM_EMPTY_PROJECT_BUCKET="YES_DELETE_ALL_PROJECT_VERSIONS"
empty_versioned_bucket "$S3_BUCKET" "sagemaker-churn-${ACCOUNT_ID}-eu-west-2"
unset CONFIRM_EMPTY_PROJECT_BUCKET
aws s3api list-object-versions --bucket "$S3_BUCKET" --output json
```

**Stop if the inventory changes after backup.** Never run this operation on a shared bucket or without permission. The helper reports and aborts when AWS returns object-level deletion errors; verify that both versions and delete markers are absent afterwards. It is not a replacement for backup, review or cost verification.

**C. Destroy only the Terraform-managed project resources, after resolving shared OIDC ownership.** From the repository root, with the **same Terraform backend, workspace and state** originally used for deployment:

```bash
aws sts get-caller-identity
terraform -chdir=infrastructure/terraform workspace show
terraform -chdir=infrastructure/terraform state list
terraform -chdir=infrastructure/terraform plan -destroy -out=destroy.tfplan
terraform -chdir=infrastructure/terraform show destroy.tfplan
# Confirm the exact resources, account and state before executing:
terraform -chdir=infrastructure/terraform apply destroy.tfplan
terraform -chdir=infrastructure/terraform state list
```

**Critical:** The canonical Chapter 8 Terraform stack reads the account-wide GitHub OIDC provider through a data source; it does not own or destroy that provider. Never apply the destruction plan if it proposes deleting or replacing shared infrastructure; separate its lifecycle into an approved owning state or otherwise settle ownership before destruction. A clean state listing should show no project resources. Verify the actual S3 bucket and IAM roles are absent with AWS CLI as well. **Do not** use `terraform destroy` against a backend whose ownership or contents you have not established.

**D. Clean remaining non-Terraform resources deliberately.** Inspect any project-specific endpoint logs, monitoring data, model records and AWS alarms. CloudWatch log groups such as **`/aws/sagemaker/TrainingJobs`** and **`/aws/sagemaker/ProcessingJobs`** are shared; **do not delete them**. The endpoint log group may hold useful evidence; retain it or remove it only after separate review. Confirm the absence of active endpoints and jobs, and check Billing/Cost Explorer for delayed charges.

**E. Keep the state backend and shared identity resources separate.** The state bucket, its previous versions and lock history are **outside this Terraform stack**. Retain state evidence or destroy the backend only after confirming that **no other workspace, deployment or owner uses it**. Do not delete shared OIDC identity providers or GitHub roles: these are outside the SageMaker Terraform module.

