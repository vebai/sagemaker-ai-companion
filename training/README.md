# Model training

`train.py` trains the churn model.

Its explicit argument is `--max-iter`. In a managed training job, it reads the training channel from `SM_CHANNEL_TRAIN` and writes model output to `SM_MODEL_DIR`.

The book supplies the dataset locations, training configuration and verification steps. Review training job status, logs and model artefacts before continuing.
