import json
import os
import uuid
from pathlib import Path

import boto3
from sagemaker.core import image_uris

region = os.environ[
    "AWS_REGION"
]
project = os.environ[
    "PROJECT_NAME"
]

release_artifact = Path(
    "workflow/"
    "latest_release_artifact.txt"
).read_text(
    encoding="utf-8"
).strip()

release_artifact_sha256 = Path(
    "workflow/"
    "latest_release_artifact_sha256.txt"
).read_text(
    encoding="utf-8"
).strip()

training_job = Path(
    "workflow/"
    "latest_training_job.txt"
).read_text(
    encoding="utf-8"
).strip()

evaluation_uri = Path(
    "workflow/"
    "latest_evaluation_uri.txt"
).read_text(
    encoding="utf-8"
).strip()

evidence = json.loads(
    Path(
        "evaluation/evaluation.json"
    ).read_text(
        encoding="utf-8"
    )
)

if (
    evidence["release_decision"]
    != "pass"
):
    raise RuntimeError(
        "Only a passing candidate "
        "can be registered"
    )

threshold = (
    evidence[
        "threshold_selection"
    ][
        "selected_decision_threshold"
    ]
)

if threshold is None:
    raise RuntimeError(
        "Passing candidate has "
        "no decision threshold"
    )

sm = boto3.client(
    "sagemaker",
    region_name=region,
)

exists = False

paginator = sm.get_paginator(
    "list_model_package_groups"
)

for page in paginator.paginate(
    NameContains=project
):
    if any(
        item[
            "ModelPackageGroupName"
        ] == project
        for item in page[
            "ModelPackageGroupSummaryList"
        ]
    ):
        exists = True
        break

if not exists:
    sm.create_model_package_group(
        ModelPackageGroupName=project,
        ModelPackageGroupDescription=(
            "Customer-churn "
            "release versions"
        ),
    )

inference_image = (
    image_uris.retrieve(
        framework="sklearn",
        region=region,
        version="1.9-0",
        image_scope="inference",
        instance_type="ml.m5.large",
    )
)

token = str(
    uuid.uuid5(
        uuid.NAMESPACE_URL,
        (
            f"{release_artifact}"
            f"|{evaluation_uri}"
        ),
    )
)


# Check Registry identity before attempting creation.
# This also handles retries after approval state has changed.
paginator = sm.get_paginator("list_model_packages")

for page in paginator.paginate(
    ModelPackageGroupName=project,
):
    for summary in page["ModelPackageSummaryList"]:
        existing_arn = summary["ModelPackageArn"]
        existing = sm.describe_model_package(
            ModelPackageName=existing_arn
        )

        containers = existing.get(
            "InferenceSpecification", {}
        ).get("Containers", [])

        if not containers:
            continue

        existing_uri = containers[0].get("ModelDataUrl")

        if existing_uri != release_artifact:
            continue

        metadata = existing.get(
            "CustomerMetadataProperties", {}
        )

        quality_uri = (
            existing.get("ModelMetrics", {})
            .get("ModelQuality", {})
            .get("Statistics", {})
            .get("S3Uri")
        )

        if not (
            metadata.get("release_artifact_sha256")
            == release_artifact_sha256
            and metadata.get("decision_threshold")
            == str(threshold)
            and metadata.get("training_job")
            == training_job
            and metadata.get("release_decision")
            == "pass"
            and quality_uri == evaluation_uri
            and containers[0].get("Image")
            == inference_image
        ):
            raise RuntimeError(
                "Existing release artefact has "
                "conflicting Registry metadata"
            )

        if existing.get("ModelPackageStatus") != "Completed":
            raise RuntimeError(
                "Existing model package is not Completed"
            )

        Path(
            "workflow/latest_model_package_arn.txt"
        ).write_text(existing_arn + "\n")

        Path(
            "workflow/latest_inference_image.txt"
        ).write_text(inference_image + "\n")

        print(
            "Existing registered release found:",
            existing_arn
        )

        raise SystemExit(0)

response = sm.create_model_package(
    ModelPackageGroupName=project,
    ModelPackageDescription=(
        "Customer-churn release "
        "candidate that passed "
        "the held-out release gate"
    ),
    ModelApprovalStatus=(
        "PendingManualApproval"
    ),
    ClientToken=token,
    InferenceSpecification={
        "Containers": [{
            "Image":
                inference_image,
            "ModelDataUrl":
                release_artifact,
            "Environment": {
                "SAGEMAKER_PROGRAM":
                    "inference.py",
                "SAGEMAKER_SUBMIT_DIRECTORY":
                    "/opt/ml/model/code",
            },
        }],
        "SupportedContentTypes": [
            "text/csv"
        ],
        "SupportedResponseMIMETypes": [
            "application/json"
        ],
        "SupportedRealtimeInferenceInstanceTypes": [
            "ml.m5.large"
        ],
    },
    ModelMetrics={
        "ModelQuality": {
            "Statistics": {
                "ContentType":
                    "application/json",
                "S3Uri":
                    evaluation_uri,
            }
        }
    },
    CustomerMetadataProperties={
        "release_decision":
            "pass",
        "target_environment":
            "staging",
        "decision_threshold":
            str(threshold),
        "release_artifact_sha256":
            release_artifact_sha256,
        "training_job":
            training_job,
    },
)

package_arn = response[
    "ModelPackageArn"
]

Path(
    "workflow/"
    "latest_model_package_arn.txt"
).write_text(
    package_arn + "\n"
)

Path(
    "workflow/"
    "latest_inference_image.txt"
).write_text(
    inference_image + "\n"
)

print(package_arn)
