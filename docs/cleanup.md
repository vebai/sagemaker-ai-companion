# Back up and empty the versioned project bucket

> **Destructive operation.** Follow Chapter 10 and [the cleanup sequence](../README.md#10-cleanup-stop-charges-and-remove-only-your-project). Verify the AWS account, project bucket and backup before deleting versions or delete markers.

The bucket has Terraform `force_destroy = false` and **versioning enabled**. `aws s3 rm --recursive` alone is **not enough** to clear versions; it can create delete markers. Export artefacts and metadata to a separate, trusted location and verify the backup first.

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

[Continue with Terraform-managed cleanup](../README.md#10-cleanup-stop-charges-and-remove-only-your-project).
