import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import boto3

region = os.environ[
    "AWS_REGION"
]
bucket = os.environ[
    "S3_BUCKET"
]

source_files = [
    Path("data/create_dataset.py"),
    Path("processing/process.py"),
    Path("training/train.py"),
    Path("evaluation/evaluate.py"),
    Path("inference/inference.py"),
    Path("workflow/run_processing.py"),
    Path("workflow/run_training.py"),
    Path("workflow/run_evaluation.py"),
    Path(
        "workflow/"
        "build_release_artifact.py"
    ),
    Path("workflow/register_model.py"),
    Path(
        "workflow/"
        "write_release_record.py"
    ),
    Path("requirements.txt"),
]

digest = hashlib.sha256()

for path in source_files:
    path_bytes = str(path).encode(
        "utf-8"
    )

    content = path.read_bytes()

    digest.update(
        len(path_bytes).to_bytes(
            8,
            "big",
        )
    )
    digest.update(path_bytes)

    digest.update(
        len(content).to_bytes(
            8,
            "big",
        )
    )
    digest.update(content)

source_revision = (
    "sha256:"
    + digest.hexdigest()
)

training_job = Path(
    "workflow/"
    "latest_training_job.txt"
).read_text(
    encoding="utf-8"
).strip()

training_artifact = Path(
    "workflow/"
    "latest_model_artifact.txt"
).read_text(
    encoding="utf-8"
).strip()

release_artifact = Path(
    "workflow/"
    "latest_release_artifact.txt"
).read_text(
    encoding="utf-8"
).strip()

evaluation_uri = Path(
    "workflow/"
    "latest_evaluation_uri.txt"
).read_text(
    encoding="utf-8"
).strip()

model_package_arn = Path(
    "workflow/"
    "latest_model_package_arn.txt"
).read_text(
    encoding="utf-8"
).strip()

approval_caller = Path(
    "workflow/"
    "latest_approval_actor.txt"
).read_text(
    encoding="utf-8"
).strip()

evaluation = json.loads(
    Path(
        "evaluation/evaluation.json"
    ).read_text(
        encoding="utf-8"
    )
)

s3 = boto3.client(
    "s3",
    region_name=region,
)

sm = boto3.client(
    "sagemaker",
    region_name=region,
)


def split_s3(uri):
    parsed = urlparse(uri)

    if parsed.scheme != "s3":
        raise ValueError(
            f"Expected S3 URI: {uri}"
        )

    return (
        parsed.netloc,
        parsed.path.lstrip("/"),
    )


def sha256_s3(uri):
    object_bucket, key = (
        split_s3(uri)
    )

    body = s3.get_object(
        Bucket=object_bucket,
        Key=key,
    )["Body"]

    value = hashlib.sha256()

    while True:
        chunk = body.read(
            1024 * 1024
        )

        if not chunk:
            break

        value.update(chunk)

    return value.hexdigest()


package = (
    sm.describe_model_package(
        ModelPackageName=(
            model_package_arn
        )
    )
)

if (
    package["ModelPackageStatus"]
    != "Completed"
):
    raise RuntimeError(
        "Model Package is not "
        "Completed: "
        + package[
            "ModelPackageStatus"
        ]
    )

if (
    package[
        "ModelApprovalStatus"
    ]
    != "Approved"
):
    raise RuntimeError(
        "Model Package is "
        "not Approved"
    )

version = package[
    "ModelPackageVersion"
]

data_uris = {
    "training":
        f"s3://{bucket}/processed/train/data.csv",
    "validation":
        f"s3://{bucket}/processed/validation/data.csv",
    "test":
        f"s3://{bucket}/processed/test/data.csv",
}

data = {
    name: {
        "uri": uri,
        "sha256": sha256_s3(uri),
    }
    for name, uri
    in data_uris.items()
}

record_uri = (
    f"s3://{bucket}/"
    "evaluation/release-records/"
    f"model-version-{version}.json"
)

record = {
    "source_revision":
        source_revision,
    "data":
        data,
    "training_job":
        training_job,
    "training_artifact": {
        "uri":
            training_artifact,
        "sha256":
            sha256_s3(
                training_artifact
            ),
    },
    "release_artifact": {
        "uri":
            release_artifact,
        "sha256":
            sha256_s3(
                release_artifact
            ),
    },
    "evaluation": {
        "uri":
            evaluation_uri,
        "sha256":
            sha256_s3(
                evaluation_uri
            ),
        "threshold_selection":
            evaluation[
                "threshold_selection"
            ],
        "test_metrics":
            evaluation[
                "test_metrics"
            ],
        "release_requirements":
            evaluation[
                "release_requirements"
            ],
        "release_decision":
            evaluation[
                "release_decision"
            ],
    },
    "model_package": {
        "arn":
            model_package_arn,
        "version":
            version,
        "status":
            package[
                "ModelPackageStatus"
            ],
        "approval_status":
            package[
                "ModelApprovalStatus"
            ],
        "approval_description":
            package.get(
                "ApprovalDescription"
            ),
        "approval_caller_context":
            approval_caller,
    },
    "environment": {
        "target":
            "staging",
        "deployment_verified":
            False,
    },
    "release_record_uri":
        record_uri,
    "recorded_at_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),
}

payload = json.dumps(
    record,
    indent=2,
).encode("utf-8")

local = Path(
    "workflow/"
    "model_release_record.json"
)

local.write_bytes(payload)

key = (
    "evaluation/release-records/"
    f"model-version-{version}.json"
)

s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=payload,
    ContentType=(
        "application/json"
    ),
)

Path(
    "workflow/"
    "latest_release_record_uri.txt"
).write_text(
    record_uri + "\n"
)

print(record_uri)
