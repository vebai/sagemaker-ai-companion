#!/usr/bin/env python3
"""Read-only review of a Chapter 8 Terraform plan in JSON form.

Usage (from repository root):
  terraform -chdir=infrastructure/terraform show -json project.tfplan \
    > /tmp/sagemaker-ch08-plan.json
  python scripts/review-chapter8-plan.py /tmp/sagemaker-ch08-plan.json

This checker DOES NOT approve or apply a plan.
"""
import json
import sys
from pathlib import Path

EXPECTED = {
    "aws_s3_bucket.project",
    "aws_s3_bucket_public_access_block.project",
    "aws_s3_bucket_server_side_encryption_configuration.project",
    "aws_s3_bucket_versioning.project",
    "aws_iam_role.workload",
    "aws_iam_role_policy.workload",
    "aws_iam_role.pipeline",
    "aws_iam_role_policy.pipeline",
    "aws_iam_openid_connect_provider.github",
    "aws_iam_role.github",
    "aws_iam_role_policy.github",
}

PROTECTED_ROLE_NAMES = {
    "terraform-book-gh-oidc-test",
    "sagemaker-ai-gh-oidc-test",
}
PROTECTED_OIDC_ADDRESS = "aws_iam_openid_connect_provider.github"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/review-chapter8-plan.py PLAN.json")
        return 2
    path = Path(sys.argv[1])
    plan = json.loads(path.read_text(encoding="utf-8"))
    changes = plan.get("resource_changes", [])
    unsafe = []
    seen = set()

    print("=== Chapter 8 Terraform plan review (READ ONLY) ===")
    for change in changes:
        address = change["address"]
        actions = change["change"]["actions"]
        before = change["change"].get("before") or {}
        after = change["change"].get("after") or {}
        name = after.get("name") or before.get("name") or address
        seen.add(address)
        print(f"{address}: {actions} ({name})")

        if address not in EXPECTED:
            unsafe.append(f"unexpected managed resource: {address}")
        if actions not in (["no-op"], ["create"], ["update"], ["delete"], ["delete", "create"], ["create", "delete"]):
            unsafe.append(f"unexpected action on {address}: {actions}")
        if address == PROTECTED_OIDC_ADDRESS and actions != ["no-op"]:
            unsafe.append(
                "GitHub OIDC provider is changing; shared-provider ownership "
                "must be resolved before apply or destroy"
            )
        if name in PROTECTED_ROLE_NAMES and actions != ["no-op"]:
            unsafe.append(f"protected test IAM role would change: {name}")
        if "delete" in actions:
            unsafe.append(f"destructive operation: {address}")
        if address == "aws_iam_role.github":
            trust = (after.get("assume_role_policy") or "")
            if actions != ["delete"] and trust and "token.actions.githubusercontent.com:sub" not in trust:
                unsafe.append("GitHub delivery role trust lacks an exact OIDC sub condition")

    if unsafe:
        print("\nSTOP — REVIEW REQUIRED:")
        for issue in unsafe:
            print(" -", issue)
        print("No AWS resources modified.")
        return 1

    if not changes:
        print("No managed resource changes in this plan.")
    print("\nPASS: No prohibited action found in reviewed resource changes.")
    print("This is NOT authorisation to apply; verify account, workspace,")
    print("state ownership, imports, IAM access, quotas and costs separately.")
    print("No AWS resources modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
