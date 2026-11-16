#!/usr/bin/env python3
"""Render the book's account-specific IAM and capture JSON locally.

Usage from repository root:
  python scripts/render-iam.py pipeline
  python scripts/render-iam.py github
  python scripts/render-iam.py capture

No AWS calls are made; differing existing files will never be overwritten.
"""
import json
import os
import re
import sys
from pathlib import Path

FILES = {
    "pipeline": [
        "pipeline/pipeline-trust.json",
        "pipeline/pipeline-role-policy.json",
    ],
    "github": [
        "workflow/github-trust.json",
        "workflow/github-pipeline-policy.json",
    ],
    "capture": ["monitoring/data-capture.json"],
}
TOKEN = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")


def render(path: str) -> None:
    target = Path(path)
    template = Path(path + ".template").read_text(encoding="utf-8")
    required = set(TOKEN.findall(template))
    missing = sorted(name for name in required if not os.environ.get(name))
    if missing:
        raise ValueError("Missing environment variables: " + ", ".join(missing))

    result = TOKEN.sub(
        lambda match: json.dumps(os.environ[match.group(1)])[1:-1],
        template,
    )
    if not isinstance(json.loads(result), dict):
        raise ValueError("Expected JSON object: " + path)
    if target.exists():
        if target.read_text(encoding="utf-8") != result:
            raise FileExistsError("Existing file differs; will not overwrite: " + path)
        print("Unchanged:", path)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(result)
    print("Rendered locally:", path)


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in FILES:
        print("Usage: python scripts/render-iam.py pipeline|github|capture")
        return 2
    try:
        for file in FILES[sys.argv[1]]:
            render(file)
    except (ValueError, OSError) as error:
        print("STOP:", error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
