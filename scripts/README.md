# Start here — setup and validation utilities

**Path:** [Repository overview](../README.md) → **Local checks / AWS identity** → [Infrastructure](../infrastructure/terraform/README.md) → [Data](../data/README.md)  
**Book:** Before Chapter 4 · **Cost:** no AWS compute; `setup-env.sh` only reads AWS identity

## Run from the repository root
```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
terraform -chdir=infrastructure/terraform init -backend=false -input=false
./scripts/validate.sh
```

**Verify:** offline validation reports all five checks as PASS. `init -backend=false` downloads providers but does not create cloud resources.

When you are ready to work with AWS, authenticate with an authorised profile, then **source**, do not execute, the environment script:
```bash
aws sts get-caller-identity
source scripts/setup-env.sh
echo "$AWS_REGION $S3_BUCKET $SAGEMAKER_ROLE_ARN"
```

`setup-env.sh` exports `AWS_REGION`, `PROJECT_NAME`, `S3_BUCKET` and `SAGEMAKER_ROLE_ARN` into the current shell. **It does not create the bucket or IAM role** and does not test your SageMaker quotas.

**Failure boundary:** Python version, missing Terraform providers, incorrect AWS credentials/profile or mismatched Region. **Cleanup:** `deactivate` exits the Python virtual environment; do not remove Terraform state or AWS resources as part of local setup. **Next:** [Infrastructure](../infrastructure/terraform/README.md) before billable managed jobs.
