# Deploying Machine Learning with Amazon SageMaker AI — Companion Code

**Book:** *Deploying Machine Learning with Amazon SageMaker AI: Training, Deployment, Automation, and Production Operations on AWS* — Victor Ebai  
**Repository:** https://github.com/vebai/sagemaker-ai-companion  
**Licence:** [MIT](LICENSE) for repository code. The book's prose and diagrams are separately copyrighted.

**What you will do:** Set up a small customer-churn project, create your own AWS foundation, prepare data, run managed SageMaker processing and training, evaluate the result, and decide whether to register and deploy it. The book explains each decision; this repository supplies the accompanying source files and repeatable commands.

**Start safely:** You can clone, install dependencies, generate example data and run offline checks **without creating AWS resources**. Running managed processing, training or a real-time endpoint **can incur AWS charges**. You must create the AWS foundation before submitting jobs. The code does not automatically deploy an endpoint or clean up your account.

**Where to start:** [Install the tools](#2-install-tools-on-your-workstation) → [Clone and check the code](#3-clone-configure-python-and-verify-identity) → [Set up AWS infrastructure](#5-bootstrap-a-private-s3-backend-for-terraform) → [Run the exercises](#7-run-the-learning-workflow) → [Clean up](#10-cleanup-stop-charges-and-remove-only-your-project).

## Read this first — what runs where?

| Action | Where | AWS cost or change? | Success evidence |
|---|---|---|---|
| Clone and install Python packages | Local Mac/Linux | No AWS changes | Virtual environment, installed dependencies |
| Generate data; run local processing | Local Mac/Linux | No AWS changes | CSV dataset and split files |
| Run `scripts/validate.sh` | Local Mac/Linux | No AWS changes | Offline source/Terraform checks pass |
| Run `scripts/setup-env.sh` | Local shell, reads AWS STS | Read-only AWS call | Correct AWS account, Region and bucket name |
| Terraform `apply` | Local shell → AWS | **Creates infrastructure** | Project bucket and IAM roles exist |
| Submit processing, training or evaluation | Local shell → SageMaker | **Billable managed jobs** | Job reaches `Completed`, outputs exist |
| Register/approve a model | Local shell → SageMaker | **Changes registry state** | Correct package and approval evidence |
| Deploy an endpoint (book Chapter 6) | AWS | **Billable while running, even when idle** | Inference request verified |
| Clean up (book Chapter 10) | AWS | **Destructive** | Resources absent; evidence retained |

**Do not run the next stage merely because the previous command exited successfully.** For SageMaker jobs, verify the managed job status and expected artefacts first.

## The workflow at a glance

```text
Local Mac/Linux shell
  ├── Python dataset generation ──> S3 raw/customer_churn.csv
  ├── Terraform ──> project S3 bucket + two SageMaker IAM roles
  └── SageMaker submissions (managed AWS compute; billed when used)
        Processing ──> S3 processed/{train,validation,test}/data.csv
        Training ──> S3 model.tar.gz
        Evaluation ──> evaluation.json + release decision
        Passing candidate ──> packaged release ──> Model Registry
        Explicit approval ──> endpoint deployment and invocation (book)
        SageMaker Pipeline ──> automated processing, training,
                               evaluation, conditional packaging/registration
        Monitoring and diagnosis ──> evidence (book)
        Cleanup ──> remove model/endpoint/registry resources,
                    empty versioned project bucket, Terraform destroy
```

**Environment:** AWS Region `eu-west-2` (London); Python **3.11**; pinned dependencies from [requirements.txt](requirements.txt); Terraform **>= 1.10** with AWS provider 6.x. Examples in `workflow/` and `pipeline/` currently request **`ml.m5.xlarge`** for processing/training and **`ml.m5.large`** for real-time inference. These instance types must be available and permitted in *your* account and Region.

## 1. Before creating anything in AWS

- Use your **own authorised AWS account**, preferably a disposable learning account, with billing alerts/budgets configured. Do not experiment in an employer's production account.
- Know which identity will operate Terraform and submit SageMaker jobs. Prefer AWS IAM Identity Center/SSO or temporary credentials over static access keys. The Terraform operator needs separate rights to manage S3, IAM and Terraform state; the SageMaker caller needs the appropriate SageMaker APIs, `iam:PassRole` to the project roles, and access to its S3 inputs/outputs. Organisation SCPs and explicit denies override IAM allows.
- **Check quotas before running managed jobs.** Use the AWS Console: **Service Quotas → Amazon SageMaker AI →** check *processing job*, *training job* and *endpoint* usage for the **exact instance type**. Quotas are operation-specific: a processing quota does not authorise training or inference. New accounts may have zero quotas; approval is not guaranteed. Also verify the scikit-learn image is available in `eu-west-2`.
- Charges can arise from **processing, training, Pipelines' underlying jobs, live endpoints (even when idle), S3 objects and versions, CloudWatch logs, data transfer and ancillary services**. Running scripts again can create additional jobs and model versions. Budgets alert you; they do not automatically stop charges. Verify current pricing: https://aws.amazon.com/sagemaker/ai/pricing/ .
- **Keep your Terraform state bucket separate from the project data bucket.** Do not delete a state bucket used by any other stack.
- The repository uses a fixed project prefix and role names: **`sagemaker-churn`**, **`SageMakerChurnExecutionRole`** and **`SageMakerChurnPipelineRole`**. Existing resources with these names can conflict. If you have already built them manually from the book, **do not apply Terraform over them blindly**; follow Chapter 8's ownership/adoption process first.

## 2. Install tools on your workstation

**macOS (Homebrew).** If Homebrew is not installed, first follow https://brew.sh/ . In Terminal:

```bash
brew update
brew install git awscli python@3.11
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
git --version
aws --version
python3.11 --version
terraform version
```

**Ubuntu/Debian.** Install Git, basic prerequisites and AWS CLI v2; select the AWS CLI archive for your machine architecture (example below is x86_64; for ARM64 use `awscli-exe-linux-aarch64.zip`). See https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html .

```bash
sudo apt-get update
sudo apt-get install -y git curl unzip gnupg ca-certificates wget
curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscliv2.zip
(cd /tmp && unzip -q awscliv2.zip && sudo ./aws/install)
aws --version
git --version
```

Install **Python 3.11** with its `venv` support from your distribution's appropriate supported packages or Python's official installation instructions (https://www.python.org/downloads/). On systems where `python3.11` is provided by APT:

```bash
sudo apt-get install -y python3.11 python3.11-venv
python3.11 --version
```

Install Terraform from HashiCorp's signed APT repository (https://developer.hashicorp.com/terraform/install):

```bash
wget -qO- https://apt.releases.hashicorp.com/gpg | \
  gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(. /etc/os-release && echo "$VERSION_CODENAME") main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update
sudo apt-get install -y terraform
terraform version
```

For Fedora/RHEL, use the official HashiCorp and AWS CLI installation guides for `dnf`; verify Python 3.11 and `python3.11 -m venv` before continuing. **AWS CloudShell** already provides an authenticated AWS CLI in many accounts, but its Python/Terraform versions, storage persistence and installed packages must be checked; local Mac/Linux execution is the documented default.

## 3. Clone, configure Python, and verify identity

Run commands from the **repository root** unless a section says otherwise. Open a new terminal and source the virtual environment again each time.

```bash
git clone https://github.com/vebai/sagemaker-ai-companion.git
cd sagemaker-ai-companion
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**What local setup proves:** You have a Python 3.11 environment and installed packages. It has **not** trained a model, deployed an endpoint or verified a live AWS architecture.

**Sign in to AWS (read-only identity step).** Preferred example for an IAM Identity Center profile (substitute your configured profile):

```bash
aws configure sso --profile sagemaker-lab
aws sso login --profile sagemaker-lab
export AWS_PROFILE=sagemaker-lab
aws sts get-caller-identity
```

If you already have an authorised AWS profile or temporary credentials, use those instead. **Never paste credentials into repository files or commit them.** Verify the correct account before every `plan`, `apply` and destructive operation.

```bash
source scripts/setup-env.sh
echo "$AWS_REGION"
echo "$S3_BUCKET"
echo "$SAGEMAKER_ROLE_ARN"
```

The setup script reads your AWS identity and exports these variables into **your current shell**:

| Variable | What it means |
|---|---|
| `AWS_REGION` | AWS Region used by the examples: `eu-west-2` |
| `PROJECT_NAME` | Project prefix used for naming: `sagemaker-churn` |
| `S3_BUCKET` | Account-specific bucket containing raw/processed data, models and evidence |
| `SAGEMAKER_ROLE_ARN` | IAM execution role assumed by managed SageMaker jobs |

**The script does not create resources, grant permissions or verify that the role exists.** If you open a new terminal, change accounts or switch AWS profiles, activate the Python environment and **source `scripts/setup-env.sh` again**.

## 4. Check the repository without creating resources

```bash
terraform -chdir=infrastructure/terraform init -backend=false -input=false
./scripts/validate.sh
```

**What this quick check proves:** Python source parses; pinned dependencies are declared; IAM policy templates render as valid JSON; Terraform configuration validates; and the source does not contain a fixed 12-digit account number. **What it does not prove:** permissions in your account, resource creation, completed jobs, model quality or endpoint health.

This checks Python syntax, pinned dependencies, IAM policy templates, Terraform formatting/validation and accidental fixed account IDs in Terraform source. The first command downloads Terraform providers; **neither command deploys SageMaker resources**. GitHub's [Validate companion code](.github/workflows/validate.yml) runs similar checks on pushes. The separate [OIDC identity test](.github/workflows/oidc-identity.yml) is for the author's AWS account only; it is **not** a reader deployment workflow and does not grant a reader permissions.

## 5. Bootstrap a private S3 backend for Terraform

**Mandatory gate before managed jobs:** Your own project S3 bucket and SageMaker execution roles must exist and the caller must have the correct permissions. Complete this infrastructure section and Section 6 first; don't proceed just because local validation passed.

Skip this section if your organisation provides an **approved, dedicated Terraform backend**; use its bucket and key instead. The backend holds **sensitive infrastructure state** and is not managed by this project stack.

For a new isolated personal lab, source `scripts/setup-env.sh`, then set a globally unique backend bucket name (adjust the suffix if already taken). The example creates a bucket; **it can incur storage/request costs**.

```bash
export TF_STATE_BUCKET="sagemaker-tfstate-$(aws sts get-caller-identity --query Account --output text)-eu-west-2"
aws s3api head-bucket --bucket "$TF_STATE_BUCKET" 2>/dev/null && {
  echo "STOP: Backend bucket exists; inspect ownership/state before proceeding"
  exit 1
}
aws s3api create-bucket --bucket "$TF_STATE_BUCKET" \
  --region eu-west-2 \
  --create-bucket-configuration LocationConstraint=eu-west-2
aws s3api put-public-access-block --bucket "$TF_STATE_BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-encryption --bucket "$TF_STATE_BUCKET" \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-bucket-versioning --bucket "$TF_STATE_BUCKET" \
  --versioning-configuration Status=Enabled
aws s3api get-bucket-versioning --bucket "$TF_STATE_BUCKET"
```

**Before Terraform init:** confirm that the operator has `s3:ListBucket` on the state bucket, `s3:GetObject`/`s3:PutObject` on the state key, and the lock-file permissions (`s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on the `.tflock` key). Follow the book's more detailed policy guidance. The Terraform configuration already declares `use_lockfile = true`.

```bash
terraform -chdir=infrastructure/terraform init -reconfigure \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config="key=sagemaker-churn/terraform.tfstate" \
  -backend-config="region=eu-west-2" \
  -backend-config="encrypt=true"

terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform workspace show
terraform -chdir=infrastructure/terraform state list
```

**Stop if the backend already contains state you do not own.** Never initialise a new empty backend over a prior deployment and assume Terraform now owns its existing resources.

## 6. Review and deploy the supporting AWS infrastructure

The Terraform stack in [infrastructure/terraform/](infrastructure/terraform/) manages **eight resources**: one project S3 bucket, its public-access/versioning/encryption controls, two SageMaker IAM roles and two inline policies. It does **not** deploy managed SageMaker jobs, pipelines, models, endpoints, CloudWatch logs or the GitHub OIDC provider.

```bash
source scripts/setup-env.sh
aws sts get-caller-identity
terraform -chdir=infrastructure/terraform plan -out=project.tfplan
terraform -chdir=infrastructure/terraform show project.tfplan
# Only after confirming the account, Region and exact resource changes:
terraform -chdir=infrastructure/terraform apply project.tfplan

aws s3api head-bucket --bucket "$S3_BUCKET"
aws iam get-role --role-name SageMakerChurnExecutionRole
aws iam get-role --role-name SageMakerChurnPipelineRole
```

The plan file is written inside the Terraform directory; **do not commit it**. This is an intentionally small teaching configuration, not a production security blueprint. AWS identity-based permissions and organisations' guardrails must be reviewed separately; the IAM role policies in Terraform do not automatically authorise your human/CI caller to invoke SageMaker. Allow for IAM propagation and verify the actual caller and role permissions rather than blindly retrying `AccessDenied`.

## 7. Run the learning workflow

**A. Generate and upload the dataset (local; S3 upload incurs requests/storage).**

```bash
python data/create_dataset.py
head -n 3 data/customer_churn.csv
aws s3 cp data/customer_churn.csv "s3://$S3_BUCKET/raw/customer_churn.csv"
aws s3api head-object --bucket "$S3_BUCKET" --key raw/customer_churn.csv
```

You can inspect the processing implementation locally before paying for managed compute:

```bash
python processing/process.py \
  --input data/customer_churn.csv \
  --output data/processed
ls data/processed/{train,validation,test}/data.csv
```

**B. Managed processing (billable).** Confirm your **processing** quota for `ml.m5.xlarge`.

```bash
python workflow/run_processing.py
PROCESSING_JOB="$(cat workflow/latest_processing_job.txt)"
aws sagemaker describe-processing-job \
  --processing-job-name "$PROCESSING_JOB" \
  --query '{Status:ProcessingJobStatus,Failure:FailureReason}' --output json
```

The submission uses `wait=False`: **do not submit training until processing has reached `Completed`**. Check the job status again later, and verify the files:

```bash
for split in train validation test; do
  aws s3api head-object --bucket "$S3_BUCKET" \
    --key "processed/$split/data.csv" --query ContentLength --output text
done
```

**C. Managed training (billable).** Confirm your **training** quota for `ml.m5.xlarge`.

```bash
python workflow/run_training.py
TRAINING_JOB="$(cat workflow/latest_training_job.txt)"
aws sagemaker describe-training-job --training-job-name "$TRAINING_JOB" \
  --query '{Status:TrainingJobStatus,Failure:FailureReason}' --output json
```

Wait until the job reports `Completed`, then capture its actual model artefact URI for the next step:

```bash
aws sagemaker describe-training-job --training-job-name "$TRAINING_JOB" \
  --query 'ModelArtifacts.S3ModelArtifacts' --output text \
  > workflow/latest_model_artifact.txt
cat workflow/latest_model_artifact.txt
```

**D. Managed evaluation and release gate (billable).** The script reads `workflow/latest_model_artifact.txt`.

```bash
python workflow/run_evaluation.py
EVALUATION_JOB="$(cat workflow/latest_evaluation_job.txt)"
aws sagemaker describe-processing-job --processing-job-name "$EVALUATION_JOB" \
  --query '{Status:ProcessingJobStatus,Failure:FailureReason}' --output json
```

Wait for `Completed` before downloading the evidence expected by the packaging and registration scripts:

```bash
aws s3 cp "$(cat workflow/latest_evaluation_uri.txt)" evaluation/evaluation.json
python -m json.tool evaluation/evaluation.json | head -n 45
```

Review the measured metrics and `release_decision`. **A completed job does not prove acceptable model quality.** Only a passing candidate may progress to packaging and registration.

**E. Package and register only a passing release.**

```bash
python workflow/build_release_artifact.py
python workflow/register_model.py
cat workflow/latest_model_package_arn.txt
aws sagemaker describe-model-package \
  --model-package-name "$(cat workflow/latest_model_package_arn.txt)" \
  --query '{Status:ModelPackageStatus,Approval:ModelApprovalStatus}' \
  --output json
```

Registration starts in **`PendingManualApproval`**. Use Chapter 5 to inspect evidence and authorise approval explicitly. For a candidate you have independently confirmed meets the gate, the operator can approve it:

```bash
aws sagemaker update-model-package \
  --model-package-arn "$(cat workflow/latest_model_package_arn.txt)" \
  --model-approval-status Approved
aws sts get-caller-identity --query Arn --output text \
  > workflow/latest_approval_actor.txt
python workflow/write_release_record.py
```

This is a *manual governance decision*, not an instruction to approve a failing model. Deployment from the approved package, endpoint invocation, rollback, monitoring and verification are detailed in **Chapters 6 and 9**. A real-time endpoint incurs charges **until it is deleted**, even with no prediction traffic.

**F. SageMaker Pipeline and GitHub automation.** Start in **Chapter 7**:

```bash
python pipeline/build_pipeline.py
python -m json.tool pipeline/pipeline_definition.json >/dev/null
```

This builds a **local pipeline definition**; it does **not** publish or execute a pipeline. Follow Chapter 7 for creation/update, execution parameters, step inspection and release gating. The Pipeline can create multiple billable processing/training jobs per execution. GitHub's offline validation and OIDC identity-test workflows do **not** automatically run that pipeline.

## 8. Follow the repository map

Use this as the learning path; each link opens the relevant directory README. The stage number indicates **when to use it**, not a script to run automatically.

| Path | When to use it / expected outcome | AWS effect | Book chapter |
|---|---|---|
| [data/](data/) | Start: generate a reproducible CSV dataset | Local only | 4 |
| [processing/](processing/) | After data: validate and split into train/validation/test | Local or billable via workflow | 4 |
| [training/](training/) | After processing: produce model artefact | Billable managed training | 4 |
| [evaluation/](evaluation/) | After training: report metrics and release decision | Local or billable via workflow | 5 |
| [inference/](inference/) | After approved release: serving input/output contract | Used by billable endpoint | 6 |
| [workflow/](workflow/) | Orchestrate manual stages, package and register releases | Managed jobs and AWS changes | 4–5 |
| [pipeline/](pipeline/) | Build an automated definition; publish/run via book | Local build; billable when run | 7 |
| [pipeline/release_source/](pipeline/release_source/) | Supporting code bundled into the Pipeline release | Runs inside Pipeline | 7 |
| [infrastructure/terraform/](infrastructure/terraform/) | **Before managed jobs:** project bucket and IAM roles | Creates/destroys AWS infrastructure | 8 |
| [scripts/](scripts/) | **Start here:** read AWS identity; offline validation | Read-only / local | Start |

Follow the linked README for each stage's **prerequisites → inputs → command → output → verification → next step**. The top-level `inference/` file is the manual release-serving implementation; `pipeline/release_source/` contains the corresponding code packaged by the managed Pipeline. They must remain compatible with the evaluated model. Generated files, credentials, local models and Terraform state should remain **outside Git**.

## 9. How to inspect failures

Start with identity and state, not repeated submissions:

```bash
aws sts get-caller-identity
echo "$AWS_REGION $S3_BUCKET"
aws sagemaker describe-processing-job --processing-job-name "$PROCESSING_JOB"
aws sagemaker describe-training-job --training-job-name "$TRAINING_JOB"
```

- **Quota/instance errors:** check the *correct operation-specific instance quota* in `eu-west-2`. Changing the training instance in one script does not update processing, Pipeline or endpoint settings.
- **`AccessDenied` or ECR errors:** distinguish caller IAM, `iam:PassRole`, SageMaker execution-role trust and permissions, organisation explicit denies and container image access.
- **Missing S3 files:** verify the exact bucket/key and previous job's `Completed` state. A submitted job is not a successful job.
- **Pipeline failed:** inspect failed step, CloudWatch logs and IAM rights including `sagemaker:AddTags` and required S3 read access; do not automatically approve a candidate.
- **Inference failures:** check endpoint state, model package/image compatibility, `text/csv` input format, feature order and the release threshold.
- **Cost surprises:** list live endpoints, active jobs, S3 versions and monitoring schedules before troubleshooting further. See Chapter 10.

Use the SageMaker AI console for visual confirmation of Processing jobs, Training jobs, Pipelines, Model Registry, Endpoints and CloudWatch logs. Keep the Region aligned.

## 10. Cleanup: stop charges and remove only *your* project

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

For a **dedicated, verified project bucket only**, after backing up everything, use the following explicit version-aware deletion. It stops if the account or bucket does not match the expected project naming pattern; it deletes **all versions and delete markers**, not just current objects:

```bash
# Run separately, only after backup and resource ownership checks.
export CONFIRM_EMPTY_PROJECT_BUCKET="YES_DELETE_ALL_PROJECT_VERSIONS"
python - <<'PY'
import boto3, os
s = boto3.Session(region_name="eu-west-2")
account = s.client("sts").get_caller_identity()["Account"]
bucket = f"sagemaker-churn-{account}-eu-west-2"
assert os.getenv("CONFIRM_EMPTY_PROJECT_BUCKET") == "YES_DELETE_ALL_PROJECT_VERSIONS"
assert os.environ["S3_BUCKET"] == bucket
s3 = s.client("s3")
items = []
for page in s3.get_paginator("list_object_versions").paginate(Bucket=bucket):
    items += [{"Key": o["Key"], "VersionId": o["VersionId"]}
              for field in ("Versions", "DeleteMarkers")
              for o in page.get(field, [])]
print("Versions and markers selected:", len(items))
for start in range(0, len(items), 1000):
    result = s3.delete_objects(
        Bucket=bucket, Delete={"Objects": items[start:start+1000]})
    if result.get("Errors"):
        raise RuntimeError(result["Errors"])
print("Deletion requests completed; list the bucket versions again to verify")
PY
unset CONFIRM_EMPTY_PROJECT_BUCKET
aws s3api list-object-versions --bucket "$S3_BUCKET" --output json
```

This snippet is a **destructive example**, not a substitute for an independently verified backup. If the S3 inventory changes after backup, stop and assess the new objects before running it.

**C. Destroy only the Terraform-managed project stack.** From the repository root, with the **same Terraform backend, workspace and state** originally used for deployment:

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

A clean state listing should show no project resources. Verify the actual S3 bucket and IAM roles are absent with AWS CLI as well. **Do not** use `terraform destroy` against a backend whose ownership or contents you have not established.

**D. Clean remaining non-Terraform resources deliberately.** Inspect any project-specific endpoint logs, monitoring data, model records and AWS alarms. CloudWatch log groups such as **`/aws/sagemaker/TrainingJobs`** and **`/aws/sagemaker/ProcessingJobs`** are shared; **do not delete them**. The endpoint log group may hold useful evidence; retain it or remove it only after separate review. Confirm the absence of active endpoints and jobs, and check Billing/Cost Explorer for delayed charges.

**E. Keep the state backend separate.** The state bucket, its previous versions and lock history are **outside this Terraform stack**. Retain state evidence or destroy the backend only after confirming that **no other workspace, deployment or owner uses it**. Do not delete shared OIDC identity providers or GitHub roles: these are outside the SageMaker Terraform module.

## 11. Validation status and known limits

- **Validated:** original customer-churn laboratory's managed processing, training, evaluation, model registration/approval, serving, monitoring and Pipeline exercises; GitHub Actions offline CI; an identity-only GitHub OIDC authentication test.
- **Validated cleanup:** the original laboratory's SageMaker control-plane resources, versioned project S3 bucket and eight Terraform-managed resources were removed, with backup evidence preserved.
- **Not separately validated:** a clean-account **live apply of the refactored public Terraform configuration**. Its Terraform and IAM templates passed offline checks. Do not confuse that with a fresh deployment proof.
- The repository's scripts are learning assets tied to the book's workflow; some intentionally submit jobs asynchronously or require a manually inspected hand-off file and an explicit approval decision. No automated workflow here approves models or deploys endpoints.
- Always inspect current service quotas, AWS documentation, pricing and package compatibility before running billable exercises.

**Engineering discipline:** establish context → build deliberately → observe behaviour → diagnose failures → verify outcomes.  
**Release rule:** compute success ≠ model quality ≠ production health.
