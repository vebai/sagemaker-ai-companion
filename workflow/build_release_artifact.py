import gzip
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import boto3

bucket = os.environ[
    "S3_BUCKET"
]
region = os.environ[
    "AWS_REGION"
]

training_artifact = Path(
    "workflow/latest_model_artifact.txt"
).read_text(
    encoding="utf-8"
).strip()

evaluation_uri = Path(
    "workflow/latest_evaluation_uri.txt"
).read_text(
    encoding="utf-8"
).strip()

evidence = json.loads(
    Path(
        "evaluation/evaluation.json"
    ).read_text(
        encoding="utf-8"
    )
)

if (
    evidence["release_decision"]
    != "pass"
):
    raise RuntimeError(
        "Only a passing candidate "
        "can become a release artefact"
    )

threshold = (
    evidence[
        "threshold_selection"
    ][
        "selected_decision_threshold"
    ]
)

if threshold is None:
    raise RuntimeError(
        "Passing evaluation has "
        "no decision threshold"
    )


def split_s3(uri):
    parsed = urlparse(uri)

    if parsed.scheme != "s3":
        raise ValueError(
            f"Expected S3 URI: {uri}"
        )

    return (
        parsed.netloc,
        parsed.path.lstrip("/"),
    )


def safe_extract(
    archive,
    destination,
):
    root = destination.resolve()

    for member in archive.getmembers():
        if (
            member.issym()
            or member.islnk()
        ):
            raise ValueError(
                "Archive contains a link"
            )

        target = (
            destination
            / member.name
        ).resolve()

        if (
            target != root
            and root not in target.parents
        ):
            raise ValueError(
                "Unsafe archive path"
            )

    archive.extractall(destination)


def normalise(info):
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    return info


s3 = boto3.client(
    "s3",
    region_name=region,
)

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    source_tar = (
        tmp
        / "training-model.tar.gz"
    )

    release_root = (
        tmp
        / "release"
    )

    release_root.mkdir()

    source_bucket, source_key = (
        split_s3(
            training_artifact
        )
    )

    s3.download_file(
        source_bucket,
        source_key,
        str(source_tar),
    )

    with tarfile.open(
        source_tar,
        "r:gz",
    ) as archive:
        safe_extract(
            archive,
            release_root,
        )

    policy = {
        "positive_class": 1,
        "decision_threshold":
            threshold,
        "selected_on":
            "validation",
        "validation_recall_target":
            evidence[
                "release_requirements"
            ][
                "validation_recall_target"
            ],
        "training_artifact_uri":
            training_artifact,
        "evaluation_uri":
            evaluation_uri,
    }

    (
        release_root
        / "decision_policy.json"
    ).write_text(
        json.dumps(
            policy,
            indent=2,
        ),
        encoding="utf-8",
    )

    code_dir = (
        release_root
        / "code"
    )

    code_dir.mkdir(
        exist_ok=True
    )

    shutil.copy2(
        "inference/inference.py",
        code_dir / "inference.py",
    )

    release_tar = (
        tmp
        / "model.tar.gz"
    )

    with release_tar.open("wb") as raw:
        with gzip.GzipFile(
            fileobj=raw,
            mode="wb",
            mtime=0,
        ) as zipped:
            with tarfile.open(
                fileobj=zipped,
                mode="w",
            ) as archive:
                for child in sorted(
                    release_root.iterdir(),
                    key=lambda p: p.name,
                ):
                    archive.add(
                        child,
                        arcname=child.name,
                        filter=normalise,
                    )

    digest = hashlib.sha256(
        release_tar.read_bytes()
    ).hexdigest()

    key = (
        "models/releases/"
        f"{digest}/model.tar.gz"
    )

    s3.upload_file(
        str(release_tar),
        bucket,
        key,
    )

release_uri = (
    f"s3://{bucket}/{key}"
)

Path(
    "workflow/"
    "latest_release_artifact.txt"
).write_text(
    release_uri + "\n"
)

Path(
    "workflow/"
    "latest_release_artifact_sha256.txt"
).write_text(
    digest + "\n"
)

print(release_uri)
