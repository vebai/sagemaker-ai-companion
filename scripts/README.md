# Start here — setup and validation utilities

**Path:** [Repository overview](../README.md) → **Local checks / AWS identity** → [Infrastructure](../infrastructure/terraform/README.md) → [Data](../data/README.md)  
**Book:** Before Chapter 4 · **Cost:** no AWS compute; `setup-env.sh` only reads AWS identity

## Run from the repository root
```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
chmod +x ./scripts/validate.sh
./scripts/validate.sh
```

When cloned with Git, `validate.sh` already has the executable bit. The `chmod` line is a safe fallback for ZIP downloads or copied files that lost executable permissions. Python programs are invoked with `python`, so they do not require an executable bit. `scripts/setup-env.sh` must be **sourced** and `workflow/empty_versioned_bucket.sh` defines a function that must be sourced deliberately; neither should be run as a standalone workload.

**Verify:** offline validation reports its checks as PASS. The script initialises Terraform providers without using a backend and does not create cloud resources.

When you are ready to work with AWS, authenticate with an authorised profile, then **source**, do not execute, the environment script:
```bash
aws sts get-caller-identity
source scripts/setup-env.sh
echo "$AWS_REGION $S3_BUCKET $SAGEMAKER_ROLE_ARN"
```

`setup-env.sh` exports the seven Chapter 4 variables: `AWS_REGION`, `AWS_DEFAULT_REGION`, `ACCOUNT_ID`, `PROJECT_NAME`, `S3_BUCKET`, `SAGEMAKER_ROLE_NAME` and `SAGEMAKER_ROLE_ARN` into the current shell. **It does not create the bucket or IAM role** and does not test your SageMaker quotas.

**Chapter 7 IAM source:** `python scripts/render-iam.py pipeline` and `python scripts/render-iam.py github` create the corresponding book filenames from local templates after the required variables are exported. The renderer makes no AWS calls and never overwrites different existing files. See the [Pipeline](../pipeline/README.md) and [workflow](../workflow/README.md) guides.

**Chapter 8 plan review:** After generating the full book Terraform plan, run `terraform -chdir=infrastructure/terraform show -json project.tfplan > /tmp/sagemaker-ch08-plan.json`, then `python scripts/review-chapter8-plan.py /tmp/sagemaker-ch08-plan.json`. It blocks changes to a shared GitHub OIDC provider, resource deletions and unexpected managed resources; it never applies changes.

**Failure boundary:** Python version, missing Terraform providers, incorrect AWS credentials/profile or mismatched Region. **Cleanup:** `deactivate` exits the Python virtual environment; do not remove Terraform state or AWS resources as part of local setup. **Next:** Follow [Chapter 4 AWS setup](../README.md#5-set-up-aws-infrastructure-in-the-books-order) before billable managed jobs; use Terraform as taught in Chapter 8.
