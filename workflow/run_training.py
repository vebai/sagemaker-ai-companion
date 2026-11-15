import os
from pathlib import Path
import boto3
from sagemaker.core import image_uris
from sagemaker.core.helper.session_helper import Session
from sagemaker.core.training.configs import (
    Compute, InputData, OutputDataConfig, SourceCode,
)
from sagemaker.train import ModelTrainer

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

trainer = ModelTrainer(
    training_image=image,
    role=role,
    sagemaker_session=session,
    base_job_name="sagemaker-churn-train",
    source_code=SourceCode(
        source_dir="training",
        entry_script="train.py",
    ),
    compute=Compute(
        instance_type="ml.m5.xlarge",
        instance_count=1,
    ),
    output_data_config=OutputDataConfig(
        s3_output_path=f"s3://{bucket}/models/",
    ),
    hyperparameters={"max-iter": "500"},
)

trainer.train(
    input_data_config=[InputData(
        channel_name="train",
        data_source=f"s3://{bucket}/processed/train/",
    )],
    wait=False,
    logs=False,
)

job_name = trainer._latest_training_job.training_job_name
Path("workflow/latest_training_job.txt").write_text(job_name + "\n")
print(job_name)
