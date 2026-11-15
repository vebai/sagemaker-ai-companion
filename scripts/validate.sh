#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=== SageMaker AI companion validation ==="

echo
echo "[1/5] Python syntax"
python - <<'PY'
import ast
from pathlib import Path

files = sorted(
    p for p in Path(".").rglob("*.py")
    if not any(
        x in p.parts
        for x in (".venv", ".terraform", "__pycache__")
    )
)

assert files, "No Python source files found"

for path in files:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("PASS:", path)

print("Python files checked:", len(files))
PY

echo
echo "[2/5] Dependency declarations"
python - <<'PY'
from pathlib import Path

requirements = Path("requirements.txt").read_text()

for package in ("boto3", "sagemaker", "scikit-learn"):
    assert any(
        line.strip().startswith(package + "==")
        for line in requirements.splitlines()
    ), f"Missing pinned dependency: {package}"

print("PASS: Required dependencies pinned")
PY

echo
echo "[3/5] IAM template rendering"
python - <<'PY'
from pathlib import Path
import json

root = Path("infrastructure/terraform")
account = "123456789012"
bucket = f"sagemaker-churn-{account}-eu-west-2"

for filename in ("pipeline-policy.json", "workload-policy.json"):
    path = root / "policies" / (filename + ".tftpl")
    raw = path.read_text()
    assert "${project_bucket}" in raw, (
        f"Missing project bucket variable: {filename}"
    )

    rendered = raw.replace("${account_id}", account)
    rendered = rendered.replace("${project_bucket}", bucket)

    policy = json.loads(rendered)
    assert policy.get("Statement"), f"No statements: {filename}"
    assert "${" not in rendered

    print("PASS:", filename)

for name in ("pipeline-trust.json", "workload-trust.json"):
    path = root / "snapshots" / name
    document = json.loads(path.read_text())
    assert document.get("Statement")
    print("PASS:", name)
PY

echo
echo "[4/5] Terraform validation"
terraform -chdir=infrastructure/terraform fmt -check -recursive
terraform -chdir=infrastructure/terraform validate
echo "PASS: Terraform"

echo
echo "[5/5] Account-specific reference check"
python - <<'PY'
from pathlib import Path

root = Path("infrastructure/terraform")

for path in root.rglob("*"):
    if not path.is_file():
        continue
    if ".terraform" in path.parts:
        continue
    if path.suffix not in (".tf", ".json", ".tftpl"):
        continue

    content = path.read_text(errors="replace")
    import re
    assert not re.search(r"(?<![0-9])[0-9]{12}(?![0-9])", content), (
        f"Hard-coded AWS account number found: {path}"
    )

print("PASS: No original account ID in Terraform source")
PY

echo
echo "=== VALIDATION PASSED ==="
echo "No AWS resources created or modified."
