# Managed workflow scripts

These scripts support the book's managed AWS exercises:

1. `run_processing.py` — process the data
2. `run_training.py` — train the model
3. `run_evaluation.py` — produce evaluation evidence
4. `build_release_artifact.py` — construct the release artefact
5. `register_model.py` — register the model
6. `write_release_record.py` — record release evidence

The later stages read artefacts or references written by earlier stages.

Use the book's execution order and inspect each result before proceeding.

The scripts use AWS environment variables configured through `scripts/setup-env.sh`. Managed AWS operations may incur charges.
