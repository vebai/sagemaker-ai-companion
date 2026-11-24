empty_versioned_bucket () {
  if [ "$#" -ne 2 ]; then
    echo "Usage: empty_versioned_bucket BUCKET EXPECTED_BUCKET" >&2
    return 1
  fi
  local BUCKET="$1" EXPECTED_BUCKET="$2" ACCOUNT VERIFIED_BUCKET REGION

  if [ "${CONFIRM_EMPTY_PROJECT_BUCKET:-}" != "YES_DELETE_ALL_PROJECT_VERSIONS" ]; then
    echo "Refusing bucket cleanup: explicit confirmation required" >&2
    return 1
  fi
  REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-}}"
  if [ "$REGION" != "eu-west-2" ]; then
    echo "Refusing bucket cleanup: AWS_REGION must be eu-west-2" >&2
    return 1
  fi
  ACCOUNT=$(aws sts get-caller-identity --query Account --output text) || return 1
  VERIFIED_BUCKET="sagemaker-churn-${ACCOUNT}-eu-west-2"
  if [ -z "$BUCKET" ] || [ "$BUCKET" != "$VERIFIED_BUCKET" ] ||
     [ "$EXPECTED_BUCKET" != "$VERIFIED_BUCKET" ] ||
     [ "${S3_BUCKET:-}" != "$VERIFIED_BUCKET" ]; then
    echo "Refusing bucket cleanup: account, bucket or environment mismatch" >&2
    return 1
  fi

  echo "Deleting every version and marker in the independently verified lab bucket: $BUCKET"

  while true; do
    VERSION_COUNT=$(aws s3api \
      list-object-versions \
      --bucket "$BUCKET" \
      --max-items 1000 \
      --query 'length(Versions || `[]`)' \
      --output text) || return 1

    MARKER_COUNT=$(aws s3api \
      list-object-versions \
      --bucket "$BUCKET" \
      --max-items 1000 \
      --query 'length(DeleteMarkers || `[]`)' \
      --output text) || return 1

    if [ "$VERSION_COUNT" = "0" ] &&
       [ "$MARKER_COUNT" = "0" ]; then
      echo "Verified empty bucket: $BUCKET"
      return 0
    fi

    if [ "$VERSION_COUNT" != "0" ]; then
      DELETE_VERSIONS=$(aws s3api \
        list-object-versions \
        --bucket "$BUCKET" \
        --max-items 1000 \
        --output json \
        --query \
'{Objects: Versions[].{Key:Key,VersionId:VersionId},Quiet:`true`}') \
        || return 1

      DELETE_ERRORS=$(aws s3api delete-objects \
        --bucket "$BUCKET" \
        --delete "$DELETE_VERSIONS" \
        --query 'length(Errors || `[]`)' --output text) || return 1
      if [ "$DELETE_ERRORS" != "0" ]; then
        echo "Refusing to continue: AWS reported object-level deletion errors" >&2
        return 1
      fi
    fi

    if [ "$MARKER_COUNT" != "0" ]; then
      DELETE_MARKERS=$(aws s3api \
        list-object-versions \
        --bucket "$BUCKET" \
        --max-items 1000 \
        --output json \
        --query \
'{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId},Quiet:`true`}') \
        || return 1

      DELETE_ERRORS=$(aws s3api delete-objects \
        --bucket "$BUCKET" \
        --delete "$DELETE_MARKERS" \
        --query 'length(Errors || `[]`)' --output text) || return 1
      if [ "$DELETE_ERRORS" != "0" ]; then
        echo "Refusing to continue: AWS reported object-level deletion errors" >&2
        return 1
      fi
    fi
  done
}
