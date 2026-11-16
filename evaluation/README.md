# 4. Evaluate the trained model

**Path:** [Train](../training/README.md) → **Evaluate** → [Release gate and Model Registry](../workflow/README.md) → [Inference](../inference/README.md)  
**Book:** Chapter 5 · **Cost:** managed evaluation uses billable SageMaker processing compute

## Purpose and prerequisite
`evaluate.py` loads a model artefact, uses **validation data** to choose a decision threshold, measures held-out **test** behaviour and writes `evaluation.json`. Do not start until the training job is `Completed`, `workflow/latest_model_artifact.txt` is populated, and the validation and test CSVs exist in S3.

**Release gate:** an explicit rule for allowing a model candidate to progress. The script records `release_decision` as `pass` or `fail`; a completed evaluation job does **not** mean the candidate passed.

## Run (AWS, billable)
From the repository root, after `source scripts/setup-env.sh` and checking your processing quota:
```bash
python workflow/run_evaluation.py
aws sagemaker describe-processing-job \
  --processing-job-name "$(cat workflow/latest_evaluation_job.txt)" \
  --query '{Status:ProcessingJobStatus,Failure:FailureReason}'
```
Wait for **`Completed`** before downloading the report:
```bash
aws s3 cp "$(cat workflow/latest_evaluation_uri.txt)" evaluation/evaluation.json
python -m json.tool evaluation/evaluation.json
```

| `evaluate.py` argument | Required? | Expected value |
|---|---|---|
| `--model` | No | Local model tarball path (managed container default) |
| `--validation`, `--test` | No | Local CSV paths (managed container defaults) |
| `--output` | No | Local JSON report path (managed container default) |
| `--model-artifact-uri` | Yes | Source model S3 URI recorded in evidence |
| `--validation-data-uri` | Yes | Validation-data S3 URI recorded in evidence |
| `--test-data-uri` | Yes | Test-data S3 URI recorded in evidence |

The path arguments describe files **inside the processing container**; URI arguments record provenance and do not replace those local inputs. The managed wrapper supplies all required values.

**Verify:** Read `release_decision`, `threshold_selection`, `test_metrics` and `release_requirements`. Only an evidenced **`pass`** may progress to release packaging. **Failure boundary:** missing model/CSV, incompatible model features, failed quota/IAM or metrics below the gate. **Cleanup:** retain evidence before removing S3 files. **Next:** [Package and register](../workflow/README.md).
