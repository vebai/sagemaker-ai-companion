import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import boto3

region = os.environ["AWS_REGION"]
bucket = os.environ["S3_BUCKET"]

request = Path(
    "inference/request.csv"
).read_bytes()

hosted = json.loads(
    Path(
        "inference/response.json"
    ).read_text(
        encoding="utf-8"
    )
)

local = json.loads(
    Path(
        "inference/"
        "local-approved-response.json"
    ).read_text(
        encoding="utf-8"
    )
)

verified_at = datetime.now(
    timezone.utc
)

timestamp = verified_at.strftime(
    "%Y%m%dT%H%M%SZ"
)

record = {
    "model_release_record_uri":
        os.environ["RELEASE_RECORD_URI"],
    "model_package_arn":
        os.environ["MODEL_PACKAGE_ARN"],
    "sagemaker_model": {
        "name":
            os.environ["MODEL_NAME"],
        "arn":
            os.environ["MODEL_ARN"],
    },
    "endpoint_configuration": {
        "name":
            os.environ[
                "ENDPOINT_CONFIG_NAME"
            ],
        "arn":
            os.environ[
                "ENDPOINT_CONFIG_ARN"
            ],
    },
    "endpoint": {
        "name":
            os.environ["ENDPOINT_NAME"],
        "arn":
            os.environ["ENDPOINT_ARN"],
        "observed_status":
            "InService",
    },
    "request": {
        "content_type":
            "text/csv",
        "sha256":
            hashlib.sha256(
                request
            ).hexdigest(),
        "value":
            request.decode(
                "utf-8"
            ).strip(),
    },
    "response": {
        "content_type":
            "application/json",
        "approved_release_execution":
            local,
        "hosted_execution":
            hosted,
    },
    "verification": {
        "same_prediction":
            local[0]["prediction"]
            == hosted[0]["prediction"],
        "probability_tolerance":
            {
                "relative": 1e-9,
                "absolute": 1e-12,
            },
        "approved_threshold":
            float(
                os.environ[
                    "APPROVED_THRESHOLD"
                ]
            ),
        "verified_at_utc":
            verified_at.isoformat(),
    },
}

key = (
    "deployments/"
    f"{os.environ['ENDPOINT_NAME']}/"
    f"verifications/{timestamp}.json"
)

uri = (
    f"s3://{bucket}/{key}"
)

payload = json.dumps(
    record,
    indent=2,
).encode("utf-8")

local_path = Path(
    "workflow/deployments/"
    f"{timestamp}.json"
)

local_path.write_bytes(payload)

s3 = boto3.client(
    "s3",
    region_name=region,
)

s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=payload,
    ContentType="application/json",
)

Path(
    "workflow/"
    "latest_deployment_verification_uri.txt"
).write_text(
    uri + "
"
)

print(uri)
