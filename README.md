# Deploying Machine Learning with Amazon SageMaker AI

[![Validate companion code](https://github.com/vebai/sagemaker-ai-companion/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/vebai/sagemaker-ai-companion/actions/workflows/validate.yml)

This is the companion repository for *Deploying Machine Learning with Amazon SageMaker AI: Training, Deployment, Automation, and Production Operations on AWS* by **Victor Ebai**. It contains the Python scripts, Terraform configuration and IAM templates for the book’s customer-churn workload. The book is self-contained, and these files let you run and inspect the exercises.

## Get the paperback

**[Amazon UK — Paperback](https://www.amazon.co.uk/dp/B0HS2PZHN9)** · [Amazon US](https://www.amazon.com/dp/B0HS2PZHN9) · [Amazon India (availability may vary)](https://www.amazon.in/dp/B0HS2PZHN9)

**Quick navigation:** [Before you begin](#before-you-begin) · [Getting started](#getting-started) · [Chapter guide](#chapter-guide) · [Validation](#verify-the-repository-files) · [Cleanup](#cleaning-up)

![Seven-stage SageMaker AI learning journey from understanding a machine-learning problem to building, deploying, automating, observing, diagnosing and recovering a model service; includes distinctions between training jobs, model artefacts, endpoints, model quality, production health and business outcomes.](docs/images/sagemaker-ai-overview.png)

*Follow one workload from data preparation and training through model release, deployment, monitoring and recovery.*

## What you will build and practise

- Prepare customer-churn data, run managed processing and training jobs, and evaluate the model against a release gate.
- Register and approve a model version, deploy it for real-time inference, and verify the request-to-prediction path.
- Build a SageMaker Pipeline and inspect a GitHub Actions release example.
- Review infrastructure ownership with Terraform, monitor service and model health, and verify recovery after a failure.

## Before you begin

- **Python 3.11 and Git** for local work. Install Python packages from the pinned [requirements file](requirements.txt).
- **Terraform 1.10 or later** for repository validation and Chapter 8. Install **AWS CLI v2** for live exercises. See the [workstation setup guide](docs/setup.md#2-install-tools-on-your-workstation).
- **An authorised AWS learning account** for managed jobs. Use temporary credentials and check the account, Region, instance availability and quotas. The examples use London (`eu-west-2`). See [AWS prerequisites](docs/setup.md#1-before-creating-anything-in-aws).

> [!WARNING]
> SageMaker jobs, idle endpoints, S3 and CloudWatch can incur charges. Start with local validation. Review ownership and Terraform state before adopting existing infrastructure, and follow the cleanup guide when finished.

## Getting started

<a id="3-clone-configure-python-and-verify-identity"></a>

1. **Clone the examples and create the Python environment.** Run commands from the repository root after cloning.

   ```bash
   git clone https://github.com/vebai/sagemaker-ai-companion.git sagemaker-churn
   cd sagemaker-churn
   python3.11 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

2. **Run the [repository checks](#verify-the-repository-files).** You can also [generate the dataset](data/README.md) locally before signing in to AWS.
3. **Verify your AWS identity before live work.** Sign in with your authorised profile or temporary credentials. For an IAM Identity Center profile, run `aws sso login --profile <your-profile>` and set `AWS_PROFILE` to that profile. Run `aws sts get-caller-identity`, then `source scripts/setup-env.sh` and confirm `AWS_REGION`, `S3_BUCKET` and `SAGEMAKER_ROLE_ARN`. The script reads the account and sets shell variables. Verify the execution role separately. In a new shell, reactivate `.venv` and source the script again.
4. **Follow the [learning workflow](docs/learning-workflow.md#7-run-the-learning-workflow).** Set up the [project bucket and role in Chapter 4](docs/learning-workflow.md#5-set-up-aws-infrastructure-in-the-books-order). In Chapter 8, [review ownership, state and the plan](docs/learning-workflow.md#6-verify-the-chapter-8-configuration-before-changes) before adopting those resources with Terraform.

## Chapter guide

<a id="find-the-code-for-each-book-chapter"></a>

Chapters 1–3 introduce the problem, SageMaker services and AWS architecture. The runnable exercises begin in Chapter 4.

| Chapter | Exercise | Files and instructions |
|---|---|---|
| 4 | Prepare data and run managed jobs | [Data](data/README.md) · [Processing](processing/README.md) · [Training](training/README.md) · [Job submission](workflow/README.md) |
| 5 | Evaluate, package, register and approve a model | [Evaluation](evaluation/README.md) · [Release and registry](workflow/README.md) |
| 6 | Deploy an approved model and verify inference | [Inference guide](inference/README.md) · [Verification record](workflow/write_deployment_verification.py) |
| 7 | Build a pipeline and review release automation | [Pipeline and IAM](pipeline/README.md) · [Release source](pipeline/release_source/README.md) · [GitHub Actions example](examples/chapter-07/ml-release.yml) |
| 8 | Review and adopt AWS infrastructure | [Canonical Terraform](infrastructure/terraform/README.md) · [Book OIDC example](examples/chapter-08/book-main.tf) |
| 9 | Examine captured requests and model inputs | [Monitoring](monitoring/README.md) |
| 10 | Diagnose failures, verify recovery and control costs | [Troubleshooting](#troubleshooting) · [Cleanup](#cleaning-up) |

The [repository map](docs/learning-workflow.md#8-follow-the-repository-map) shows where each stage’s source and instructions live.

## Verify the repository files

```bash
bash scripts/validate.sh
```

[GitHub Actions](.github/workflows/validate.yml) runs on pushes and pull requests. It checks the companion source and templates, validates Terraform without a backend, and tests the Chapter 8 plan guard. Terraform may download providers during validation. Live account permissions, managed jobs, model quality and endpoint health require separate checks. A clean-account live apply of the Chapter 8 stack remains unverified.

The Chapter 7 release workflow is an inactive example. The separate [OIDC identity test](.github/workflows/oidc-identity.yml) targets the author’s AWS account. For your exercises, verify each managed job’s status and expected artefacts before advancing, and use the book’s explicit approval and deployment steps.

## Troubleshooting

Check the AWS identity, Region and first failed step before resubmitting a job. Use the [diagnostic guide](docs/learning-workflow.md#9-how-to-inspect-failures) to check quotas, IAM, S3 paths, model approval and endpoint health.

## Cleaning up

> [!WARNING]
> Stop billable jobs and endpoints, preserve evidence, and confirm resource ownership before deleting anything. Protect shared resources such as OIDC providers, CloudWatch log groups and Terraform state.

Follow the [cleanup and versioned S3 procedure](docs/cleanup.md) in Chapter 10’s order, then verify what remains.

## Continue with AWS Cloud Engineering

*AWS Cloud Engineering in 10 Days* gives you more practice with the IAM, EC2, networking and monitoring used in AWS workloads.

**[Amazon UK — Paperback](https://www.amazon.co.uk/dp/B0HR7NQM3R)** · [Companion labs](https://github.com/vebai/aws-cloud-engineering-in-10-days)

## Licence

The reusable code is available under the [MIT License](LICENSE). Book text and the overview illustration are © 2026 Victor Ebai.
