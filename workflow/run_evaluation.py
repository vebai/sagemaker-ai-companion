import os
from datetime import datetime, timezone
from pathlib import Path

import boto3
from sagemaker.core import image_uris
from sagemaker.core.helper.session_helper import Session
from sagemaker.core.processing import ScriptProcessor
from sagemaker.core.shapes import (
    ProcessingInput,
    ProcessingOutput,
    ProcessingS3Input,
    ProcessingS3Output,
)

region = os.environ["AWS_REGION"]
bucket = os.environ["S3_BUCKET"]
role = os.environ["SAGEMAKER_ROLE_ARN"]

model_artifact = Path(
    "workflow/latest_model_artifact.txt"
).read_text(
    encoding="utf-8"
).strip()

validation_uri = (
    f"s3://{bucket}/processed/"
    "validation/data.csv"
)

test_uri = (
    f"s3://{bucket}/processed/"
    "test/data.csv"
)

name = (
    "sagemaker-churn-evaluate-"
    f"{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
)

output_prefix = (
    f"s3://{bucket}/evaluation/{name}"
)

session = Session(
    boto_session=boto3.Session(
        region_name=region
    ),
    default_bucket=bucket,
)

image = image_uris.retrieve(
    framework="sklearn",
    region=region,
    version="1.9-0",
    image_scope="training",
    instance_type="ml.m5.xlarge",
)

processor = ScriptProcessor(
    role=role,
    image_uri=image,
    command=["python3"],
    instance_count=1,
    instance_type="ml.m5.xlarge",
    sagemaker_session=session,
)

processor.run(
    code="evaluation/evaluate.py",
    inputs=[
        ProcessingInput(
            input_name="model",
            s3_input=ProcessingS3Input(
                s3_uri=model_artifact,
                local_path=(
                    "/opt/ml/processing/model"
                ),
                s3_data_type="S3Prefix",
                s3_input_mode="File",
            ),
        ),
        ProcessingInput(
            input_name="validation",
            s3_input=ProcessingS3Input(
                s3_uri=validation_uri,
                local_path=(
                    "/opt/ml/processing/validation"
                ),
                s3_data_type="S3Prefix",
                s3_input_mode="File",
            ),
        ),
        ProcessingInput(
            input_name="test",
            s3_input=ProcessingS3Input(
                s3_uri=test_uri,
                local_path=(
                    "/opt/ml/processing/test"
                ),
                s3_data_type="S3Prefix",
                s3_input_mode="File",
            ),
        ),
    ],
    outputs=[
        ProcessingOutput(
            output_name="evaluation",
            s3_output=ProcessingS3Output(
                s3_uri=output_prefix,
                local_path=(
                    "/opt/ml/processing/output"
                ),
                s3_upload_mode="EndOfJob",
            ),
        )
    ],
    arguments=[
        "--model-artifact-uri",
        model_artifact,
        "--validation-data-uri",
        validation_uri,
        "--test-data-uri",
        test_uri,
    ],
    wait=False,
    logs=False,
    job_name=name,
)

Path(
    "workflow/latest_evaluation_job.txt"
).write_text(
    name + "\n"
)

Path(
    "workflow/latest_evaluation_uri.txt"
).write_text(
    f"{output_prefix}/evaluation.json\n"
)

print(name)
