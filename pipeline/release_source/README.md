# Pipeline release source

This directory contains:

- `inference.py`: serving implementation included in the release
- `package_release.py`: release packaging

`package_release.py` accepts `--training-artifact-uri` and `--evaluation-uri`.

These sources are used by the parent Pipeline. Do not treat them as standalone end-to-end release commands.
