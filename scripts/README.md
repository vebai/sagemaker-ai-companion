# Start here — setup and validation utilities

**Path:** [Repository overview](../README.md) → **Local checks / AWS identity** → [Infrastructure](../infrastructure/terraform/README.md) → [Data](../data/README.md)  
**Book:** Before Chapter 4 · **Cost:** no AWS compute; `setup-env.sh` only reads AWS identity

## Run from the repository root
```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
./scripts/validate.sh
```

**Verify:** offline validation reports its checks as PASS. The script initialises Terraform providers without using a backend and does not create cloud resources.

When you are ready to work with AWS, authenticate with an authorised profile, then **source**, do not execute, the environment script:
```bash
aws sts get-caller-identity
source scripts/setup-env.sh
echo "$AWS_REGION $S3_BUCKET $SAGEMAKER_ROLE_ARN"
```

`setup-env.sh` exports `AWS_REGION`, `PROJECT_NAME`, `S3_BUCKET` and `SAGEMAKER_ROLE_ARN` into the current shell. **It does not create the bucket or IAM role** and does not test your SageMaker quotas.

**Chapter 8 plan review:** After generating the full book Terraform plan, run `terraform -chdir=infrastructure/terraform show -json project.tfplan > /tmp/sagemaker-ch08-plan.json`, then `python scripts/review-chapter8-plan.py /tmp/sagemaker-ch08-plan.json`. It blocks changes to a shared GitHub OIDC provider, resource deletions and unexpected managed resources; it never applies changes.

**Failure boundary:** Python version, missing Terraform providers, incorrect AWS credentials/profile or mismatched Region. **Cleanup:** `deactivate` exits the Python virtual environment; do not remove Terraform state or AWS resources as part of local setup. **Next:** Follow [Chapter 4 AWS setup](../README.md#5-set-up-aws-infrastructure-in-the-books-order) before billable managed jobs; use Terraform as taught in Chapter 8.
