import json
import os
from pathlib import Path

import boto3
from sagemaker.core import image_uris
from sagemaker.core.model_metrics import MetricsSource, ModelMetrics
from sagemaker.core.processing import FrameworkProcessor, ScriptProcessor
from sagemaker.core.shapes import (
    ProcessingInput, ProcessingOutput,
    ProcessingS3Input, ProcessingS3Output,
)
from sagemaker.core.training.configs import (
    Compute, InputData, OutputDataConfig, SourceCode,
)
from sagemaker.core.workflow.conditions import ConditionEquals
from sagemaker.core.workflow.execution_variables import ExecutionVariables
from sagemaker.core.workflow.functions import Join, JsonGet
from sagemaker.core.workflow.parameters import ParameterString
from sagemaker.core.workflow.pipeline_context import PipelineSession
from sagemaker.core.workflow.properties import PropertyFile
from sagemaker.mlops.workflow.condition_step import ConditionStep
from sagemaker.mlops.workflow.fail_step import FailStep
from sagemaker.mlops.workflow.model_step import ModelStep
from sagemaker.mlops.workflow.pipeline import Pipeline
from sagemaker.mlops.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.serve.model_builder import ModelBuilder
from sagemaker.train import ModelTrainer
# Configure the shared context.
region = os.environ["AWS_REGION"]
bucket = os.environ["S3_BUCKET"]
project = os.environ["PROJECT_NAME"]
workload_role = os.environ["SAGEMAKER_ROLE_ARN"]

session = PipelineSession(
    boto_session=boto3.Session(region_name=region),
    default_bucket=bucket,
)

training_image = image_uris.retrieve(
    "sklearn", region=region, version="1.9-0",
    image_scope="training", instance_type="ml.m5.xlarge",
)

inference_image = image_uris.retrieve(
    "sklearn", region=region, version="1.9-0",
    image_scope="inference", instance_type="ml.m5.large",
)


input_data = ParameterString(
    name="InputDataUrl",
    default_value=f"s3://{bucket}/raw/customer_churn.csv",
)

source_revision = ParameterString(
    name="SourceRevision",
    default_value="local",
)

execution_root = Join(
    on="/",
    values=[
        f"s3://{bucket}/pipeline",
        ExecutionVariables.PIPELINE_EXECUTION_ID,
    ],
)

processed_root = Join(on="/", values=[execution_root, "processed"])
models_root = Join(on="/", values=[execution_root, "models"])
evaluation_root = Join(on="/", values=[execution_root, "evaluation"])
release_root = Join(on="/", values=[execution_root, "release"])


processor = ScriptProcessor(
    role=workload_role,
    image_uri=training_image,
    command=["python3"],
    instance_count=1,
    instance_type="ml.m5.xlarge",
    sagemaker_session=session,
)

process_args = processor.run(
    code="processing/process.py",
    inputs=[ProcessingInput(
        input_name="raw",
        s3_input=ProcessingS3Input(
            s3_uri=input_data,
            local_path="/opt/ml/processing/input",
            s3_data_type="S3Prefix",
            s3_input_mode="File",
        ),
    )],
# Continue
    outputs=[ProcessingOutput(
        output_name="processed",
        s3_output=ProcessingS3Output(
            s3_uri=processed_root,
            local_path="/opt/ml/processing/output",
            s3_upload_mode="EndOfJob",
        ),
    )],
)

step_process = ProcessingStep(
    name="ProcessData",
    step_args=process_args,
)

processed_output = (
    step_process.properties
    .ProcessingOutputConfig.Outputs["processed"]
    .S3Output.S3Uri
)
# Define the three downstream data locations:
train_uri = Join(
    on="/",
    values=[processed_output, "train"],
)

validation_uri = Join(
    on="/",
    values=[processed_output, "validation", "data.csv"],
)

test_uri = Join(
    on="/",
    values=[processed_output, "test", "data.csv"],
)


trainer = ModelTrainer(
    training_image=training_image,
    role=workload_role,
    sagemaker_session=session,
    base_job_name=f"{project}-pipeline-train",
    source_code=SourceCode(
        source_dir="training",
        entry_script="train.py",
    ),
    compute=Compute(
        instance_type="ml.m5.xlarge",
        instance_count=1,
    ),
    output_data_config=OutputDataConfig(
        s3_output_path=models_root,
    ),
    hyperparameters={"max-iter": "500"},
)
# Create the Training Step.
train_args = trainer.train(
    input_data_config=[
        InputData(
            channel_name="train",
            data_source=train_uri,
        )
    ]
)

step_train = TrainingStep(
    name="TrainModel",
    step_args=train_args,
)

model_artifact = (
    step_train.properties
    .ModelArtifacts.S3ModelArtifacts
)


evaluation_report = PropertyFile(
    name="EvaluationReport",
    output_name="evaluation",
    path="evaluation.json",
)

evaluation_processor = ScriptProcessor(
    role=workload_role,
    image_uri=training_image,
    command=["python3"],
    instance_count=1,
    instance_type="ml.m5.xlarge",
    sagemaker_session=session,
)

# Create its inputs.

evaluation_inputs = [
    ProcessingInput(
        input_name="model",
        s3_input=ProcessingS3Input(
            s3_uri=model_artifact,
            local_path="/opt/ml/processing/model",
            s3_data_type="S3Prefix",
            s3_input_mode="File",
        ),
    ),
    ProcessingInput(
        input_name="validation",
        s3_input=ProcessingS3Input(
            s3_uri=validation_uri,
            local_path="/opt/ml/processing/validation",
            s3_data_type="S3Prefix",
            s3_input_mode="File",
        ),
    ),
# Continue
    ProcessingInput(
        input_name="test",
        s3_input=ProcessingS3Input(
            s3_uri=test_uri,
            local_path="/opt/ml/processing/test",
            s3_data_type="S3Prefix",
            s3_input_mode="File",
        ),
    ),
]
# Create the Evaluation Step.
evaluation_args = evaluation_processor.run(
    code="evaluation/evaluate.py",
    inputs=evaluation_inputs,
    outputs=[ProcessingOutput(
        output_name="evaluation",
        s3_output=ProcessingS3Output(
            s3_uri=evaluation_root,
            local_path="/opt/ml/processing/output",
            s3_upload_mode="EndOfJob",
        ),
    )],
    arguments=[
        "--model-artifact-uri", model_artifact,
        "--validation-data-uri", validation_uri,
        "--test-data-uri", test_uri,
    ],
)

step_evaluate = ProcessingStep(
    name="EvaluateModel",
    step_args=evaluation_args,
    property_files=[evaluation_report],
)
# Expose the evidence used by later steps.
evaluation_output = (
    step_evaluate.properties
    .ProcessingOutputConfig.Outputs["evaluation"]
    .S3Output.S3Uri
)

evaluation_json_uri = Join(
    on="/",
    values=[evaluation_output, "evaluation.json"],
)

release_decision = JsonGet(
    step_name=step_evaluate.name,
    property_file=evaluation_report,
    json_path="release_decision",
)


release_manifest = PropertyFile(
    name="ReleaseManifest",
    output_name="release",
    path="release_manifest.json",
)

release_processor = FrameworkProcessor(
    role=workload_role,
    image_uri=training_image,
    command=["python3"],
    instance_count=1,
    instance_type="ml.m5.xlarge",
    sagemaker_session=session,
)
# Create the release-processing arguments.
release_args = release_processor.run(
    code="pipeline/release_source/package_release.py",
    source_dir="pipeline/release_source",
    inputs=[
        ProcessingInput(
            input_name="model",
            s3_input=ProcessingS3Input(
                s3_uri=model_artifact,
                local_path="/opt/ml/processing/model",
                s3_data_type="S3Prefix",
                s3_input_mode="File",
            ),
        ),
# Continue.
        ProcessingInput(
            input_name="evaluation",
            s3_input=ProcessingS3Input(
                s3_uri=evaluation_json_uri,
                local_path="/opt/ml/processing/evaluation",
                s3_data_type="S3Prefix",
                s3_input_mode="File",
            ),
        ),
    ],
    outputs=[ProcessingOutput(
        output_name="release",
        s3_output=ProcessingS3Output(
            s3_uri=release_root,
            local_path="/opt/ml/processing/release",
            s3_upload_mode="EndOfJob",
        ),
    )],
# Complete the call.
    arguments=[
        "--training-artifact-uri",
        model_artifact,
        "--evaluation-uri",
        evaluation_json_uri,
    ],
)

step_release = ProcessingStep(
    name="BuildReleaseArtefact",
    step_args=release_args,
    property_files=[release_manifest],
)
# Expose its artefact and identity.
release_output = (
    step_release.properties
    .ProcessingOutputConfig.Outputs["release"]
    .S3Output.S3Uri
)

release_model_uri = Join(
    on="/",
    values=[release_output, "model.tar.gz"],
)

release_digest = JsonGet(
    step_name=step_release.name,
    property_file=release_manifest,
    json_path="release_artifact_sha256",
)

release_threshold = JsonGet(
    step_name=step_release.name,
    property_file=release_manifest,
    json_path="decision_threshold",
)


# Define the evaluation evidence attached to the registered candidate.
model_metrics = ModelMetrics(
    model_statistics=MetricsSource(
        s3_uri=evaluation_json_uri,
        content_type="application/json",
    )
)

builder = ModelBuilder(
    role_arn=workload_role,
    sagemaker_session=session,
    image_uri=inference_image,
    s3_model_data_url=release_model_uri,
    env_vars={
        "SAGEMAKER_PROGRAM": "inference.py",
        "SAGEMAKER_SUBMIT_DIRECTORY":
            "/opt/ml/model/code",
    },
)
# Define registration.
register_args = builder.register(
    model_package_group_name=project,
    content_types=["text/csv"],
    response_types=["application/json"],
    inference_instances=["ml.m5.large"],
    model_metrics=model_metrics,
    approval_status="PendingManualApproval",
    customer_metadata_properties={
        "pipeline_execution_id":
            ExecutionVariables.PIPELINE_EXECUTION_ID,
        "source_revision": source_revision,
        "release_decision": "pass",
        "decision_threshold": release_threshold,
        "release_artifact_sha256": release_digest,
    },
)
# Create the Registry and failure steps.
step_register = ModelStep(
    name="RegisterModel",
    step_args=register_args,
    depends_on=[step_release],
)

step_fail = FailStep(
    name="FailReleaseGate",
    error_message=(
        "Candidate did not satisfy "
        "the release requirements"
    ),
)
# Create the release gate.
step_gate = ConditionStep(
    name="CheckReleaseGate",
    conditions=[
        ConditionEquals(
            left=release_decision,
            right="pass",
        )
    ],
    if_steps=[
        step_release,
        step_register,
    ],
    else_steps=[step_fail],
)
# This is the central decision.


pipeline = Pipeline(
    name=f"{project}-pipeline",
    parameters=[
        input_data,
        source_revision,
    ],
    steps=[
        step_process,
        step_train,
        step_evaluate,
        step_gate,
    ],
    sagemaker_session=session,
)

definition = json.loads(
    pipeline.definition()
)
# Verify the expected components exist.
required_steps = {
    "ProcessData",
    "TrainModel",
    "EvaluateModel",
    "CheckReleaseGate",
    "BuildReleaseArtefact",
    "RegisterModel",
    "FailReleaseGate",
}

definition_text = json.dumps(definition)

for name in required_steps:
    if name not in definition_text:
        raise RuntimeError(
            f"Pipeline definition missing {name}"
        )

# Write the definition.

Path(
    "pipeline/pipeline_definition.json"
).write_text(
    json.dumps(definition, indent=2),
    encoding="utf-8",
)

print(
    "Pipeline definition verified: "
    "pipeline/pipeline_definition.json"
)
