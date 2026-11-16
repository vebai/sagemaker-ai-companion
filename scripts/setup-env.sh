#!/usr/bin/env bash

# Source this file from the repository root:
# source scripts/setup-env.sh

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI is required." >&2
  return 1 2>/dev/null || exit 1
fi

export AWS_REGION="eu-west-2"
export AWS_DEFAULT_REGION="$AWS_REGION"
export PROJECT_NAME="sagemaker-churn"

export ACCOUNT_ID
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)" || {
  echo "Unable to verify AWS identity." >&2
  return 1 2>/dev/null || exit 1
}

if [[ ! "$ACCOUNT_ID" =~ ^[0-9]{12}$ ]]; then
  echo "AWS identity returned an invalid account ID." >&2
  return 1 2>/dev/null || exit 1
fi
export S3_BUCKET="${PROJECT_NAME}-${ACCOUNT_ID}-${AWS_REGION}"
export SAGEMAKER_ROLE_NAME="SageMakerChurnExecutionRole"
export SAGEMAKER_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${SAGEMAKER_ROLE_NAME}"

echo "AWS account: $ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "Project: $PROJECT_NAME"
echo "Project bucket: $S3_BUCKET"
echo "SageMaker role name: $SAGEMAKER_ROLE_NAME"
echo "SageMaker workload role: $SAGEMAKER_ROLE_ARN"
echo "Environment configured. No AWS resources modified."
