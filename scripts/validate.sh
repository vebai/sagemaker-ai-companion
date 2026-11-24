#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=== SageMaker AI companion validation ==="

echo "[preflight] Script permissions and Bash syntax"
test -x scripts/validate.sh || {
  echo "scripts/validate.sh is not executable; run: chmod +x ./scripts/validate.sh" >&2
  exit 1
}
for script in scripts/*.sh workflow/*.sh; do
  bash -n "$script"
  echo "PASS: Bash syntax: $script"
done
echo "Note: scripts/setup-env.sh and workflow/empty_versioned_bucket.sh are sourced helpers."

echo "[safety] Verify versioned-S3 cleanup identity guards (AWS mocked)"
bash scripts/test-bucket-guard.sh

# Initialise providers without accessing or modifying backend state.
terraform -chdir=infrastructure/terraform init -backend=false -input=false >/dev/null
terraform -chdir=infrastructure/terraform-legacy init -backend=false -input=false >/dev/null

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

root = Path("infrastructure/terraform-legacy")
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
terraform -chdir=infrastructure/terraform-legacy fmt -check -recursive
terraform -chdir=infrastructure/terraform-legacy validate
echo "PASS: Terraform"

echo
echo "[5/5] Account-specific reference check"
python - <<'PY'
from pathlib import Path

root = Path("infrastructure/terraform-legacy")

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
echo
echo "[6/6] Canonical Chapter 8 Terraform and shared OIDC safety"
python - <<'PY'
from pathlib import Path
main = Path("infrastructure/terraform/main.tf").read_text()
outputs = Path("infrastructure/terraform/outputs.tf").read_text()
assert 'data "aws_iam_openid_connect_provider" "github"' in main
assert 'resource "aws_iam_openid_connect_provider"' not in main
assert 'data.aws_iam_openid_connect_provider.github.arn' in main
assert 'data.aws_iam_openid_connect_provider.github.arn' in outputs
print("PASS: shared GitHub OIDC provider referenced without lifecycle ownership")
PY

echo "[6/6] Chapter 8 Terraform configuration validation"
terraform -chdir=infrastructure/terraform validate
echo "PASS: Chapter 8 Terraform"

echo
echo "[reader assets] Chapter 7 IAM and Chapter 9 monitoring checks"
python scripts/test-reader-assets.py

echo "=== VALIDATION PASSED ==="
echo "No AWS resources created or modified."
