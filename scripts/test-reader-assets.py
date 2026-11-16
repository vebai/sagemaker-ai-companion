#!/usr/bin/env python3
"""Offline tests for the book's Chapter 7 IAM and Chapter 9 capture source."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
templates = [
    "pipeline/pipeline-trust.json.template",
    "pipeline/pipeline-role-policy.json.template",
    "workflow/github-trust.json.template",
    "workflow/github-pipeline-policy.json.template",
    "monitoring/data-capture.json.template",
]
for path in templates:
    document = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    print("PASS template:", path)

source = ROOT / "monitoring/compare_input.py"
ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
print("PASS: Chapter 9 comparison script parses")

with tempfile.TemporaryDirectory() as dirname:
    tmp = Path(dirname)
    for path in templates:
        output = tmp / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text((ROOT / path).read_text(encoding="utf-8"), encoding="utf-8")
    env = dict(os.environ)
    env.update({
        "SAGEMAKER_ROLE_ARN": "arn:aws:iam::123456789012:role/SageMakerChurnExecutionRole",
        "SAGEMAKER_PIPELINE_ROLE_ARN": "arn:aws:iam::123456789012:role/SageMakerChurnPipelineRole",
        "GITHUB_OIDC_PROVIDER_ARN": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com",
        "GITHUB_OIDC_SUB": "repo:example/project:ref:refs/heads/main",
        "S3_BUCKET": "sagemaker-churn-123456789012-eu-west-2",
        "CAPTURE_URI": "s3://sagemaker-churn-123456789012-eu-west-2/monitoring/data-capture",
    })
    command = [sys.executable, str(ROOT / "scripts/render-iam.py")]
    for mode in ("pipeline", "github", "capture"):
        run = subprocess.run(command + [mode], cwd=tmp, env=env,
                             capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
    for template in templates:
        path = tmp / template.removesuffix(".template")
        raw = path.read_text(encoding="utf-8")
        assert "${" not in raw
        assert isinstance(json.loads(raw), dict)
        assert path.stat().st_mode & 0o077 == 0
        print("PASS generated:", path.relative_to(tmp))
    again = subprocess.run(command + ["github"], cwd=tmp, env=env,
                           capture_output=True, text=True)
    assert again.returncode == 0, again.stderr
    env["GITHUB_OIDC_SUB"] = "repo:another/project:ref:refs/heads/main"
    changed = subprocess.run(command + ["github"], cwd=tmp, env=env,
                             capture_output=True, text=True)
    assert changed.returncode != 0, "Renderer must not overwrite existing files"
print("PASS: reader assets")
