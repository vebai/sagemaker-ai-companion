# Automate the SageMaker release path

**Path:** [Process](../processing/README.md) → [Train](../training/README.md) → [Evaluate](../evaluation/README.md) → **Pipeline** → Release decision → [Inference](../inference/README.md)  
**Book:** Chapter 7 · **Cost:** building the definition locally is not an AWS deployment; executing a Pipeline launches billable managed jobs

## Purpose and prerequisites
`build_pipeline.py` defines:

`ProcessData → TrainModel → EvaluateModel → CheckReleaseGate → (BuildReleaseArtefact → RegisterModel | FailReleaseGate)`

A failed evaluation takes the fail branch; a passing evaluation allows packaging and registration as a **pending** model package. **Registration is not approval or deployment.** Before publishing/running the Pipeline, verify your bucket, both SageMaker roles, caller permissions, processing/training quotas and raw CSV input. Use `source scripts/setup-env.sh` to supply `AWS_REGION`, `PROJECT_NAME`, `S3_BUCKET` and `SAGEMAKER_ROLE_ARN`.

## Local definition check (no managed jobs)
From the repository root:
```bash
python pipeline/build_pipeline.py
python -m json.tool pipeline/pipeline_definition.json >/dev/null
```

**Output:** `pipeline/pipeline_definition.json`, a local definition, **not** an AWS Pipeline. Follow Chapter 7 to create/update and execute the Pipeline with the intended execution role and parameters.

## What to verify after execution
- **Technical failure:** inspect the failed step, AWS error and CloudWatch logs before retrying.
- **Release gate fails:** inspect the evaluation JSON and `FailReleaseGate`; **do not register or approve** that candidate.
- **Release gate passes:** inspect processing output, trained artefact, evaluation report, release manifest and registered package. Its initial status is `PendingManualApproval`; a human approval remains necessary.

Pipeline outputs are execution-scoped under `s3://$S3_BUCKET/pipeline/<execution-id>/`. [`release_source/`](release_source/README.md) packages inference code and the evaluated decision policy together with a trained model, so the served implementation matches the release. The top-level [`inference/`](../inference/README.md) is used in the manual path.

**Failure boundary:** `sagemaker:AddTags`, S3 evaluation/release reads, `iam:PassRole`, quota and image permissions are distinct failure points. **Cleanup:** stop in-progress executions and remove project-owned Pipeline/Registry resources after saving evidence; remove the bucket separately. **Next:** Chapter 8 infrastructure ownership and Chapter 9 monitoring.
