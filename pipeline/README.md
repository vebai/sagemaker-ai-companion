# SageMaker Pipeline

`build_pipeline.py` defines the managed workflow.

Required environment variables:

- `AWS_REGION`
- `PROJECT_NAME`
- `S3_BUCKET`
- `SAGEMAKER_ROLE_ARN`

`release_source/` contains the inference implementation and release-packaging code used by the Pipeline.

Follow the book's instructions to create or update the Pipeline and run it. Inspect each step and its evidence. A successful Pipeline run does not automatically prove model quality or serving readiness.
