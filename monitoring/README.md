# Chapter 9 — Observing SageMaker and model health

**Book:** Chapter 9, Sections 9.5–9.6. This folder provides the book's [data-capture JSON template](data-capture.json.template) and its exact [input comparison script](compare_input.py).

## Create the data-capture request

First verify the currently active endpoint and its configuration, as the book instructs. Captured input and output can contain production data; protect it as carefully as other workload records. This lab requests a **100% sampling rate** to make a handful of requests observable; review cost and privacy before enabling it.

From the repository root after `source scripts/setup-env.sh`:

```bash
export CAPTURE_URI="s3://${S3_BUCKET}/monitoring/data-capture"
python scripts/render-iam.py capture
python -m json.tool monitoring/data-capture.json >/dev/null
```

This only creates a **local JSON file**. It does not update the endpoint or create AWS resources. Continue with Chapter 9's safe endpoint-configuration and data-capture verification sequence.

## Compare a baseline with captured inference input

Follow Chapter 9 to create or download `monitoring/baseline-train.csv` (training reference data) and download captured JSON Lines to `monitoring/capture/`. These files are local evidence, not checked-in source.

```bash
python monitoring/compare_input.py
```

The script reports average `monthly_charges` and the fraction of records with `month_to_month` contracts for baseline and captured inputs. A measurable difference **is not by itself a production drift decision**. Use representative windows, sample counts, thresholds and investigation as taught in the book.

**Failure boundary:** If no compatible captured inputs exist, stop and check the endpoint, capture destination, content type and object format. **Cleanup:** Retain required evidence before removing only project-owned S3 capture objects and restoring the approved endpoint configuration.
