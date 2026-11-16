#!/usr/bin/env python3
"""Offline smoke tests for the read-only Chapter 8 plan guard."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

GUARD = Path(__file__).with_name("review-chapter8-plan.py")


def check(address, actions, expected_exit):
    payload = {
        "resource_changes": [{
            "address": address,
            "change": {
                "actions": actions,
                "before": {"name": "test"},
                "after": {"name": "test"},
            },
        }],
    }
    with tempfile.TemporaryDirectory() as td:
        file = Path(td) / "plan.json"
        file.write_text(json.dumps(payload), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(GUARD), str(file)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == expected_exit, (
            f"{address} {actions}: expected {expected_exit}, "
            f"got {result.returncode}\n{result.stdout}\n{result.stderr}"
        )


check("aws_s3_bucket.project", ["no-op"], 0)
check("aws_s3_bucket.project", ["create"], 0)
check("aws_s3_bucket.project", ["delete"], 1)
check("aws_iam_openid_connect_provider.github", ["create"], 1)
check("aws_iam_openid_connect_provider.github", ["update"], 1)
check("aws_iam_openid_connect_provider.github", ["delete"], 1)
check("aws_iam_openid_connect_provider.github", ["no-op"], 1)
check("aws_iam_role.unexpected", ["create"], 1)
print("PASS: Chapter 8 plan guard blocks destructive and OIDC changes")
