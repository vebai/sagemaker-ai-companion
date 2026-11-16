# 6. Serve the approved model

**Path:** [Evaluate](../evaluation/README.md) → [Register and approve](../workflow/README.md) → **Inference** → Monitor → Recover  
**Book:** Chapter 6 (deployment) and Chapter 9 (monitoring) · **Cost:** a deployed real-time endpoint is billable even when idle

## Purpose and prerequisites
`inference.py` is the serving implementation included in the approved model release. A **release contract** is the set of expectations frozen with the evaluated model: input features and representation, preprocessing, request content type, response format and selected decision threshold. First obtain a passing evaluation, packaged release, registered model package and **explicit approval**.

## Serving contract to verify
- **Input:** five customer features — `tenure_months`, `contract_type`, `monthly_charges`, `support_calls`, `payment_method`; no `churned` label in a prediction request
- **Content type:** `text/csv` for the documented endpoint
- **Preprocessing:** categorical representations must match those used by the trained model
- **Decision threshold:** use the evaluated threshold packaged with the release, not a new untested value
- **Output:** the documented prediction JSON must be compatible with the calling application

**Run:** The file is loaded by SageMaker's serving container; **do not execute `python inference/inference.py` as an endpoint deployment command**. Follow Chapter 6 to create a SageMaker Model, endpoint configuration and endpoint, wait for `InService`, then send the book's known request.

**Verify:** A successful deployment API response is not an inference result. Confirm endpoint health, valid response format and expected prediction behaviour. Changing serving code independently of the evaluated model invalidates release evidence.

**Failure boundary:** wrong feature order or categories, `ContentType` mismatch, wrong artefact/image, IAM/network or endpoint failure. **Cleanup:** delete the endpoint promptly after the exercise; it continues incurring charges while idle. **Next:** [Pipeline automation](../pipeline/README.md) and Chapter 9 monitoring.
