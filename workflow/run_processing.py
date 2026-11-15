import os
from datetime import datetime, timezone
from pathlib import Path
import boto3
from sagemaker.core import image_uris
from sagemaker.core.helper.session_helper import Session
from sagemaker.core.processing import ScriptProcessor
from sagemaker.core.shapes import (
    ProcessingInput, ProcessingOutput,
    ProcessingS3Input, ProcessingS3Output,
)

region = os.environ["AWS_REGION"]
bucket = os.environ["S3_BUCKET"]
role = os.environ["SAGEMAKER_ROLE_ARN"]

session = Session(
    boto_session=boto3.Session(region_name=region),
    default_bucket=bucket,
)

image = image_uris.retrieve(
    framework="sklearn",
    region=region,
    version="1.9-0",
    image_scope="training",
    instance_type="ml.m5.xlarge",
)

name = f"sagemaker-churn-process-{datetime.now(timezone.utc):%Y%m%d%H%M%S}"

processor = ScriptProcessor(
    role=role,
    image_uri=image,
    command=["python3"],
    instance_count=1,
    instance_type="ml.m5.xlarge",
    sagemaker_session=session,
)

processor.run(
    code="processing/process.py",
    inputs=[ProcessingInput(
        input_name="raw",
        s3_input=ProcessingS3Input(
            s3_uri=f"s3://{bucket}/raw/customer_churn.csv",
            local_path="/opt/ml/processing/input",
            s3_data_type="S3Prefix",
            s3_input_mode="File",
        ),
    )],
    outputs=[ProcessingOutput(
        output_name="processed",
        s3_output=ProcessingS3Output(
            s3_uri=f"s3://{bucket}/processed/",
            local_path="/opt/ml/processing/output",
            s3_upload_mode="EndOfJob",
        ),
    )],
    wait=False,
    logs=False,
    job_name=name,
)

Path("workflow/latest_processing_job.txt").write_text(name + "\n")
print(name)
