import argparse
import gzip
import hashlib
import json
import shutil
import tarfile
from pathlib import Path


def safe_extract(archive, destination):
    root = destination.resolve()
    for member in archive.getmembers():
        if member.issym() or member.islnk():
            raise ValueError("Archive contains a link")
        target = (destination / member.name).resolve()
        if target != root and root not in target.parents:
            raise ValueError("Unsafe archive path")
    archive.extractall(destination)

def normalise(info):
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mtime = 0
    return info
parser = argparse.ArgumentParser()
parser.add_argument("--training-artifact-uri", required=True)
parser.add_argument("--evaluation-uri", required=True)
args = parser.parse_args()

model_path = Path("/opt/ml/processing/model/model.tar.gz")
evidence_path = Path(
    "/opt/ml/processing/evaluation/evaluation.json"
)
release_root = Path("/tmp/release")
release_root.mkdir(parents=True, exist_ok=True)

evidence = json.loads(
    evidence_path.read_text(encoding="utf-8")
)

if evidence["release_decision"] != "pass":
    raise RuntimeError("Candidate did not pass evaluation")

threshold = evidence[
    "threshold_selection"
]["selected_decision_threshold"]

with tarfile.open(model_path, "r:gz") as archive:
    safe_extract(archive, release_root)


policy = {
    "positive_class": 1,
    "decision_threshold": threshold,
    "selected_on": "validation",
    "validation_recall_target": evidence[
        "release_requirements"
    ]["validation_recall_target"],
    "training_artifact_uri": args.training_artifact_uri,
    "evaluation_uri": args.evaluation_uri,
}

(release_root / "decision_policy.json").write_text(
    json.dumps(policy, indent=2),
    encoding="utf-8",
)

code_dir = release_root / "code"
code_dir.mkdir(exist_ok=True)

shutil.copy2(
    Path(__file__).resolve().parent / "inference.py",
    code_dir / "inference.py",
)

output = Path("/opt/ml/processing/release/model.tar.gz")
output.parent.mkdir(parents=True, exist_ok=True)

with output.open("wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as archive:
            for child in sorted(release_root.iterdir()):
                archive.add(
                    child,
                    arcname=child.name,
                    filter=normalise,
                )

digest = hashlib.sha256(output.read_bytes()).hexdigest()

manifest = {
    "release_artifact_sha256": digest,
    "training_artifact_uri": args.training_artifact_uri,
    "evaluation_uri": args.evaluation_uri,
    "decision_threshold": str(threshold),
}

Path(
    "/opt/ml/processing/release/release_manifest.json"
).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

print(digest)
