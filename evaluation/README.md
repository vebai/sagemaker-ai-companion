# Model evaluation

`evaluate.py` produces model evaluation evidence.

Supported arguments include:

- `--model`
- `--validation`
- `--test`
- `--output`
- `--model-artifact-uri`
- `--validation-data-uri`
- `--test-data-uri`

The script is used after training. Interpret performance against the release gate defined in the book; training completion alone is not evidence of acceptable model quality.
