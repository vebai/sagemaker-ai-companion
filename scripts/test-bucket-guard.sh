#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source workflow/empty_versioned_bucket.sh

# AWS calls are mocked: this test cannot access or change AWS resources.
aws () {
  if [ "$1" = "sts" ] && [ "$2" = "get-caller-identity" ]; then
    printf "123456789012\n"
  elif [ "$1" = "s3api" ] && [ "$2" = "list-object-versions" ]; then
    printf "0\n"
  else
    echo "Unexpected AWS call in cleanup guard test: $*" >&2
    return 99
  fi
}

BUCKET="sagemaker-churn-123456789012-eu-west-2"
export S3_BUCKET="$BUCKET" AWS_REGION="eu-west-2"
unset CONFIRM_EMPTY_PROJECT_BUCKET || true

if empty_versioned_bucket "$BUCKET" "$BUCKET" >/dev/null 2>&1; then
  echo "FAIL: confirmation guard" >&2; exit 1
fi
export CONFIRM_EMPTY_PROJECT_BUCKET="YES_DELETE_ALL_PROJECT_VERSIONS"
if empty_versioned_bucket "other-bucket" "other-bucket" >/dev/null 2>&1; then
  echo "FAIL: bucket identity guard" >&2; exit 1
fi
if empty_versioned_bucket "$BUCKET" "other-bucket" >/dev/null 2>&1; then
  echo "FAIL: expected bucket guard" >&2; exit 1
fi
export AWS_REGION="eu-west-1"
if empty_versioned_bucket "$BUCKET" "$BUCKET" >/dev/null 2>&1; then
  echo "FAIL: Region guard" >&2; exit 1
fi
export AWS_REGION="eu-west-2" S3_BUCKET="other-bucket"
if empty_versioned_bucket "$BUCKET" "$BUCKET" >/dev/null 2>&1; then
  echo "FAIL: environment bucket guard" >&2; exit 1
fi
export S3_BUCKET="$BUCKET"
empty_versioned_bucket "$BUCKET" "$BUCKET" >/dev/null
unset CONFIRM_EMPTY_PROJECT_BUCKET
echo "PASS: versioned bucket cleanup refuses unapproved or mismatched targets"
