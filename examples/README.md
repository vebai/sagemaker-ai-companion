# Chapter 7 — Release workflow source

The book's `ml-release.yml` is provided at [`chapter-07/ml-release.yml`](chapter-07/ml-release.yml). It is deliberately **inactive** because the exact Chapter 7 workflow starts billable SageMaker Pipeline executions when triggered.

The book's full Chapter 8 Terraform configuration is in [`infrastructure/terraform/`](../infrastructure/terraform/README.md). The earlier eight-resource implementation is preserved in `infrastructure/terraform-legacy/` for migration and audit only.

**Before activating delivery:** configure the required GitHub repository variables, review OIDC trust and role permissions, validate the AWS account and Region, check SageMaker quotas and costs, and ensure manual approval remains separate. Do not move this file into `.github/workflows/` until those controls are satisfied.

For an offline check of the chapter's Terraform configuration, run from the repository root:

```bash
terraform -chdir=infrastructure/terraform init -backend=false -input=false
terraform -chdir=infrastructure/terraform validate
```

No deployment is performed by this example file in its current location.
