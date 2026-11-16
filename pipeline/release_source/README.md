# Pipeline release-packaging source

**Path:** [Pipeline](../README.md) → **Release packaging** → Model Registry → [Inference](../../inference/README.md)  
**Book:** Chapter 7 · **Cost:** this source executes within billable managed Pipeline processing

## Purpose and prerequisite
The parent [Pipeline](../README.md) uses these two files after the model passes evaluation:

| File | Input | Output / responsibility |
|---|---|---|
| `package_release.py` | Training artefact and evaluation report; `--training-artifact-uri` and `--evaluation-uri` | Release model archive, decision policy and release manifest |
| `inference.py` | Packaged alongside the model | Serving implementation the registered candidate will use |

**Run:** Do not invoke these files as a standalone end-to-end deployment. Start with `python pipeline/build_pipeline.py` at the repository root, then follow Chapter 7 to execute the managed Pipeline. The Pipeline passes container-local inputs and arguments to the packaging step.

**Verify:** A passing evaluation must precede packaging; check the output release manifest, model artefact, digest and the Registry package created from them. Changing serving code or the release policy after evaluation changes what the evidence supports.

**Failure boundary:** missing model/evaluation input, unsafe archive, failed release-gate condition or missing S3 permissions. **Cleanup:** retain the release manifest and evidence before removing Pipeline artefacts and packages. **Next:** [Inference contract](../../inference/README.md).
