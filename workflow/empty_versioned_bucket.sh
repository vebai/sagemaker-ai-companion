empty_versioned_bucket () {
  BUCKET="$1"
  EXPECTED_BUCKET="$2"

  if [ -z "$BUCKET" ] ||
     [ "$BUCKET" != "$EXPECTED_BUCKET" ]; then
    echo \
      "Refusing bucket cleanup: identity mismatch" \
      >&2
    return 1
  fi

  echo "Emptying verified bucket: $BUCKET"

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

      aws s3api delete-objects \
        --bucket "$BUCKET" \
        --delete "$DELETE_VERSIONS" \
        >/dev/null || return 1
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

      aws s3api delete-objects \
        --bucket "$BUCKET" \
        --delete "$DELETE_MARKERS" \
        >/dev/null || return 1
    fi
  done
}
