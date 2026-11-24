# Deploying Machine Learning with Amazon SageMaker AI

This is the companion repository for *Deploying Machine Learning with Amazon SageMaker AI: Training, Deployment, Automation, and Production Operations on AWS* by **Victor Ebai**. It provides the customer-churn example, Python scripts, Terraform configurations, IAM templates and practical verification guidance.

**The book is fully self-contained.** Its explanations, commands, technical decisions and core examples do not require this repository. These files provide convenient, testable copies for readers who prefer to clone and run the exercises.

## Get the book

**[Amazon UK — book page](https://www.amazon.co.uk/dp/B0HS2PZHN9)** (default) · [Amazon US](https://www.amazon.com/dp/B0HS2PZHN9) · [Amazon India (availability may vary)](https://www.amazon.in/dp/B0HS2PZHN9)

**Quick navigation:** [Chapter files](#find-the-code-for-each-book-chapter) · [Before AWS](#before-you-begin) · [Getting started](#3-clone-configure-python-and-verify-identity) · [Workflow](#7-run-the-learning-workflow) · [Troubleshooting](#9-how-to-inspect-failures) · [Cleanup](#10-cleanup-stop-charges-and-remove-only-your-project)

The learning journey moves from a defined ML problem through training, model release, deployment, automation, monitoring and evidence-based recovery.

![Seven-stage SageMaker AI learning journey from understanding a machine-learning problem to building, deploying, automating, observing, diagnosing and recovering a model service; includes distinctions between training jobs, model artefacts, endpoints, model quality, production health and business outcomes.](docs/images/sagemaker-ai-overview.png)

*Learning overview: a completed training job is not the same as a model artefact, a deployed endpoint or a reliable business outcome. Check evidence and acceptance criteria at every transition.*

The practical method is **Understand → Build → Deploy → Automate → Observe → Diagnose → Recover → Verify**. Use the book to understand the decisions; use the repository for reproducible code and lab evidence.

## What you will build and practise

- Prepare and split customer-churn data for repeatable machine-learning experiments.
- Run managed processing and training jobs, evaluate results and apply a release gate.
- Register an approved model version and deploy an endpoint deliberately when ready.
- Build a SageMaker Pipeline and inspect the supplied, inactive CI/CD workflow.
- Track service and model health, investigate failures and verify recovery.
- Review account-specific AWS identities, infrastructure ownership, costs and safe cleanup.

## Before you begin

**First-time setup:** Check the [AWS prerequisites and cost guidance](docs/setup.md#1-before-creating-anything-in-aws), [install tools](docs/setup.md#2-install-tools-on-your-workstation), then [clone and verify your identity](#3-clone-configure-python-and-verify-identity).

You need Python **3.11**, Git, AWS CLI v2, Terraform for the infrastructure chapter, and an authorised AWS account for managed jobs. The examples use **AWS London (`eu-west-2`)**, but instance availability and quotas must be verified for the specific operation and instance type.

**Costs and security:** SageMaker jobs, endpoints (including idle endpoints), S3 and CloudWatch can incur charges. Use a dedicated learning account, temporary credentials, quotas and budgets. Do not run Terraform against existing resources until ownership and imports are understood. Start with offline validation; no script silently deploys an inference endpoint.

## Find the code for each book chapter

Use this chapter index to open the relevant **source file or directory README**. Chapters 1–3 establish the concepts and architecture, so they have no separate executable code. Chapters 9–10 extend the same workload, with Chapter 9 monitoring source and Chapter 10 cleanup guidance.

| Book chapter | Companion source and instructions | What you will use |
|---|---|---|
| **1 — Understanding the Machine-Learning Problem** | No standalone code — start with [the data contract and dataset generator](data/README.md) when you reach Chapter 4 | Define the classification problem, features and labels |
| **2 — Understanding Amazon SageMaker AI** | No standalone code — see the [managed-workflow guide](workflow/README.md) for the later practical implementation | Understand processing, training, model packages and endpoints |
| **3 — AWS Architecture for SageMaker** | No standalone code — see [infrastructure source](infrastructure/terraform/README.md) when you reach Chapter 8 | Understand the AWS service, identity and storage boundaries |
| **4 — Preparing Data and Running Training Jobs** | [Dataset](data/README.md) · [Processing](processing/README.md) · [Training](training/README.md) · [Job submission scripts](workflow/README.md) | Generate data, submit managed processing and training, verify artefacts |
| **5 — Evaluating, Registering and Governing Models** | [Evaluation script](evaluation/evaluate.py) · [Evaluation guide](evaluation/README.md) · [Release and registry scripts](workflow/README.md) | Measure model quality, package a passing candidate, register and approve |
| **6 — Deploying Models for Inference** | [Inference handler](inference/inference.py) · [Inference guide](inference/README.md) · [Deployment verification record](workflow/write_deployment_verification.py) | Verify the approved model's real-time prediction path |
| **7 — SageMaker Pipelines and Release Automation** | [Pipeline builder](pipeline/build_pipeline.py) · [Pipeline IAM templates](pipeline/README.md) · [GitHub IAM templates](workflow/README.md) · [Release-packaging source](pipeline/release_source/README.md) · [GitHub release workflow](examples/chapter-07/ml-release.yml) | Build and inspect the Pipeline; review the inactive CI/CD delivery example |
| **8 — Production Security and Infrastructure as Code** | [Canonical Terraform configuration](infrastructure/terraform/README.md) · [Terraform source files](infrastructure/terraform/main.tf) · [Book-version OIDC example](examples/chapter-08/book-main.tf) | Review identity and infrastructure ownership; import existing resources safely |
| **9 — Observing SageMaker and Model Health** | [Monitoring guide](monitoring/README.md) · [Capture template](monitoring/data-capture.json.template) · [Input comparison script](monitoring/compare_input.py) · [Inference handler](inference/inference.py) | Inspect captured requests, compare input distributions and interpret health evidence |
| **10 — Troubleshooting, Recovery and Cost Control** | [Troubleshooting guide](#9-how-to-inspect-failures) · [Cleanup instructions](#10-cleanup-stop-charges-and-remove-only-your-project) · [Versioned S3 cleanup helper](workflow/empty_versioned_bucket.sh) | Diagnose failures, preserve evidence and clean up project-owned resources |

**Start here:** [Install and clone](#3-clone-configure-python-and-verify-identity) → [check prerequisites](#1-before-creating-anything-in-aws) → follow the book's chapters in order. All relative links above open files in this repository. The Chapter 7 release workflow is a reference under `examples/`, not an automatically running GitHub Action.

## Read this first — what runs where?

| Action | Where | AWS cost or change? | Success evidence |
|---|---|---|---|
| Clone and install Python packages | Local Mac/Linux | No AWS changes | Virtual environment, installed dependencies |
| Generate data; run local processing | Local Mac/Linux | No AWS changes | CSV dataset and split files |
| Run `scripts/validate.sh` | Local Mac/Linux | No AWS changes | Offline source/Terraform checks pass |
| Run `scripts/setup-env.sh` | Local shell, reads AWS STS | Read-only AWS call | Correct AWS account, Region and bucket name |
| Chapter 4 manual infrastructure setup; Chapter 8 Terraform adoption | Local shell → AWS | **Creates or adopts infrastructure** | Verified bucket and IAM roles; reviewed Terraform state |
| Submit processing, training or evaluation | Local shell → SageMaker | **Billable managed jobs** | Job reaches `Completed`, outputs exist |
| Register/approve a model | Local shell → SageMaker | **Changes registry state** | Correct package and approval evidence |
| Deploy an endpoint (book Chapter 6) | AWS | **Billable while running, even when idle** | Inference request verified |
| Clean up (book Chapter 10) | AWS | **Destructive** | Resources absent; evidence retained |

**Do not run the next stage merely because the previous command exited successfully.** For SageMaker jobs, verify the managed job status and expected artefacts first.

## Workflow and environment

Use **Python 3.11**, AWS Region `eu-west-2`, pinned dependencies in [requirements.txt](requirements.txt), and Terraform 1.10 or later. Check the relevant SageMaker quotas for the `ml.m5.xlarge` processing/training and `ml.m5.large` endpoint examples. The [learning workflow guide](docs/learning-workflow.md) contains the detailed commands.

## 1. Before creating anything in AWS

Use an authorised learning account, verify your identity and Region, confirm SageMaker instance quotas, and understand the costs of managed jobs and idle endpoints. Prefer temporary credentials and avoid shared infrastructure.

Read the [account, IAM, quotas and safety prerequisites](docs/setup.md#1-before-creating-anything-in-aws) before creating resources.

## 2. Install tools on your workstation

Follow the [macOS and Linux installation instructions](docs/setup.md#2-install-tools-on-your-workstation) for Python 3.11, Git, AWS CLI v2 and Terraform. Verify each tool before continuing.

## 3. Clone, configure Python, and verify identity

Run commands from the **repository root** unless a section says otherwise. Open a new terminal and source the virtual environment again each time.

```bash
git clone https://github.com/vebai/sagemaker-ai-companion.git sagemaker-churn
cd sagemaker-churn
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
chmod +x ./scripts/validate.sh
./scripts/validate.sh
```

**What this quick check proves:** Python source parses, dependencies are pinned and the book's canonical Terraform configuration validates offline. Archived source is checked separately by the validation tooling. **What it does not prove:** permissions in your account, resource creation, completed jobs, model quality or endpoint health.

This checks Python syntax, pinned dependencies, legacy IAM policy templates and the Terraform configurations. It performs no AWS deployment. The script downloads Terraform providers for offline validation; **it does not deploy SageMaker resources**. GitHub's [Validate companion code](.github/workflows/validate.yml) runs similar checks on pushes. The separate [OIDC identity test](.github/workflows/oidc-identity.yml) is for the author's AWS account only; it is **not** a reader deployment workflow and does not grant a reader permissions.

## 5. Set up AWS infrastructure in the book's order

**Chapter 4 first:** establish the project S3 bucket and execution role, then verify identity, trust and `iam:PassRole`. **Chapter 8 later:** review ownership and import existing resources before adopting Terraform.

[Detailed infrastructure setup](docs/learning-workflow.md#5-set-up-aws-infrastructure-in-the-books-order) · [Canonical Terraform guide](infrastructure/terraform/README.md)

## 6. Verify the Chapter 8 configuration before changes

Validate the Terraform source offline, then review the exact account, workspace, state and proposed plan. The shared GitHub OIDC provider is a data source, not a Terraform-owned resource.

[Safe configuration and plan review steps](docs/learning-workflow.md#6-verify-the-chapter-8-configuration-before-changes)

## 7. Run the learning workflow

Follow the book's sequence: **data → processing → training → evaluation → release gate → approval → inference → monitoring**. Managed SageMaker jobs are billable. A submitted job is **not** proof of successful completion; verify each hand-off before continuing.

[Commands and verification checkpoints](docs/learning-workflow.md#7-run-the-learning-workflow) · [Managed workflow guide](workflow/README.md)

## 8. Follow the repository map

Use the [chapter index above](#find-the-code-for-each-book-chapter) or the [directory-by-directory workflow map](docs/learning-workflow.md#8-follow-the-repository-map). Each folder contains its own prerequisites, commands and verification guidance.

## 9. How to inspect failures

Check the AWS identity and the first failed boundary before resubmitting jobs. Investigate quotas, IAM, S3 paths, model approval and endpoint health separately.

[Diagnostic commands and failure boundaries](docs/learning-workflow.md#9-how-to-inspect-failures)

## 10. Cleanup: stop charges and remove only *your* project

> **Destructive operations require explicit approval.** First stop billable endpoints and jobs; then back up your S3 data, verify account and bucket ownership, remove project-owned resources in dependency order, and confirm what remains. Never delete shared OIDC identity providers, shared CloudWatch log groups or an unverified Terraform state backend.

Use the [full cleanup and versioned-S3 procedure](docs/cleanup.md) in conjunction with Chapter 10. Nothing in this repository automatically deletes AWS resources.

## 11. Validation scope and known limits

- **Offline CI:** checks Python syntax, templates, IAM source, Terraform configurations and safety boundaries. It does not create AWS resources.
- **Managed workflow:** processing, training, evaluation, registration, serving and pipeline exercises have been exercised, but must be verified again for each reader's account, identity and available quotas.
- **Important limit:** a clean-account, live deployment of the canonical Chapter 8 Terraform stack has **not** been independently established. Offline validation is not a live apply.
- No automated workflow here approves model quality, deploys an endpoint or performs destructive cleanup. Follow the book's approval and evidence checkpoints.

**Engineering discipline:** establish context → build deliberately → observe behaviour → diagnose failures → verify outcomes.  
**Release rule:** compute success ≠ model quality ≠ production health.

## Continue with the book

The **[Amazon UK book page](https://www.amazon.co.uk/dp/B0HS2PZHN9)** provides the complete explanations, release decisions and operational troubleshooting exercises. For readers strengthening their AWS foundation, [AWS Cloud Engineering in 10 Days](https://github.com/vebai/aws-cloud-engineering-in-10-days) covers account context, IAM, EC2, networking and evidence-based verification.

The reusable code is covered by the [MIT License](LICENSE); book text and this overview illustration remain © 2026 Victor Ebai.

